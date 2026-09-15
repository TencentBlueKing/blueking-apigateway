#
# TencentBlueKing is pleased to support the open source community by making
# 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
# Copyright (C) Tencent. All rights reserved.
# Licensed under the MIT License (the "License"); you may not use this file except
# in compliance with the License. You may obtain a copy of the License at
#
#     http://opensource.org/licenses/MIT
#
# Unless required by applicable law or agreed to in writing, software distributed under
# the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND,
# either express or implied. See the License for the specific language governing permissions and
# limitations under the License.
#
# We undertake not to change the open source license (MIT license) applicable
# to the current version of the project delivered to anyone in the future.
#
import re
from collections import defaultdict
from dataclasses import dataclass, field
from itertools import chain, islice
from typing import Any, DefaultDict, Dict, Iterable, Iterator, List, Optional, Tuple

from apigateway.core.constants import HTTP_METHOD_ANY, HTTP_METHOD_CHOICES

# 同一方法、同一归一化路径的资源放在一起，例如 ("GET", "/users/{}") -> [资源1, 资源2]。
_PathIndex = DefaultDict[Tuple[str, str], List[Dict[str, Any]]]
_MAX_CONFLICT_GROUPS = 200
_MAX_GROUP_RESOURCES = 50
_PATH_PARAMETER = re.compile(r"\{\w+\}")


def find_resource_path_conflicts(
    resources: List[Dict[str, Any]], candidate: Optional[Dict[str, Any]] = None
) -> Tuple[List[Dict[str, Any]], bool]:
    """检测资源路径，返回 (冲突组列表, 是否还有未返回的组)。

    candidate=None 时检测全部资源；传入 candidate 时只检测它与 resources 的冲突。
    编辑场景由调用方先从 resources 中排除当前资源。

    例：GET /users/{id} 与 GET /users/{name} 返回一个 normalized_path 组。
    GET /biz/{id}/batch 与 GET /biz/{id}/{name} 返回一个 literal_parameter 组。
    完整静态路径与参数路径的重叠不提示，例如 /users/new 与 /users/{id}。

    处理顺序：按方法和归一化路径分组 -> 建路径段索引 -> 按需生成冲突组。
    最多返回 200 组，每组最多 50 条资源；组数与组内资源各有独立的截断标记。
    下游函数使用 yield 按需生成结果，不能改成先算全量列表再截断。
    环境变量、混合参数段、子路径通配符及字面量中的正则匹配语义不在检测范围内。
    """
    normalized: _PathIndex = defaultdict(list)
    for resource in resources:
        item = _normalize_resource(resource)
        for method in _resource_methods(resource):
            normalized[method, item["normalized_path"]].append(item)

    trees = _build_parameter_trees(normalized)
    if candidate is None:
        group_iterator = _find_all_groups(normalized, trees)
    else:
        group_iterator = _find_candidate_groups(normalized, trees, _normalize_resource(candidate))
    # 多取第 201 组，只用于判断是否截断；恰好 200 组时不能标记为截断。
    groups = list(islice(group_iterator, _MAX_CONFLICT_GROUPS + 1))
    return groups[:_MAX_CONFLICT_GROUPS], len(groups) > _MAX_CONFLICT_GROUPS


def _normalize_resource(resource: Dict[str, Any]) -> Dict[str, Any]:
    """保留展示字段，参数名统一替换为 {}，忽略尾斜杠。

    例：/biz/{biz_id}/apps/{app_id}/ -> /biz/{}/apps/{}；根路径仍为 /。
    """
    return {
        "id": resource.get("id"),
        "name": resource.get("name", ""),
        "method": resource["method"],
        "path": resource["path"],
        "normalized_path": _PATH_PARAMETER.sub("{}", resource["path"].rstrip("/")) or "/",
    }


