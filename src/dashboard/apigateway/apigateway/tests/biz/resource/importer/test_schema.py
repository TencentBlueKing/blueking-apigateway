# -*- coding: utf-8 -*-
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
from apigateway.biz.openapi.schema import (
    SchemaValidateErr,
    convert_openapi2_formdata_to_openapi,
    convert_openapi2_parameters_to_openapi,
    convert_openapi2_response_headers_to_openapi,
)


class TestSchema:
    def test_schema_validate_err_escapes_html(self):
        err = SchemaValidateErr(
            "<img src=x onerror=alert(1)>",
            "$.paths./<img src=x onerror=alert(1)>",
            ["paths", "/<img src=x onerror=alert(1)>"],
        )

        result = err.to_dict()
        assert result["message"] == "&lt;img src=x onerror=alert(1)&gt;"
        assert result["json_path"] == "$.paths./&lt;img src=x onerror=alert(1)&gt;"
        assert result["absolute_path"] == ["paths", "/&lt;img src=x onerror=alert(1)&gt;"]

    def test_convert_openapi2_formdata_to_openapi(self):
        formdata_params = [
            {"name": "file", "type": "file", "required": True},
            {"name": "name", "type": "string", "required": False},
        ]
        consumers = ["application/json"]

        expected_output = {
            "content": {
                "multipart/form-data": {
                    "schema": {
                        "type": "object",
                        "properties": {"file": {"type": "string"}, "name": {"type": "string"}},
                        "required": ["file"],
                    }
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
