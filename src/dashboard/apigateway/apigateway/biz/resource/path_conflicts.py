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
from itertools import zip_longest
from typing import Any, DefaultDict, Dict, List, Optional, Tuple

from apigateway.core.constants import HTTP_METHOD_ANY, HTTP_METHOD_CHOICES

_PathIndex = DefaultDict[Tuple[str, str], List[Dict[str, Any]]]
_MAX_CONFLICT_GROUPS = 200
_PATH_PARAMETER = re.compile(r"\{\w+\}")


def find_resource_path_conflicts(
    resources: List[Dict[str, Any]], candidate: Optional[Dict[str, Any]] = None
) -> Tuple[List[Dict[str, Any]], bool]:
    """Group the two supported overlap types by concrete HTTP method in O(n).

    ANY expands to the supported methods. Trailing slashes follow RouteConvertor;
    environment references and subpath wildcards are not expanded.
    """
    # 完整路径索引用于查找同路径资源；父路径索引只收集末段为字面量的资源。
    # 末段参数资源可以直接通过 normalized[(method, prefix + "/{}")] 查到。
    normalized: _PathIndex = defaultdict(list)
    literals: _PathIndex = defaultdict(list)
    for resource in resources:
        item = _normalize_resource(resource)
        path = item["normalized_path"]
        prefix, _, last = path.rpartition("/")
        for method in _resource_methods(resource):
            normalized[method, path].append(item)
            if last and "{" not in last and "}" not in last:
                literals[method, prefix].append(item)

    if candidate is None:
        groups = _find_all_groups(normalized, literals)
    else:
        groups = _find_candidate_groups(normalized, literals, _normalize_resource(candidate))
    # 限制的是组数，保留组内全部资源；不展开两两配对，输出规模仍与资源数成正比。
    return groups[:_MAX_CONFLICT_GROUPS], len(groups) > _MAX_CONFLICT_GROUPS


def _normalize_resource(resource: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "id": resource.get("id"),
        "name": resource.get("name", ""),
        "method": resource["method"],
        "path": resource["path"],
        "normalized_path": _PATH_PARAMETER.sub("{}", resource["path"].rstrip("/")) or "/",
    }


def _resource_methods(resource: Dict[str, Any]) -> List[str]:
    # 方法数量固定，ANY 展开不改变 O(n) 复杂度；资源本身仍保留原始 method。
    if resource["method"] == HTTP_METHOD_ANY:
        return [method for method, _ in HTTP_METHOD_CHOICES]
    return [resource["method"]]


def _find_all_groups(normalized: _PathIndex, literals: _PathIndex) -> List[Dict[str, Any]]:
    # 第一类：相同具体方法、相同归一化路径下有多个资源，就构成一个冲突组。
    groups = [
        {"type": "normalized_path", "method": method, "resources": items}
        for (method, _), items in normalized.items()
        if len(items) > 1
    ]
    # 第二类：同父路径下同时有字面量末段和参数末段，报告两类资源之间的重叠。
    # 不同字面量之间未必重叠，因此这里不是组内资源的两两冲突声明。
    literal_groups = []
    for (method, prefix), items in literals.items():
        parameters = normalized.get((method, prefix + "/{}"), [])
        if parameters:
            literal_groups.append({"type": "literal_parameter", "method": method, "resources": items + parameters})
    # 两类组交替返回，避免归一化路径组占满上限后隐藏所有末段重叠组。
    return [group for pair in zip_longest(groups, literal_groups) for group in pair if group is not None]


def _find_candidate_groups(
    normalized: _PathIndex, literals: _PathIndex, candidate: Dict[str, Any]
) -> List[Dict[str, Any]]:
    # 候选资源不加入索引：直接查询它对应的 key，避免遍历或返回与它无关的冲突。
    # 编辑场景由调用方先排除当前资源，避免把旧路径作为另一个资源参与检测。
    groups = []
    path = candidate["normalized_path"]
    prefix, _, last = path.rpartition("/")
    for method in _resource_methods(candidate):
        same_path = normalized.get((method, path), [])
        if same_path:
            groups.append({"type": "normalized_path", "method": method, "resources": same_path + [candidate]})

        # 只查询另一类末段；例如候选 /x/batch 不能把已有 /x/other 带入结果。
        if last == "{}":
            overlaps = literals.get((method, prefix), [])
        elif last and "{" not in last and "}" not in last:
            overlaps = normalized.get((method, prefix + "/{}"), [])
        else:
            overlaps = []
        if overlaps:
            groups.append({"type": "literal_parameter", "method": method, "resources": overlaps + [candidate]})
    return groups
