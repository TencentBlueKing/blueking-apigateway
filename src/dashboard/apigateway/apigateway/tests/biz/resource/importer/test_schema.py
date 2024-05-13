#  -*- coding: utf-8 -*-
#  #
#  TencentBlueKing is pleased to support the open source community by making
#  蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
#  Copyright (C) 2017 THL A29 Limited, a Tencent company. All rights reserved.
#  Licensed under the MIT License (the "License"); you may not use this file except
#  in compliance with the License. You may obtain a copy of the License at
#  #
#      http://opensource.org/licenses/MIT
#  #
#  Unless required by applicable law or agreed to in writing, software distributed under
#  the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND,
#  either express or implied. See the License for the specific language governing permissions and
#  limitations under the License.
#  #
#  We undertake not to change the open source license (MIT license) applicable
#  to the current version of the project delivered to anyone in the future.
#  #
import pytest

from apigateway.biz.resource.importer.schema import (
    convert_openapi2_formdata_to_openapi,
    convert_openapi2_parameters_to_openapi,
    convert_openapi2_response_headers_to_openapi,
    convert_operation_v3_to_v2,
    convert_parameters_to_openapi2,
    convert_request_body_to_openapi2,
    convert_responses_to_openapi2,
)


class TestSchema:
    def test_convert_openapi2_formdata_to_openapi(self):
        formdata_params = [
            {"name": "file", "type": "file", "required": True},
            {"name": "name", "type": "string", "required": False},
        ]
        consumers = ["application/json"]

        expected_output = {
            "content": {
                "multipart/form-data": {
                    "type": "object",
                    "properties": {"file": {"type": "string"}, "name": {"type": "string"}},
                    "required": ["file"],
                }
            }
        }

        result = convert_openapi2_formdata_to_openapi(formdata_params, consumers)
        assert result == expected_output

    def test_convert_openapi2_parameters_to_openapi(self):
        parameters = [{"name": "id", "in": "query", "type": "integer", "required": True}]

        expected_output = [
            {"name": "id", "in": "query", "required": True, "description": "", "schema": {"type": "integer"}}
        ]

        result = convert_openapi2_parameters_to_openapi(parameters)
        assert result == expected_output

    def test_convert_openapi2_response_headers_to_openapi(self):
        headers = {"X-Rate-Limit": {"type": "integer", "description": "Calls per hour allowed by the user."}}

        expected_output = {
            "X-Rate-Limit": {"schema": {"type": "integer"}, "description": "Calls per hour allowed by the user."}
        }

        result = convert_openapi2_response_headers_to_openapi(headers)
        assert result == expected_output

    def test_convert_parameters_to_openapi2(self):
        openapi_parameters = [{"name": "id", "in": "query", "schema": {"type": "integer"}, "required": True}]

        expected_output = [{"name": "id", "in": "query", "type": "integer", "required": True}]

        result = convert_parameters_to_openapi2(openapi_parameters)
        assert result == expected_output

    def test_convert_request_body_to_openapi2(self):
        request_body = {
            "content": {"application/json": {"schema": {"type": "object", "properties": {"name": {"type": "string"}}}}}
        }

        expected_output = [
            {
                "in": "body",
                "name": "body",
                "required": False,
                "schema": {"type": "object", "properties": {"name": {"type": "string"}}},
                "consumes": ["application/json"],
            }
        ]

        result = convert_request_body_to_openapi2(request_body)
        assert result == expected_output

    def test_convert_responses_to_openapi2(self):
        responses = {
            "200": {
                "description": "Success",
                "content": {
                    "application/json": {"schema": {"type": "object", "properties": {"message": {"type": "string"}}}}
                },
            }
        }

        expected_output = {
            "200": {
                "description": "Success",
                "schema": {"type": "object", "properties": {"message": {"type": "string"}}},
            }
        }

        result = convert_responses_to_openapi2(responses)
        assert result == expected_output

    @pytest.fixture(autouse=True)
    def mock_convert_functions(self, mocker):
        mocker.patch("apigateway.biz.resource.importer.schema.convert_request_body", return_value=([], []))
        mocker.patch("apigateway.biz.resource.importer.schema.convert_parameters", return_value=[])
        mocker.patch("apigateway.biz.resource.importer.schema.convert_responses", return_value=({}, []))

    def test_convert_operation_v3_to_v2(self):
        v3_operation = {
            "description": "Retrieve a user",
            "summary": "Get User",
            "operationId": "getUser",
            "tags": ["user"],
            "requestBody": {
                "content": {
                    "application/json": {"schema": {"type": "object", "properties": {"id": {"type": "string"}}}}
                }
            },
            "parameters": [{"name": "userId", "in": "path", "required": True, "schema": {"type": "string"}}],
            "responses": {
                "200": {
                    "description": "successful operation",
                    "content": {
                        "application/json": {"schema": {"type": "object", "properties": {"name": {"type": "string"}}}}
                    },
                }
            },
        }

        expected_v2_operation = {
            "description": "Retrieve a user",
            "summary": "Get User",
            "operationId": "getUser",
            "tags": ["user"],
            "parameters": [],
            "consumes": [],
            "responses": {},
            "produces": [],
        }

        result = convert_operation_v3_to_v2(v3_operation)
        assert result == expected_v2_operation
