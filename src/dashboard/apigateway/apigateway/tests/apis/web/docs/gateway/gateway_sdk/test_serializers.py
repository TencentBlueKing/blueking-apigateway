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

from apigateway.apis.web.docs.gateway.gateway_sdk.serializers import StageSDKOutputSLZ


class TestStageSDKOutputSLZ:
    @pytest.mark.parametrize(
        "data, expected",
        [
            (
                {
                    "stage": {
                        "id": 1,
                        "name": "prod",
                    },
                    "resource_version": {
                        "id": 2,
                        "version": "1.0.0",
                    },
                    "sdk": {
                        "language": "python",
                        "version": "1.0.0",
                        "url": "http://example.com",
                        "name": "foo",
                        "install_command": "install command",
                    },
                },
                {
                    "stage": {
                        "id": 1,
                        "name": "prod",
                    },
                    "resource_version": {
                        "id": 2,
                        "version": "1.0.0",
                    },
                    "sdk": {
                        "version": "1.0.0",
                        "url": "http://example.com",
                        "name": "foo",
                        "install_command": "install command",
                    },
                },
            ),
            (
                {
                    "stage": {
                        "id": 1,
                        "name": "prod",
                    },
                    "resource_version": {
                        "id": 2,
                        "version": "1.0.0",
                    },
                    "sdk": None,
                },
                {
                    "stage": {
                        "id": 1,
                        "name": "prod",
                    },
                    "resource_version": {
                        "id": 2,
                        "version": "1.0.0",
                    },
                    "sdk": None,
                },
            ),
        ],
    )
    def test_to_representation(self, data, expected):
        slz = StageSDKOutputSLZ(data)
        assert slz.data == expected
