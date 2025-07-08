#
# TencentBlueKing is pleased to support the open source community by making
# 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
# Copyright (C) 2025 Tencent. All rights reserved.
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

from apigateway.service.plugin.normalizer import format_fault_injection_config, format_response_rewrite_config


@pytest.mark.parametrize(
    "config, expected",
    [
        ({"abort": {"body": "", "vars": ""}, "delay": {"vars": ""}}, {}),
        (
            {"abort": {"body": "some body", "vars": ""}, "delay": {"vars": "some vars"}},
            {"abort": {"body": "some body"}, "delay": {"vars": "some vars"}},
        ),
    ],
)
def test_format_fault_injection_config(config, expected):
    assert format_fault_injection_config(config) == expected


@pytest.mark.parametrize(
    "config, expected",
    [
        ({"body": "", "vars": "", "headers": {"add": [], "set": [], "remove": []}}, {"headers": {}}),
        (
            {
                "body": "test",
                "vars": "test",
                "headers": {
                    "add": [{"key": "name1", "value": "value1"}],
                    "set": [{"key": "key1", "value": "value1"}],
                    "remove": [{"key": "key2"}],
                },
            },
            {
                "body": "test",
                "vars": "test",
                "headers": {
                    "add": [{"key": "name1", "value": "value1"}],
                    "set": [{"key": "key1", "value": "value1"}],
                    "remove": [{"key": "key2"}],
                },
            },
        ),
    ],
)
def test_format_response_rewrite_config(config, expected):
    assert format_response_rewrite_config(config) == expected