def _resource_methods(resource: Dict[str, Any]) -> List[str]:
    """返回参与比较的具体方法：GET -> [GET]，ANY -> 配置支持的七种方法。

    只展开比较方法，不修改资源中用于展示的原始 method。
    """
    if resource["method"] == HTTP_METHOD_ANY:
        return [method for method, _ in HTTP_METHOD_CHOICES]
    return [resource["method"]]


@dataclass
class _PathNode:
    """路径段树的节点；children 用路径段作键，叶节点的 path 保存完整归一化路径。

    例：/a/{} 对应根节点 -> 空字符串 -> a -> {}，最后一个节点保存 /a/{}。
    """

    children: Dict[str, "_PathNode"] = field(default_factory=dict)
    path: Optional[str] = None


def _parameter_segments(path: str) -> List[str]:
    """拆分可参与逐段重叠检测的参数路径，不支持的路径返回空列表。

    例：/a/{} -> ["", "a", "{}"]；/a/new、/a/{id}.json、/{env.region}/{} -> []。
    保留开头及中间的空段，因为参数不能匹配空字符串。
    """
    segments = path.split("/")
    if "{}" not in segments:
        return []
    for segment in segments:
        if segment == "{}":
            continue
        if "{" in segment or "}" in segment:
            return []
    return segments


def _build_parameter_trees(normalized: _PathIndex) -> Dict[Tuple[str, int], _PathNode]:
    """按 (具体方法, 路径段数) 建树，避免比较方法或段数不同的路径。

    例：GET /a/{} 与 GET /b/{} 在同一棵树，POST /a/{} 在另一棵树。
    同一归一化路径只建一个叶节点，2000 条等价资源也只占一个叶节点。
    """
    trees: Dict[Tuple[str, int], _PathNode] = {}
    for method, path in normalized:
        segments = _parameter_segments(path)
        if not segments:
            continue
        node = trees.setdefault((method, len(segments)), _PathNode())
        for segment in segments:
            node = node.children.setdefault(segment, _PathNode())
        node.path = path
    return trees


def _overlapping_paths(root: _PathNode, segments: List[str], path: str) -> Iterator[str]:
    """按树的遍历顺序生成与 path 重叠的其他路径，不返回 path 本身。

    字面量只尝试同名分支和参数分支；{} 尝试所有非空分支。
    例：/a/{}/fixed 能找到 /a/{}/{}，但找不到 /a/{}/other。
    使用栈而非递归，避免长路径触发递归深度限制；栈后进先出，影响结果展示顺序。
    """
    pending = [(root, 0)]
    while pending:
        node, index = pending.pop()
        if index == len(segments):
            if node.path is not None and node.path != path:
                yield node.path
            continue

        segment = segments[index]
        if segment == "{}":
            for child_segment, child in node.children.items():
                if child_segment:  # 参数至少匹配一个字符，不能匹配空段。
                    pending.append((child, index + 1))
        else:
            literal_child = node.children.get(segment)
            if literal_child is not None:
                pending.append((literal_child, index + 1))
            parameter_child = node.children.get("{}")
            if segment and parameter_child is not None:
                pending.append((parameter_child, index + 1))


