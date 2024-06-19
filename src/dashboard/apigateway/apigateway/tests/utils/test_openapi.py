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
