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
from itertools import combinations, islice, product
from typing import Any, DefaultDict, Dict, Iterable, List, Optional, Tuple

from apigateway.core.constants import HTTP_METHOD_ANY

_ResourceEntry = Tuple[int, Dict[str, Any]]
_MAX_CONFLICT_PAIRS = 200
_PATH_PARAMETER = re.compile(r"\{\w+\}")


def find_resource_path_conflicts(
    resources: List[Dict[str, Any]], candidate: Optional[Dict[str, Any]] = None
) -> Tuple[List[Dict[str, Any]], bool]:
    """Find the two supported overlap types; this does not predict APISIX's winning route.

    Return at most 200 pairs and whether additional conflicts were found.
    Trailing slashes follow RouteConvertor._convert_uris. Environment references
    are deliberately not parameters. Subpath wildcard overlaps are outside scope.
    """
    conflicts = list(islice(_iter_resource_path_conflicts(resources, candidate), _MAX_CONFLICT_PAIRS + 1))
    return conflicts[:_MAX_CONFLICT_PAIRS], len(conflicts) > _MAX_CONFLICT_PAIRS


def _iter_resource_path_conflicts(
    resources: List[Dict[str, Any]], candidate: Optional[Dict[str, Any]]
) -> Iterable[Dict[str, Any]]:
    normalized: DefaultDict[str, List[_ResourceEntry]] = defaultdict(list)
    prefixes: DefaultDict[str, Dict[str, List[_ResourceEntry]]] = defaultdict(
        lambda: {"parameters": [], "literals": []}
    )
    for index, resource in enumerate(resources + ([candidate] if candidate is not None else [])):
        path = _PATH_PARAMETER.sub("{}", resource["path"].rstrip("/")) or "/"
        item = {
            "id": resource.get("id"),
            "name": resource.get("name", ""),
            "method": resource["method"],
            "path": resource["path"],
            "normalized_path": path,
        }
        entry = (index, item)
        normalized[path].append(entry)
        prefix, _, last = path.rpartition("/")
        if last == "{}":
            prefixes[prefix]["parameters"].append(entry)
        elif last and "{" not in last and "}" not in last:
            prefixes[prefix]["literals"].append(entry)

    pairs: Iterable[Tuple[_ResourceEntry, _ResourceEntry]]
    for entries in normalized.values():
        if candidate is None:
            pairs = combinations(entries, 2)
        else:
            # Only compare the candidate; do not enumerate existing conflicts.
            pairs = product(
                [entry for entry in entries if entry[0] != len(resources)],
                [entry for entry in entries if entry[0] == len(resources)],
            )
        for left, right in pairs:
            conflict = _make_conflict(left, right, "normalized_path")
            if conflict is not None:
                yield conflict
    for group in prefixes.values():
        for left, right in _literal_parameter_pairs(group, len(resources) if candidate is not None else None):
            conflict = _make_conflict(left, right, "literal_parameter")
            if conflict is not None:
                yield conflict


def _make_conflict(left: _ResourceEntry, right: _ResourceEntry, conflict_type: str) -> Optional[Dict[str, Any]]:
    _, left_item = left
    _, right_item = right
    methods = {left_item["method"], right_item["method"]}
    if len(methods) > 1 and HTTP_METHOD_ANY not in methods:
        return None
    return {"type": conflict_type, "resources": [left_item, right_item]}


def _literal_parameter_pairs(
    group: Dict[str, List[_ResourceEntry]], candidate_index: Optional[int]
) -> Iterable[Tuple[_ResourceEntry, _ResourceEntry]]:
    literals, parameters = group["literals"], group["parameters"]
    if candidate_index is not None:
        if any(entry[0] == candidate_index for entry in literals):
            literals = [entry for entry in literals if entry[0] == candidate_index]
        else:
            parameters = [entry for entry in parameters if entry[0] == candidate_index]
    return product(literals, parameters)
