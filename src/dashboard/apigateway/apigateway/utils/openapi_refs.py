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
from typing import Any, List, Set

UNSAFE_OPENAPI_REF_MESSAGE = "OpenAPI document contains external $ref which is not allowed"


def validate_openapi_refs(data: Any) -> None:
    """Reject $ref values that are not in-document fragments (must start with '#')."""
    if has_unsafe_openapi_refs(data):
        raise ValueError(UNSAFE_OPENAPI_REF_MESSAGE)


def has_unsafe_openapi_refs(node: Any) -> bool:
    """Walk mappings/sequences once and report the first external $ref."""
    stack: List[Any] = [node]
    seen: Set[int] = set()

    while stack:
        current_node = stack.pop()
        if isinstance(current_node, dict):
            node_id = id(current_node)
            if node_id in seen:
                continue
            seen.add(node_id)
            for key, value in current_node.items():
                if key == "$ref":
                    if isinstance(value, str) and not value.startswith("#"):
                        return True
                else:
                    stack.append(value)
        elif isinstance(current_node, list):
            node_id = id(current_node)
            if node_id in seen:
                continue
            seen.add(node_id)
            stack.extend(current_node)

    return False
