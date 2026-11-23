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
import pytest

from apigateway.biz.skill.schema_converter import (
    ResourceParam,
    ResponseField,
    SchemaType,
    convert_schema_params,
    convert_schema_responses,
    get_response_schema,
    has_non_json_object_body,
)

pytestmark = pytest.mark.no_meta_schema

T = SchemaType.from_schema

SCHEMA = {
    "parameters": [
        {"name": "bk_biz_id", "in": "path", "required": True, "schema": {"type": "integer"}, "description": "业务 ID"},
        {"name": "keyword", "in": "query", "schema": {"type": "string"}},
        {"name": "X-Trace", "in": "header", "schema": {"type": "string"}},
        {"name": "sid", "in": "cookie", "schema": {"type": "string"}},
    ],
    "requestBody": {
        "content": {
            "application/json": {
                "schema": {
                    "type": "object",
                    "required": ["name"],
                    "properties": {
                        "name": {"type": "string", "description": "任务名"},
                        "hosts": {"type": "array", "items": {"type": "integer"}},
                    },
                }
            }
        }
    },
    "responses": {
        "400": {"description": "bad"},
        "201": {"description": "created"},
        "200": {
            "description": "ok",
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "result": {"type": "boolean"},
                            "data": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {"id": {"type": ["integer", "string"], "description": "任务 ID"}},
                                },
                            },
                        },
                    }
                }
            },
        },
    },
}


def test_convert_schema_params():
    assert convert_schema_params(SCHEMA) == [
        ResourceParam(
            name="bk_biz_id",
            location="path",
            required=True,
            description="业务 ID",
            schema={"type": "integer"},
        ),
        ResourceParam(name="keyword", location="query", schema={"type": "string"}),
        ResourceParam(name="X-Trace", location="header", schema={"type": "string"}),
        ResourceParam(
            name="name",
            location="body",
            required=True,
            description="任务名",
            schema={"type": "string", "description": "任务名"},
        ),
        ResourceParam(
            name="hosts",
            location="body",
            schema={"type": "array", "items": {"type": "integer"}},
        ),
    ]


def test_param_type_from_schema():
    assert [str(param.type) for param in convert_schema_params(SCHEMA)] == [
        "integer",
        "string",
        "string",
        "string",
        "array<integer>",
    ]


def test_param_keeps_published_schema():
    """嵌套对象数组、子字段必填、枚举都留在 schema 里，type 只是从它推导出的类型"""
    var_schema = {
        "type": "array",
        "items": {
            "type": "object",
            "required": ["name"],
            "additionalProperties": False,
            "properties": {
                "name": {"type": "string"},
                "kind": {"type": "string", "enum": ["string", "host"]},
                "server": {
                    "type": "object",
                    "properties": {"host_id_list": {"type": "array", "items": {"type": "integer"}}},
                },
            },
        },
    }
    scope_schema = {"type": "string", "enum": ["biz", "biz_set"], "description": "资源范围类型"}
    schema = {
        "parameters": [{"name": "bk_scope_type", "in": "query", "schema": scope_schema}],
        "requestBody": {
            "content": {
                "application/json": {"schema": {"type": "object", "properties": {"global_var_list": var_schema}}}
            }
        },
    }

    scope, var_list = convert_schema_params(schema)

    assert (str(scope.type), scope.description, scope.schema) == ("string", "资源范围类型", scope_schema)
    assert (str(var_list.type), var_list.schema) == ("array<object>", var_schema)


def test_param_serialization_kept():
    array_schema = {"type": "array", "items": {"type": "string"}}
    schema = {
        "parameters": [
            {"name": "status", "in": "query", "style": "form", "explode": False, "schema": array_schema},
            {"name": "path", "in": "query", "allowReserved": True, "schema": {"type": "string"}},
            {"name": "keyword", "in": "query", "schema": {"type": "string"}},
            # Swagger 2.0 导入的 collectionFormat=csv 被转成 simple，query 不允许，丢掉 style
            {"name": "ids", "in": "query", "style": "simple", "explode": False, "schema": array_schema},
            {"name": "X-Tags", "in": "header", "style": "simple", "schema": array_schema},
        ],
    }

    assert [param.serialization for param in convert_schema_params(schema)] == [
        {"style": "form", "explode": False},
        {"allowReserved": True},
        {},
        {"explode": False},
        {"style": "simple"},
    ]


def test_non_json_request_body_is_not_converted():
    schema = {
        "parameters": [{"name": "task_id", "in": "path", "required": True, "schema": {"type": "integer"}}],
        "requestBody": {
            "content": {
                "multipart/form-data": {
                    "schema": {
                        "type": "object",
                        "required": ["file"],
                        "properties": {"file": {"type": "string", "description": "文件"}},
                    }
                }
            }
        },
    }

    assert has_non_json_object_body(schema)
    assert convert_schema_params(schema) == [
        ResourceParam(name="task_id", location="path", required=True, schema={"type": "integer"}),
    ]


def test_json_request_body_preferred_over_other_content_types():
    schema = {
        "requestBody": {
            "content": {
                "multipart/form-data": {"schema": {"type": "object", "properties": {"file": {"type": "string"}}}},
                "application/json": {
                    "schema": {"type": "object", "properties": {"name": {"type": "string"}}, "required": ["name"]}
                },
            }
        }
    }

    assert not has_non_json_object_body(schema)
    assert convert_schema_params(schema) == [
        ResourceParam(name="name", location="body", required=True, schema={"type": "string"}),
    ]


