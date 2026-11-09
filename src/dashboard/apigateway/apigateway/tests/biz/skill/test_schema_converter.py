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

from apigateway.biz.skill import ResourceParam, ResponseField
from apigateway.biz.skill.schema_converter import convert_schema_params, convert_schema_responses, schema_type_text

pytestmark = pytest.mark.no_meta_schema

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
        ResourceParam(name="bk_biz_id", location="path", type="integer", required=True, description="业务 ID"),
        ResourceParam(name="keyword", location="query", type="string"),
        ResourceParam(name="X-Trace", location="header", type="string"),
        ResourceParam(name="name", location="body", type="string", required=True, description="任务名"),
        ResourceParam(name="hosts", location="body", type="array<integer>"),
    ]


def test_convert_schema_responses():
    assert convert_schema_responses(SCHEMA) == [
        ResponseField(field="result", type="boolean"),
        ResponseField(field="data", type="array<object>"),
        ResponseField(field="data[].id", type="integer|string", description="任务 ID"),
    ]


@pytest.mark.parametrize("schema", [{}, {"responses": {"404": {}}}, {"responses": {"200": {"description": "ok"}}}])
def test_convert_empty(schema):
    assert convert_schema_params(schema) == []
    assert convert_schema_responses(schema) == []


@pytest.mark.parametrize(
    "schema, expected",
    [
        ({"type": "string"}, "string"),
        ({"type": ["integer", "null"]}, "integer|null"),
        ({"type": "array", "items": {"type": "string"}}, "array<string>"),
        ({"type": "array"}, "array"),
        ({"properties": {}}, "object"),
        ({}, ""),
    ],
)
def test_schema_type_text(schema, expected):
    assert schema_type_text(schema) == expected
