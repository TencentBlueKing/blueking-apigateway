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

from apigateway.legacy_esb.management.commands.export_buffet_to_resources import Command


class TestCommand:
    @pytest.mark.parametrize(
        "resources, expected",
        [
            (
                [
                    {"name": "test"},
                    {"name": "hello"},
                ],
                [
                    {"name": "test"},
                    {"name": "hello"},
                ],
            ),
            (
                [
                    {"name": "test"},
                    {"name": "hello"},
                    {"name": "hello"},
                ],
                [
                    {"name": "test"},
                    {"name": "hello"},
                    {"name": "hello_2"},
                ],
            ),
            (
                [
                    {"name": "test"},
                    {"name": "hello"},
                    {"name": "test"},
                    {"name": "hello"},
                    {"name": "hello"},
                ],
                [
                    {"name": "test"},
                    {"name": "hello"},
                    {"name": "test_2"},
                    {"name": "hello_2"},
                    {"name": "hello_3"},
                ],
            ),
        ],
    )
    def test_rename_duplicate_name(self, resources, expected):
        command = Command()
        assert command._rename_duplicate_names(resources) == expected