def _make_group(kind: str, method: str, resources: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
    """按输入顺序取最多 50 条资源，多取第 51 条用于判断组内是否截断。

    例：输入恰好 50 条时 resources_truncated=False，51 条时为 True。
    resources 可以是生成器；这里不会为了精确总数而遍历剩余资源。
    """
    items = list(islice(resources, _MAX_GROUP_RESOURCES + 1))
    return {
        "type": kind,
        "method": method,
        "resources": items[:_MAX_GROUP_RESOURCES],
        "resources_truncated": len(items) > _MAX_GROUP_RESOURCES,
    }


def _overlap_group(
    method: str, anchors: List[Dict[str, Any]], overlaps: Iterator[Dict[str, Any]]
) -> Optional[Dict[str, Any]]:
    """用基准资源与重叠资源组装一组；没有其他重叠路径则返回 None。

    anchors 中的资源归一化路径相同；单资源检测时只有 candidate 一条。
    例：基准为 [a1, a2]、重叠资源为 [b, c]，组内顺序为 [a1, b, a2, c]。
    先放一对实际重叠路径，避免 50 个名额全被等价基准资源占满。
    """
    first = next(overlaps, None)
    if first is None:
        return None
    conflicting_pair = [anchors[0], first]
    remaining_anchors = islice(anchors, 1, None)
    resources = chain(conflicting_pair, remaining_anchors, overlaps)
    return _make_group("literal_parameter", method, resources)


def _find_all_groups(normalized: _PathIndex, trees: Dict[Tuple[str, int], _PathNode]) -> Iterator[Dict[str, Any]]:
    """交替生成等价路径组与逐段重叠组，一类耗尽后继续另一类。

    例：等价组 N1、N2、N3，重叠组 L1，输出 N1、L1、N2、N3。
    这样 200 组上限不会优先被某一种冲突占满。
    """
    equivalent_groups = _find_equivalent_groups(normalized)
    overlap_groups = _find_overlap_groups(normalized, trees)
    while True:
        equivalent = next(equivalent_groups, None)
        if equivalent is not None:
            yield equivalent
        overlap = next(overlap_groups, None)
        if overlap is not None:
            yield overlap
        if equivalent is None and overlap is None:
            return


def _find_equivalent_groups(normalized: _PathIndex) -> Iterator[Dict[str, Any]]:
    """同一方法、同一归一化路径存在两条以上资源时，生成一个等价路径组。"""
    for (method, _), resources in normalized.items():
        if len(resources) > 1:
            yield _make_group("normalized_path", method, resources)


def _resources_for_paths(normalized: _PathIndex, method: str, paths: Iterable[str]) -> Iterator[Dict[str, Any]]:
    """把归一化路径依次展开为资源；例如 [路径A, 路径B] -> [a1, a2, b1]。"""
    for path in paths:
        yield from normalized[method, path]


def _find_overlap_groups(normalized: _PathIndex, trees: Dict[Tuple[str, int], _PathNode]) -> Iterator[Dict[str, Any]]:
    """依次选路径作基准，生成与该基准重叠的资源组。

    参数较多的路径先作基准，尽量把多个字面量路径归入同一组。
    visited 只记录已作过基准的路径，不能把整组路径都标记为已处理。
    例：a 与 b、c 重叠，b 与 c 也重叠，可能返回 [a, b, c]、[b, c] 两组；
    第一组不承诺 b 与 c 的关系，第二组仍需保留。
    """
    visited = set()
    for method, path in sorted(normalized, key=lambda key: -key[1].count("{}")):
        segments = _parameter_segments(path)
        if not segments:
            continue
        visited.add((method, path))
        root = trees[method, len(segments)]
        overlapping_paths = _overlapping_paths(root, segments, path)
        unvisited_paths = (other for other in overlapping_paths if (method, other) not in visited)
        overlaps = _resources_for_paths(normalized, method, unvisited_paths)
        group = _overlap_group(method, normalized[method, path], overlaps)
        if group is not None:
            yield group


def _find_candidate_groups(
    normalized: _PathIndex, trees: Dict[Tuple[str, int], _PathNode], candidate: Dict[str, Any]
) -> Iterator[Dict[str, Any]]:
    """只生成与候选资源有关的组，候选资源始终放在组内第一条。

    同一具体方法最多有一个等价组和一个逐段重叠组；ANY 分别检测七种方法。
    其他已有资源之间即使冲突，也不会单独生成组。
    """
    path = candidate["normalized_path"]
    segments = _parameter_segments(path)
    for method in _resource_methods(candidate):
        same_path = normalized.get((method, path), [])
        if same_path:
            yield _make_group("normalized_path", method, chain([candidate], same_path))
        root = trees.get((method, len(segments)))
        if root is None:
            continue
        overlapping_paths = _overlapping_paths(root, segments, path)
        overlaps = _resources_for_paths(normalized, method, overlapping_paths)
        group = _overlap_group(method, [candidate], overlaps)
        if group is not None:
            yield group
