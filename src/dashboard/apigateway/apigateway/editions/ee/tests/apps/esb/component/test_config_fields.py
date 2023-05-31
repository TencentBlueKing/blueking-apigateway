# -*- coding: utf-8 -*-
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

from apigateway.apps.esb.component.config_fields import ConfigField, FieldTypeEnum, enrich_config_fields


class TestFieldTypeEnum:
    def test(self):
        assert FieldTypeEnum.string == "string"
        assert FieldTypeEnum.boolean == "boolean"
        assert FieldTypeEnum.int == "int"
        assert FieldTypeEnum.enum == "enum"
        assert FieldTypeEnum.password == "password"


class TestConfigField:
    @pytest.mark.parametrize(
        "data, expected",
        [
            (
                {
                    "variable": "name",
                    "label": "test",
                },
                {
                    "variable": "name",
                    "label": "test",
                    "type": "string",
                    "default": "",
                },
            ),
            (
                {
                    "variable": "name",
                    "label": "test",
                    "type": "password",
                    "default": "test",
                    "options": [("a", "a")],
                    "show_if": "name=test",
                },
                {
                    "variable": "name",
                    "label": "test",
                    "type": "password",
                    "default": "test",
                    "options": [("a", "a")],
                    "show_if": "name=test",
                },
            ),
        ],
    )
    def test(self, data, expected):
        result = ConfigField(**data).dict(exclude_none=True)
        assert result == expected


@pytest.mark.parametrize(
    "config_fields, config, expected",
    [
        (
            [
                {
                    "variable": "name",
                }
            ],
            {},
            [
                {
                    "variable": "name",
                    "label": "name",
                    "type": "string",
                    "default": "",
                }
            ],
        ),
        (
            [
                {
                    "variable": "name",
                    "default": "test",
                    "type": "password",
                }
            ],
            {
                "name": "new-test",
            },
            [
                {
                    "variable": "name",
                    "label": "name",
                    "default": "new-test",
                    "type": "password",
                }
            ],
        ),
    ],
)
def test_enrich_config_fields(config_fields, config, expected):
    result = enrich_config_fields(config_fields, config)
    assert result == expected
