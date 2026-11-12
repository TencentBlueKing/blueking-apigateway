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
"""将资源的 OpenAPI schema 转换为 Skill 用的参数和响应字段。

类型写法：`string`、`integer`、`array<string>`；多种类型用 `|` 连接，如 `array|integer|string`。
响应字段用相对响应体的字段路径表示，数组层级写成 `[]`，如 `data.items[].id`。
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List

JSON_CONTENT_TYPE = "application/json"


@dataclass
class ResourceParam:
    name: str
    location: str  # path / query / header / body
    type: str = ""
    required: bool = False
    description: str = ""
    schema: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ResponseField:
    field: str
    type: str = ""
    description: str = ""


def has_non_json_request_body(schema: Dict[str, Any]) -> bool:
    """有请求体，但没有 application/json。这种请求体不转成 body 参数。"""
    content = (schema.get("requestBody") or {}).get("content") or {}
    return bool(content) and JSON_CONTENT_TYPE not in content


def convert_schema_params(schema: Dict[str, Any]) -> List[ResourceParam]:
    """parameters 转成 path / query / header 参数，requestBody 的 JSON 对象顶层属性转成 body 参数"""
    params = [
        ResourceParam(
            name=item["name"],
            location=item["in"],
            type=schema_type_text(item.get("schema") or {}),
            required=bool(item.get("required", False)),
            description=item.get("description") or (item.get("schema") or {}).get("description") or "",
            schema=item.get("schema") or {},
        )
        for item in schema.get("parameters") or []
        if item.get("name") and item.get("in") in ("path", "query", "header")
    ]

    body_schema = _json_content_schema(schema.get("requestBody") or {})
    required = set(body_schema.get("required") or [])
    for name, prop in (body_schema.get("properties") or {}).items():
        params.append(
            ResourceParam(
                name=name,
                location="body",
                type=schema_type_text(prop),
                required=name in required,
                description=prop.get("description") or "",
                schema=prop,
            )
        )
    return params


def convert_schema_responses(schema: Dict[str, Any]) -> List[ResponseField]:
    """取第一个 2xx 响应的 JSON schema，展开成字段路径；数组元素的字段写成 `<数组>[].<字段>`"""
    responses = schema.get("responses") or {}
    success_codes = sorted(code for code in responses if str(code).startswith("2"))
    if not success_codes:
        return []

    fields: List[ResponseField] = []
    _collect_fields(_get_content_schema(responses[success_codes[0]] or {}), "", fields)
    return fields


def schema_type_text(schema: Dict[str, Any]) -> str:
    """JSON Schema -> 资源定义里的类型写法：string、array<string>、integer|string"""
    schema_type = schema.get("type")
    if isinstance(schema_type, list):
        return "|".join(schema_type)
    if schema_type == "array":
        item_type = schema_type_text(schema.get("items") or {})
        return f"array<{item_type}>" if item_type else "array"
    if not schema_type and "properties" in schema:
        return "object"
    return schema_type or ""


def _json_content_schema(container: Dict[str, Any]) -> Dict[str, Any]:
    """只取 application/json。请求体没有 JSON 时不退回其他 content type，避免被渲染成 JSON。"""
    content = container.get("content") or {}
    return ((content.get(JSON_CONTENT_TYPE) or {}).get("schema")) or {}


def _get_content_schema(container: Dict[str, Any]) -> Dict[str, Any]:
    """响应：没有 application/json 时退回第一个 content type。"""
    content = container.get("content") or {}
    if not content:
        return {}
    media = content.get(JSON_CONTENT_TYPE) or next(iter(content.values()))
    return (media or {}).get("schema") or {}


def _collect_fields(schema: Dict[str, Any], prefix: str, fields: List[ResponseField]) -> None:
    for name, raw_prop in (schema.get("properties") or {}).items():
        prop = raw_prop or {}
        path = f"{prefix}.{name}" if prefix else name
        fields.append(
            ResponseField(field=path, type=schema_type_text(prop), description=prop.get("description") or "")
        )
        if prop.get("type") == "array":
            _collect_fields(prop.get("items") or {}, f"{path}[]", fields)
        else:
            _collect_fields(prop, path, fields)
