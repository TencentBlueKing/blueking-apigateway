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
"""内存中的资源，测试用。fixture 先还原成发布数据和 OpenAPI schema，再走 build_skill_resource。"""

import copy
import json
from typing import Any, Dict, Iterable

from apigateway.biz.released_resource import ReleasedResourceData
from apigateway.biz.skill.resource_loader import (
    ResourceProvider,
    SkillResource,
    SkillResourceUnavailableError,
    build_skill_resource,
)
from apigateway.core.constants import ResourceKindEnum


class StaticResourceProvider(ResourceProvider):
    def __init__(self, resources: Iterable[SkillResource]):
        self._resources = {resource.key: resource for resource in resources}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "StaticResourceProvider":
        """`{"resources": [...]}`，每项含 gateway、stage、resource、method、path、description、auth、params、response"""
        resources = []
        for index, item in enumerate(data["resources"], start=1):
            try:
                resource = build_skill_resource(
                    item["gateway"],
                    item["stage"],
                    ReleasedResourceData.from_data(released_resource_payload(item, index)),
                    fixture_resource_schema(item),
                )
            except SkillResourceUnavailableError:
                continue
            resources.append(resource)
        return cls(resources)

    def get_resource(self, gateway: str, stage: str, resource: str) -> SkillResource:
        found = self._resources.get((gateway, stage, resource))
        if found is None:
            raise SkillResourceUnavailableError(f"fixture 中没有资源 {resource}")
        return found


def released_resource_payload(item: Dict[str, Any], resource_id: int) -> Dict[str, Any]:
    """fixture 的一项资源 -> ReleasedResource.data。认证五项原样放进 resource_auth，OAuth2 默认关闭。"""
    auth = item.get("auth") or {}
    auth_config = {
        "app_verified_required": auth.get("app_verified_required", True),
        "auth_verified_required": auth.get("user_verified_required", False),
        "resource_perm_required": auth.get("resource_perm_required", True),
        "oauth2_public_client_enabled": auth.get("oauth2_public_client_enabled", False),
        "oauth2_personal_client_enabled": auth.get("oauth2_personal_client_enabled", False),
    }
    return {
        "id": resource_id,
        "name": item["resource"],
        "method": item["method"],
        "path": item["path"],
        "description": item.get("description", ""),
        "is_public": item.get("is_public", True),
        "kind": item.get("kind") or ResourceKindEnum.STANDARD.value,
        "disabled_stages": item.get("disabled_stages", []),
        "contexts": {"resource_auth": {"config": json.dumps(auth_config)}},
        "api_labels": [],
    }


def fixture_resource_schema(resource: Dict[str, Any]) -> Dict[str, Any]:
    """fixture 的 params / response -> 该资源的 OpenAPI schema。参数写了 schema 时原样使用，否则由 type 生成。"""
    parameters = []
    body_properties = {}
    body_required = []
    for item in resource.get("params", []):
        param_schema = (
            copy.deepcopy(item["schema"]) if "schema" in item else _fixture_type_schema(item.get("type") or "")
        )
        if item.get("description"):
            param_schema["description"] = item["description"]
        if item["in"] == "body":
            body_properties[item["name"]] = param_schema
            if item.get("required"):
                body_required.append(item["name"])
            continue
        parameters.append(
            {
                "name": item["name"],
                "in": item["in"],
                "required": bool(item.get("required")),
                "description": item.get("description") or "",
                "schema": param_schema,
            }
        )

    schema: Dict[str, Any] = {"parameters": parameters}
    if body_properties:
        schema["requestBody"] = {
            "required": bool(body_required),
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": body_properties,
                        "required": body_required,
                    }
                }
            },
        }

    response_schema: Dict[str, Any] = {"type": "object", "properties": {}}
    for item in resource.get("response", []):
        _add_fixture_response_field(response_schema, item)
    if response_schema["properties"]:
        schema["responses"] = {
            "200": {
                "description": "ok",
                "content": {"application/json": {"schema": response_schema}},
            }
        }
    return schema


def _fixture_type_schema(type_text: str) -> Dict[str, Any]:
    if type_text.startswith("array<") and type_text.endswith(">"):
        return {"type": "array", "items": _fixture_type_schema(type_text[6:-1])}
    if "|" in type_text:
        return {"type": type_text.split("|")}
    return {"type": type_text} if type_text else {}


def _add_fixture_response_field(root: Dict[str, Any], field: Dict[str, Any]) -> None:
    current = root
    parts = field["field"].split(".")
    for index, raw_part in enumerate(parts):
        is_array = raw_part.endswith("[]")
        name = raw_part[:-2] if is_array else raw_part
        is_last = index == len(parts) - 1
        properties = current.setdefault("properties", {})
        if is_last:
            value_schema = _fixture_type_schema(field.get("type") or "")
            if field.get("description"):
                value_schema["description"] = field["description"]
            if is_array:
                value_schema = {"type": "array", "items": value_schema}
            # 子字段先写入时，父字段这一条只补类型和说明，不盖掉已经展开的子字段
            existing = properties.get(name)
            if isinstance(existing, dict):
                if existing.get("properties") and "properties" not in value_schema:
                    value_schema["properties"] = existing["properties"]
                existing_items = existing.get("items")
                if isinstance(existing_items, dict) and existing_items.get("properties"):
                    items = value_schema.setdefault("items", {})
                    items.setdefault("properties", existing_items["properties"])
                    items.setdefault("type", existing_items.get("type", "object"))
                    value_schema["type"] = "array"
            properties[name] = value_schema
            return
        if is_array:
            item_schema = properties.setdefault(
                name, {"type": "array", "items": {"type": "object", "properties": {}}}
            )["items"]
            current = item_schema
        else:
            current = properties.setdefault(name, {"type": "object", "properties": {}})
