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

类型用 SchemaType 表示，文本写法为 `string`、`array<string>`、`integer|string`、`array<object>|null`；
声明里输入、输出的 type 用同一写法，由 SchemaType.parse 解析。
响应字段用相对响应体的字段路径表示，数组层级写成 `[]`，如 `data.items[].id`。
"""

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, FrozenSet, List, Optional, Set

JSON_CONTENT_TYPE = "application/json"
# OpenAPI Parameter 上决定取值如何写进路径、query、header 的字段，和 schema 平级
PARAM_SERIALIZATION_KEYS = ("style", "explode", "allowReserved")

_JSON_TYPE_CHECKS: Dict[str, Callable[[Any], bool]] = {
    "string": lambda value: isinstance(value, str),
    "integer": lambda value: isinstance(value, int) and not isinstance(value, bool),
    "number": lambda value: isinstance(value, (int, float)) and not isinstance(value, bool),
    "boolean": lambda value: isinstance(value, bool),
    "object": lambda value: isinstance(value, dict),
    "null": lambda value: value is None,
}
# 声明里能写的类型名
TYPE_NAMES = frozenset([*_JSON_TYPE_CHECKS, "array"])


def _split_union(text: str) -> List[str]:
    """按顶层的 | 拆开联合类型，array<…> 里的 | 不拆

    例如："array<integer|string>|null" -> ["array<integer|string>", "null"]
    """
    parts, depth, start = [], 0, 0
    for index, char in enumerate(text):
        if char == "<":
            depth += 1
        elif char == ">":
            depth -= 1
        elif char == "|" and depth == 0:
            parts.append(text[start:index])
            start = index + 1
    parts.append(text[start:])
    return parts


@dataclass(frozen=True)
class SchemaType:
    """JSON Schema 的 type；含 array 时 items 是元素类型，元素没写类型时为 None。
    联合类型与书写顺序无关，直接用 == 比较。"""

    types: FrozenSet[str]
    items: Optional["SchemaType"] = None

    @classmethod
    def from_schema(cls, schema: Dict[str, Any]) -> Optional["SchemaType"]:
        """JSON Schema -> 类型；没写 type 也没有 properties 时为 None

        例如：
            {"type": "array", "items": {"type": "integer"}} -> array<integer>
            {"type": ["array", "null"], "items": {"type": "string"}} -> array<string>|null
            {"properties": {...}}（没写 type） -> object
            {}、{"oneOf": [...]} -> None
        """
        schema_type = schema.get("type")
        if isinstance(schema_type, str):
            types = frozenset([schema_type])
        elif isinstance(schema_type, list) and schema_type:
            types = frozenset(schema_type)
        elif "properties" in schema:
            types = frozenset(["object"])
        else:
            return None
        items = cls.from_schema(schema.get("items") or {}) if "array" in types else None
        return cls(types, items)

    @classmethod
    def parse(cls, text: str) -> "SchemaType":
        """类型文本 -> 类型，str() 的逆运算；联合类型里的名字不能重复，数组最多一种元素类型。不合规时抛 ValueError

        例如：
            "array<object>" -> array<object>
            "string|integer" -> integer|string
            "array<integer|string>|null" -> array<integer|string>|null
            "list"、"string|string"、"array<>"、"array|array<string>" -> ValueError
        """
        names: Set[str] = set()
        items = None
        for part in _split_union(text):
            name = part
            if part.startswith("array<") and part.endswith(">"):
                name, items = "array", cls.parse(part[len("array<") : -1])
            if name not in TYPE_NAMES or name in names:
                raise ValueError(text)
            names.add(name)
        return cls(frozenset(names), items)

    @classmethod
    def array_of(cls, item: "SchemaType") -> "SchemaType":
        """以 item 为元素的数组

        例如：integer -> array<integer>
        """
        return cls(frozenset(["array"]), item)

    @property
    def is_array(self) -> bool:
        """取值可以是数组，含可空数组 array<x>|null"""
        return "array" in self.types

    def matches(self, value: Any) -> bool:
        """YAML/JSON 值是否符合类型；不认识的类型名不限制取值

        例如：
            (1, integer) -> True；(True, integer) -> False（布尔值不算整数）
            ([1, "a"], array<integer|string>) -> True
            (None, string|null) -> True
        """
        for name in self.types:
            if name == "array":
                if isinstance(value, list) and (self.items is None or all(self.items.matches(item) for item in value)):
                    return True
            elif _JSON_TYPE_CHECKS.get(name, lambda _value: True)(value):
                return True
        return False

    def __str__(self) -> str:
        """类型文本，按名字排序、null 放最后

        例如：array<integer>；integer|string；array<object>|null；元素没写类型的数组为 array
        """
        names = sorted(self.types, key=lambda name: (name == "null", name))
        return "|".join(f"array<{self.items}>" if name == "array" and self.items else name for name in names)


@dataclass
class ResourceParam:
    name: str
    location: str  # path / query / header / body
    required: bool = False
    description: str = ""
    schema: Dict[str, Any] = field(default_factory=dict)
    # 定义里写了的 PARAM_SERIALIZATION_KEYS；body 参数按 JSON 发送，没有这些字段
    serialization: Dict[str, Any] = field(default_factory=dict)

    @property
    def type(self) -> Optional[SchemaType]:
        """schema 的类型，没写类型时为 None"""
        return SchemaType.from_schema(self.schema)


@dataclass
class ResponseField:
    field: str
    type: Optional[SchemaType] = None
    description: str = ""


def has_non_json_object_body(schema: Dict[str, Any]) -> bool:
    """有请求体，但不是 application/json，或 JSON 的顶层不是对象。body 参数取自对象的顶层属性，这种请求体不转成 body 参数

    例如：
        requestBody.content 只有 multipart/form-data -> True
        JSON 请求体为 {"type": "array", "items": {...}} -> True
        JSON 请求体为 {"type": "object", ...} 或只写了 properties，content type 可带 charset；没有 requestBody -> False
    """
    content = (schema.get("requestBody") or {}).get("content") or {}
    if not content:
        return False
    media = _json_media(content)
    if media is None:
        return True
    body_type = SchemaType.from_schema(media.get("schema") or {})
    return body_type is not None and body_type.types != {"object"}


def convert_schema_params(schema: Dict[str, Any]) -> List[ResourceParam]:
    """parameters 转成 path / query / header 参数，requestBody 的 JSON 对象顶层属性转成 body 参数

    例如：
        parameters 为 [{"name": "task_id", "in": "path", "required": True, "schema": {"type": "integer"}}]
            -> ResourceParam(name="task_id", location="path", required=True, schema={"type": "integer"}, ...)
        query 参数写了 "explode": False -> ResourceParam(..., serialization={"explode": False})
        requestBody 的 JSON schema 为 {"required": ["name"], "properties": {"name": {"type": "string"}}}
            -> ResourceParam(name="name", location="body", required=True, schema={"type": "string"}, ...)
        in 为 cookie 的参数 -> 忽略
    """
    params = [
        ResourceParam(
            name=item["name"],
            location=item["in"],
            required=bool(item.get("required", False)),
            description=item.get("description") or (item.get("schema") or {}).get("description") or "",
            schema=item.get("schema") or {},
            serialization=_param_serialization(item),
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
                required=name in required,
                description=prop.get("description") or "",
                schema=prop,
            )
        )
    return params


def get_response_schema(schema: Dict[str, Any]) -> Dict[str, Any]:
    """第一个 2xx 响应的 application/json schema，原样返回；没有 2xx 响应或它没有 JSON 内容时为 {}

    例如：
        responses 有 200 和 400 -> 200 的 application/json schema
        200 只有 text/plain -> {}
        只有 400 -> {}
    """
    return _json_content_schema(_first_success_response(schema))


def has_non_json_response(schema: Dict[str, Any]) -> bool:
    """第一个 2xx 响应有内容，但没有 application/json

    例如：
        200 只有 text/xml 或 */* -> True
        200 有 application/json; charset=utf-8 -> False
        200 没有 content、没有 2xx 响应 -> False
    """
    content = _first_success_response(schema).get("content") or {}
    return bool(content) and _json_media(content) is None


def convert_schema_responses(schema: Dict[str, Any]) -> List[ResponseField]:
    """第一个 2xx 响应的 schema 展开成字段路径，用于查找引用的字段；数组元素的字段写成 `<数组>[].<字段>`

    例如：200 响应为 {"properties": {"data": {"type": "array", "items": {"properties": {"id": {"type": "integer"}}}}}}
        -> [ResponseField("data", array<object>), ResponseField("data[].id", integer)]
        没有 2xx 响应 -> []
    """
    fields: List[ResponseField] = []
    _collect_fields(get_response_schema(schema), "", fields)
    return fields


def _param_serialization(param: Dict[str, Any]) -> Dict[str, Any]:
    """取参数上写了的 PARAM_SERIALIZATION_KEYS

    例如：{"in": "query", "style": "form", "explode": False} -> {"style": "form", "explode": False}
        {"in": "query", "style": "simple", "explode": False} -> {"explode": False}
    """
    serialization = {key: param[key] for key in PARAM_SERIALIZATION_KEYS if key in param}
    # Swagger 2.0 导入会给 query 参数写上 OpenAPI 不允许的 style: simple（biz/openapi/schema.py）
    if param["in"] == "query" and serialization.get("style") == "simple":
        del serialization["style"]
    return serialization


def _first_success_response(schema: Dict[str, Any]) -> Dict[str, Any]:
    """按状态码排序后的第一个 2xx 响应对象；没有时为 {}

    例如：responses 有 201 和 200 -> 200 的响应对象；只有 400 -> {}
    """
    responses = schema.get("responses") or {}
    success_codes = sorted(code for code in responses if str(code).startswith("2"))
    return (responses[success_codes[0]] or {}) if success_codes else {}


def _json_content_schema(container: Dict[str, Any]) -> Dict[str, Any]:
    """只取 application/json 的 schema；请求体和响应都不退回其他 content type，调用说明只按 JSON 写

    例如：{"content": {"application/json": {"schema": {"type": "object"}}}} -> {"type": "object"}；
    只有 multipart/form-data 或 text/plain -> {}
    """
    return (_json_media(container.get("content") or {}) or {}).get("schema") or {}


def _json_media(content: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """content 里 application/json 的 media 对象，忽略 charset 等参数；没有时为 None

    例如：{"application/json; charset=utf-8": {...}} -> {...}；只有 multipart/form-data -> None
    """
    return next(
        (media or {} for key, media in content.items() if key.split(";")[0].strip().lower() == JSON_CONTENT_TYPE),
        None,
    )


def _collect_fields(schema: Dict[str, Any], prefix: str, fields: List[ResponseField]) -> None:
    """递归展开 properties，把字段路径追加到 fields；数组字段继续展开元素，路径加 []

    例如：prefix 为 "data"，schema 为 {"properties": {"tags": {"type": "array", "items": {"type": "string"}}}}
        -> 追加 ResponseField("data.tags", array<string>)；元素没有 properties，不再追加
        可空数组 {"type": ["array", "null"], "items": {...}} 同样展开元素
    """
    for name, raw_prop in (schema.get("properties") or {}).items():
        prop = raw_prop or {}
        path = f"{prefix}.{name}" if prefix else name
        prop_type = SchemaType.from_schema(prop)
        fields.append(ResponseField(field=path, type=prop_type, description=prop.get("description") or ""))
        if prop_type and prop_type.is_array:
            _collect_fields(prop.get("items") or {}, f"{path}[]", fields)
        else:
            _collect_fields(prop, path, fields)