def test_json_content_type_with_parameters():
    body = {"type": "object", "properties": {"name": {"type": "string"}}}
    schema = {
        "requestBody": {"content": {"application/json; charset=utf-8": {"schema": body}}},
        "responses": {"200": {"content": {"application/json;charset=UTF-8": {"schema": body}}}},
    }

    assert not has_non_json_object_body(schema)
    assert convert_schema_params(schema) == [ResourceParam(name="name", location="body", schema={"type": "string"})]
    assert convert_schema_responses(schema) == [ResponseField(field="name", type=T({"type": "string"}))]


@pytest.mark.parametrize(
    "body_schema, expected",
    [
        ({"type": "array", "items": {"type": "object", "properties": {"id": {"type": "integer"}}}}, True),
        ({"type": "string"}, True),
        ({"type": "object", "properties": {"id": {"type": "integer"}}}, False),
        ({"properties": {"id": {"type": "integer"}}}, False),
        (None, False),
    ],
)
def test_has_non_json_object_body(body_schema, expected):
    schema = {"requestBody": {"content": {"application/json": {"schema": body_schema}}}} if body_schema else {}

    assert has_non_json_object_body(schema) is expected


def test_convert_schema_responses():
    assert [(item.field, str(item.type), item.description) for item in convert_schema_responses(SCHEMA)] == [
        ("result", "boolean", ""),
        ("data", "array<object>", ""),
        ("data[].id", "integer|string", "任务 ID"),
    ]


def test_get_response_schema_is_published_schema():
    response = SCHEMA["responses"]["200"]["content"]["application/json"]["schema"]

    assert get_response_schema(SCHEMA) is response


def test_nullable_array_items_are_expanded():
    data_schema = {"type": ["array", "null"], "items": {"properties": {"id": {"type": "integer"}}}}
    schema = {
        "responses": {"200": {"content": {"application/json": {"schema": {"properties": {"data": data_schema}}}}}}
    }

    assert [(item.field, str(item.type)) for item in convert_schema_responses(schema)] == [
        ("data", "array<object>|null"),
        ("data[].id", "integer"),
    ]


@pytest.mark.parametrize("schema", [{}, {"responses": {"404": {}}}, {"responses": {"200": {"description": "ok"}}}])
def test_convert_empty(schema):
    assert convert_schema_params(schema) == []
    assert convert_schema_responses(schema) == []
    assert get_response_schema(schema) == {}


class TestSchemaType:
    @pytest.mark.parametrize(
        "schema, expected",
        [
            ({"type": "string"}, "string"),
            ({"type": ["null", "integer"]}, "integer|null"),
            ({"type": "array", "items": {"type": "string"}}, "array<string>"),
            ({"type": ["array", "null"], "items": {"type": "string"}}, "array<string>|null"),
            ({"type": "array", "items": {"type": ["string", "integer"]}}, "array<integer|string>"),
            ({"type": "array"}, "array"),
            ({"properties": {}}, "object"),
        ],
    )
    def test_text(self, schema, expected):
        assert str(T(schema)) == expected

    @pytest.mark.parametrize("schema", [{}, {"type": []}, {"oneOf": [{"type": "string"}]}])
    def test_untyped(self, schema):
        assert T(schema) is None

    @pytest.mark.parametrize(
        "text",
        ["string", "integer|null", "array", "array<object>", "array<integer|string>|null", "array<array<string>>"],
    )
    def test_parse_round_trip(self, text):
        assert str(SchemaType.parse(text)) == text

    def test_parse_matches_schema(self):
        assert SchemaType.parse("null|array<string>") == T({"type": ["array", "null"], "items": {"type": "string"}})
        assert SchemaType.parse("string|integer") == T({"type": ["integer", "string"]})

    @pytest.mark.parametrize(
        "text", ["", "list", "Integer", "array<>", "string|string", "array|array<string>", "array<object", "a>|b"]
    )
    def test_parse_invalid(self, text):
        with pytest.raises(ValueError):
            SchemaType.parse(text)

    def test_union_order_ignored(self):
        assert T({"type": ["integer", "string"]}) == T({"type": ["string", "integer"]})
        assert T({"type": "array", "items": {"type": "integer"}}) != T({"type": "array"})

    def test_array_of(self):
        assert SchemaType.array_of(T({"type": "integer"})) == T({"type": "array", "items": {"type": "integer"}})

    @pytest.mark.parametrize(
        "schema, value, expected",
        [
            ({"type": "integer"}, 1, True),
            ({"type": "integer"}, True, False),
            ({"type": "integer"}, 1.5, False),
            ({"type": "number"}, 1, True),
            ({"type": ["string", "null"]}, None, True),
            ({"type": "string"}, None, False),
            ({"type": "array", "items": {"type": "integer"}}, [1, 2], True),
            ({"type": "array", "items": {"type": "integer"}}, [1, "a"], False),
            ({"type": "array"}, [1, "a"], True),
            ({"type": "object"}, {}, True),
            ({"type": "file"}, "x", True),
        ],
    )
    def test_matches(self, schema, value, expected):
        assert T(schema).matches(value) is expected
