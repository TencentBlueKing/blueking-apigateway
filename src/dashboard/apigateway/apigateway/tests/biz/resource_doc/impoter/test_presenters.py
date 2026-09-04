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
import copy

import pytest

from apigateway.biz.resource_doc import OpenAPIDocGenerationError
from apigateway.biz.resource_doc.importer.presenters import OperationDocBuilder


def _openapi(operation, *, method="post", path="/users/{user_id}"):
    return {
        "openapi": "3.1.0",
        "info": {"title": "users", "version": "1.0.0"},
        "paths": {path: {method: operation}},
    }


def test_build_operation_doc_context():
    openapi = _openapi(
        {
            "operationId": "update_user",
            "summary": "Update user",
            "description": "Updates a user profile.",
            "deprecated": True,
            "tags": ["users"],
            "parameters": [
                {
                    "name": "user_id",
                    "in": "path",
                    "required": True,
                    "description": "User identifier",
                    "schema": {"type": "integer", "format": "int64", "minimum": 1},
                },
                {
                    "name": "verbose",
                    "in": "query",
                    "schema": {"type": ["boolean", "null"], "default": False},
                },
            ],
            "requestBody": {
                "required": True,
                "description": "Profile data",
                "content": {
                    "application/json": {
                        "schema": {
                            "type": "object",
                            "required": ["profile"],
                            "properties": {
                                "profile": {
                                    "type": "object",
                                    "properties": {
                                        "name": {"type": "string", "minLength": 1},
                                        "roles": {"type": "array", "items": {"type": "string"}},
                                    },
                                }
                            },
                        },
                        "example": {"profile": {"name": "Alice", "roles": ["admin"]}},
                    }
                },
            },
            "responses": {"204": {"description": "Updated"}},
        }
    )

    doc = OperationDocBuilder(openapi).build()

    assert (doc.operation_id, doc.method, doc.path) == ("update_user", "POST", "/users/{user_id}")
    assert doc.summary == "Update user"
    assert doc.deprecated is True
    assert doc.tags == ["users"]
    assert doc.parameters[0].type == "integer<int64>"
    assert doc.parameters[0].constraints == "minimum: 1"
    assert doc.parameters[1].type == "boolean \\| null"
    assert doc.parameters[1].default == "false"
    assert doc.request_body is not None
    assert doc.request_body.required is True
    assert [field.path for field in doc.request_body.contents[0].schema.fields] == [
        "profile",
        "profile.name",
        "profile.roles",
        "profile.roles[]",
    ]
    assert doc.request_body.contents[0].examples[0].value == (
        '{\n  "profile": {\n    "name": "Alice",\n    "roles": [\n      "admin"\n    ]\n  }\n}'
    )


def test_build_responses_with_headers_and_named_examples():
    openapi = _openapi(
        {
            "operationId": "create_user",
            "responses": {
                "201": {
                    "description": "Created",
                    "headers": {
                        "X-Request-ID": {
                            "description": "Request identifier",
                            "required": True,
                            "schema": {"type": "string", "example": "req-1"},
                        }
                    },
                    "content": {
                        "application/json": {
                            "schema": {"type": "object", "properties": {"id": {"type": "integer"}}},
                            "examples": {
                                "created": {
                                    "summary": "Created user",
                                    "value": {"id": 1},
                                },
                                "empty": {"value": None},
                            },
                        }
                    },
                },
                "2XX": {"description": "Any success"},
                "default": {"description": "Unexpected"},
            },
        }
    )

    responses = OperationDocBuilder(openapi).build().responses

    assert [response.status_code for response in responses] == ["201", "2XX", "default"]
    assert [response.status_text for response in responses] == ["Created", "", ""]
    assert responses[0].headers[0].name == "X-Request-ID"
    assert responses[0].headers[0].location == "header"
    assert responses[0].headers[0].example == "req-1"
    assert [(example.name, example.summary, example.value) for example in responses[0].contents[0].examples] == [
        ("created", "Created user", '{\n  "id": 1\n}'),
        ("empty", "", "null"),
    ]


def test_build_parameter_from_content_schema():
    openapi = _openapi(
        {
            "operationId": "list_users",
            "parameters": [
                {
                    "name": "filter",
                    "in": "query",
                    "content": {
                        "application/json": {
                            "schema": {"type": "object", "example": {"active": True}},
                        }
                    },
                    "example": {"active": False},
                }
            ],
            "responses": {"200": {"description": "OK"}},
        }
    )

    parameter = OperationDocBuilder(openapi).build().parameters[0]

    assert parameter.type == "object"
    assert parameter.example == '{<br>  "active": false<br>}'


