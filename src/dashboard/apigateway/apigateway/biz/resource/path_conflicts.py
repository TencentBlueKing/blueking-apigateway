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
from itertools import zip_longest
from typing import Any, DefaultDict, Dict, Iterator, List, Optional, Tuple

from apigateway.core.constants import HTTP_METHOD_ANY, HTTP_METHOD_CHOICES

_PathIndex = DefaultDict[Tuple[str, str], List[Dict[str, Any]]]
_MAX_CONFLICT_GROUPS = 200
_PATH_PARAMETER = re.compile(r"\{\w+\}")


def find_resource_path_conflicts(
    resources: List[Dict[str, Any]], candidate: Optional[Dict[str, Any]] = None
) -> Tuple[List[Dict[str, Any]], bool]:
    """Find equivalent paths and segment overlaps between parameterized routes.

    ANY expands to concrete methods. Static routes take precedence over parameter
    routes, so only exact normalization conflicts are reported for static paths.
    Environment references, mixed parameter segments and subpath wildcards are
    outside the segment-overlap analysis.
    """
    normalized: _PathIndex = defaultdict(list)
    for resource in resources:
        item = _normalize_resource(resource)
        for method in _resource_methods(resource):
            normalized[method, item["normalized_path"]].append(item)

    trees = _build_parameter_trees(normalized)
    if candidate is None:
        groups = _find_all_groups(normalized, trees)
    else:
        groups = _find_candidate_groups(normalized, trees, _normalize_resource(candidate))
    # Preserve group limits and complete resource lists within each returned group.
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


@dataclass
class _PathNode:
    children: Dict[str, "_PathNode"] = field(default_factory=dict)
    path: Optional[str] = None


def _parameter_segments(path: str) -> List[str]:
    segments = path.split("/")
    if "{}" not in segments or any("{" in part or "}" in part for part in segments if part != "{}"):
        return []
    return segments


def _build_parameter_trees(normalized: _PathIndex) -> Dict[Tuple[str, int], _PathNode]:
    # Index unique patterns, not resources: thousands of equivalent paths share a leaf.
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
    # Fixed segments visit only the identical literal and parameter branches.
    # Parameters can match any nonempty segment. Iteration avoids recursion depth limits.
    pending = [(root, 0)]
    while pending:
        node, index = pending.pop()
        if index == len(segments):
            if node.path is not None and node.path != path:
                yield node.path
            continue
        segment = segments[index]
        if segment == "{}":
            children = [child for key, child in node.children.items() if key]
        else:
            keys = (segment, "{}") if segment else (segment,)
            children = [node.children[key] for key in keys if key in node.children]
        pending.extend((child, index + 1) for child in children)


def _find_all_groups(normalized: _PathIndex, trees: Dict[Tuple[str, int], _PathNode]) -> List[Dict[str, Any]]:
    groups = [
        {"type": "normalized_path", "method": method, "resources": items}
        for (method, _), items in normalized.items()
        if len(items) > 1
    ]
    overlap_groups = []
    visited = set()
    # General patterns first retain a compact group for one parameter versus many literals.
    for method, path in sorted(normalized, key=lambda key: -key[1].count("{}")):
        segments = _parameter_segments(path)
        if not segments:
            continue
        visited.add((method, path))
        overlaps = [
            other
            for other in _overlapping_paths(trees[method, len(segments)], segments, path)
            if (method, other) not in visited
        ]
        if overlaps:
            items = normalized[method, path] + [item for other in overlaps for item in normalized[method, other]]
            # Each other pattern overlaps the anchor; other patterns need not overlap each other.
            overlap_groups.append({"type": "literal_parameter", "method": method, "resources": items})
    return [group for pair in zip_longest(groups, overlap_groups) for group in pair if group is not None]


def _find_candidate_groups(
    normalized: _PathIndex, trees: Dict[Tuple[str, int], _PathNode], candidate: Dict[str, Any]
) -> List[Dict[str, Any]]:
    groups = []
    path = candidate["normalized_path"]
    segments = _parameter_segments(path)
    for method in _resource_methods(candidate):
        same_path = normalized.get((method, path), [])
        if same_path:
            groups.append({"type": "normalized_path", "method": method, "resources": same_path + [candidate]})
        root = trees.get((method, len(segments)))
        if root is None:
            continue
        overlaps = [item for other in _overlapping_paths(root, segments, path) for item in normalized[method, other]]
        if overlaps:
            groups.append({"type": "literal_parameter", "method": method, "resources": overlaps + [candidate]})
    return groups
