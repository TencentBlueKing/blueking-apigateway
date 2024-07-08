#
# TencentBlueKing is pleased to support the open source community by making
# 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
# Copyright (C) 2017 THL A29 Limited, a Tencent company. All rights reserved.
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

from apigateway.utils import openapi
from apigateway.utils.openapi import generate_parameters_example, get_openapi_example


class TestOpenAPI:
    @pytest.mark.parametrize(
        "schema, expected",
        [
            ({"type": "string", "example": "John Doe"}, "John Doe"),
            ({"type": "integer", "example": 42}, 42),
            (
                {"type": "object", "properties": {"name": {"type": "string", "example": "John Doe"}}},
                {"name": "John Doe"},
            ),
            ({"type": "array", "items": {"type": "string", "example": "item"}}, ["item"]),
            ({"type": "string", "format": "email"}, None),
            # We can't predict the exact email, so we check type later
            ({"type": "integer", "minimum": 10, "maximum": 20}, None),
            # We can't predict the exact number, so we check range later
            ({"type": "string", "enum": ["red", "green", "blue"]}, None),
            # We can't predict the exact value, so we check if it's in enum
        ],
    )
    def test_generate_example(self, schema, expected):
        result = openapi.generate_example(schema)
        if expected is not None:
            assert result == expected
        elif schema["type"] == "string" and schema.get("format") == "email":
            assert "@" in result  # Simple check to ensure it's an email
        elif schema["type"] == "integer":
            assert schema["minimum"] <= result <= schema["maximum"]
        elif "enum" in schema:
            assert result in schema["enum"]

    @pytest.mark.parametrize(
        "parameters, expected_path, expected_query, expected_headers",
        [
            (
                [
                    {"name": "userId", "in": "path", "example": "123"},
                    {"name": "search", "in": "query", "example": "test"},
                    {"name": "Authorization", "in": "header", "example": "Bearer token"},
                ],
                {"userId": "123"},
                {"search": "test"},
                {"Authorization": "Bearer token"},
            ),
            (
                [
                    {"name": "userId", "in": "path"},
                    {"name": "search", "in": "query"},
                    {"name": "Authorization", "in": "header"},
                ],
                {"userId": "example_value"},
                {"search": "example_value"},
                {"Authorization": "example_value"},
            ),
            ([], {}, {}, {}),
        ],
    )
    def test_generate_parameters_example(self, parameters, expected_path, expected_query, expected_headers):
        path_params, query_params, headers = generate_parameters_example(parameters)
        assert path_params == expected_path
        assert query_params == expected_query
        assert headers == expected_headers

    @pytest.mark.parametrize(
        "schema, expected_example",
        [
            (
                {
                    "requestBody": {
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "id": {"type": "integer", "example": 1},
                                        "name": {"type": "string", "example": "test"},
                                    },
                                }
                            }
                        }
                    },
                    "parameters": [
                        {"name": "userId", "in": "path", "example": "123"},
                        {"name": "search", "in": "query", "example": "test"},
                        {"name": "Authorization", "in": "header", "example": "Bearer token"},
                    ],
                },
                {
                    "body_example": {"id": 1, "name": "test"},
                    "path_params": {"userId": "123"},
                    "query_params": {"search": "test"},
                    "headers": {"Authorization": "Bearer token"},
                },
            )
        ],
    )
    def test_get_openapi_example(self, schema, expected_example):
        example = get_openapi_example(schema)
        assert example == expected_example