def test_schema_type_expressions_for_array_map_and_compositions():
    openapi = _openapi(
        {
            "operationId": "types",
            "requestBody": {
                "content": {
                    "application/json": {
                        "schema": {
                            "type": "object",
                            "properties": {
                                "ids": {"type": "array", "items": {"type": "integer", "format": "int64"}},
                                "metadata": {"type": "object", "additionalProperties": {"type": "string"}},
                                "choice": {"oneOf": [{"type": "string"}, {"type": "integer"}]},
                                "loose": {"anyOf": [{"type": "boolean"}, {"type": "null"}]},
                                "combined": {
                                    "allOf": [
                                        {"type": "object", "properties": {"name": {"type": "string"}}},
                                        {"type": "object", "properties": {"age": {"type": "integer"}}},
                                    ]
                                },
                                "optional": {"type": "string", "nullable": True},
                            },
                        }
                    }
                }
            },
            "responses": {"200": {"description": "OK"}},
        }
    )

    schema = OperationDocBuilder(openapi).build().request_body.contents[0].schema
    fields = {field.path: field.type for field in schema.fields}

    assert fields["ids"] == "array<integer<int64>>"
    assert fields["metadata"] == "map<string, string>"
    assert fields["choice"] == "oneOf<string \\| integer>"
    assert fields["loose"] == "anyOf<boolean \\| null>"
    assert fields["combined"] == "allOf<object & object>"
    assert fields["combined.name"] == "string"
    assert fields["combined.age"] == "integer"
    assert fields["optional"] == "string \\| null"


def test_schema_constraints_include_supported_keywords_in_stable_order():
    openapi = _openapi(
        {
            "operationId": "constraints",
            "parameters": [
                {
                    "name": "value",
                    "in": "query",
                    "schema": {
                        "type": "string",
                        "enum": ["a", "b"],
                        "default": "a",
                        "minimum": 1,
                        "exclusiveMinimum": True,
                        "maximum": 10,
                        "exclusiveMaximum": False,
                        "minLength": 1,
                        "maxLength": 10,
                        "pattern": "a|b",
                        "minItems": 1,
                        "maxItems": 2,
                    },
                }
            ],
            "responses": {"200": {"description": "OK"}},
        }
    )

    constraints = OperationDocBuilder(openapi).build().parameters[0].constraints

    assert constraints == (
        'enum: [<br>  "a",<br>  "b"<br>]<br>default: a<br>minimum: 1<br>exclusiveMinimum: true'
        "<br>maximum: 10<br>exclusiveMaximum: false<br>minLength: 1<br>maxLength: 10"
        "<br>pattern: a\\|b<br>minItems: 1<br>maxItems: 2"
    )


def test_schema_cycle_is_marked_without_recursing_forever():
    node = {"type": "object", "properties": {}}
    node["properties"]["child"] = node
    openapi = _openapi(
        {
            "operationId": "recursive",
            "requestBody": {"content": {"application/json": {"schema": node}}},
            "responses": {"200": {"description": "OK"}},
        }
    )

    fields = OperationDocBuilder(openapi).build().request_body.contents[0].schema.fields

    assert [(field.path, field.constraints) for field in fields] == [("child", "recursive")]


def test_schema_depth_is_limited_to_eight():
    root = {"type": "object", "properties": {}}
    current = root
    for index in range(1, 11):
        child = {"type": "object", "properties": {}}
        current["properties"][f"level_{index}"] = child
        current = child
    openapi = _openapi(
        {
            "operationId": "deep",
            "requestBody": {"content": {"application/json": {"schema": root}}},
            "responses": {"200": {"description": "OK"}},
        }
    )

    fields = OperationDocBuilder(openapi).build().request_body.contents[0].schema.fields

    assert len(fields) == 8
    assert fields[-1].path.endswith("level_8")
    assert fields[-1].constraints == "max-depth: 8"


def test_table_values_escape_pipe_and_newline():
    openapi = _openapi(
        {
            "operationId": "escape",
            "summary": "first|second\nthird",
            "parameters": [
                {
                    "name": "x|name",
                    "in": "header",
                    "description": "line 1\r\nline 2",
                    "schema": {"type": "string", "pattern": "a|b"},
                }
            ],
            "responses": {"200": {"description": "OK"}},
        }
    )

    doc = OperationDocBuilder(openapi).build()

    assert doc.summary == "first\\|second<br>third"
    assert doc.parameters[0].name == "x\\|name"
    assert doc.parameters[0].description == "line 1<br>line 2"
    assert doc.parameters[0].constraints == "pattern: a\\|b"


def test_build_is_deterministic_and_does_not_mutate_openapi():
    openapi = _openapi(
        {
            "operationId": "stable",
            "requestBody": {
                "content": {
                    "application/json": {
                        "schema": {"type": "array", "example": [{"b": 2, "a": 1}]},
                    },
                    "text/plain": {"example": "hello"},
                }
            },
            "responses": {"200": {"description": "OK"}},
        }
    )
    original = copy.deepcopy(openapi)

    first = OperationDocBuilder(openapi).build()
    second = OperationDocBuilder(openapi).build()

    assert first == second
    assert openapi == original
    assert [item.media_type for item in first.request_body.contents] == ["application/json", "text/plain"]
    assert first.request_body.contents[0].examples[0].value == '[\n  {\n    "a": 1,\n    "b": 2\n  }\n]'


@pytest.mark.parametrize(
    "paths",
    [
        {"/users": {"parameters": []}},
        {
            "/users": {
                "get": {"operationId": "get_users", "responses": {}},
                "post": {"operationId": "create_user", "responses": {}},
            }
        },
    ],
)
def test_build_rejects_zero_or_multiple_operations(paths):
    with pytest.raises(OpenAPIDocGenerationError):
        OperationDocBuilder({"openapi": "3.0.1", "info": {}, "paths": paths}).build()
