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
import pytest

from apigateway.apis.v2.sync.serializers import GatewaySyncInputSLZ, SDKGenerateInputSLZ, StageSyncInputSLZ
from apigateway.core.constants import GatewayKindEnum


def test_gateway_sync_input_maps_ai_kind():
    slz = GatewaySyncInputSLZ(data={"name": "ai-gateway", "kind": "ai"})

    slz.is_valid(raise_exception=True)

    assert slz.validated_data["kind"] == GatewayKindEnum.AI.value


class TestSDKGenerateInputSLZ:
    @pytest.mark.parametrize(
        "version, is_valid",
        [
            ("", True),
            ("1.2.3", True),
            ("1.2.3-beta.1+build.1", True),
            ("v1.2.3", False),
            ("1.2", False),
            ("1.0.0');__import__('os').system('touch /tmp/sdk-version-pwned')#", False),
        ],
    )
    def test_validate_version(self, version, is_valid):
        slz = SDKGenerateInputSLZ(
            data={
                "resource_version": "1.0.0",
                "languages": ["python"],
                "version": version,
            },
        )

        assert slz.is_valid() is is_valid
        if not is_valid:
            assert "version" in slz.errors


class TestStageSyncInputSLZ:
    def test_validate_delegates_plugin_validation_to_stage_sync_handler(self, mocker, fake_gateway):
        mocked_validate = mocker.patch("apigateway.apis.v2.sync.serializers.StageSyncHandler.validate_plugin_configs")

        slz = StageSyncInputSLZ(context={"gateway": fake_gateway})
        slz.validate(
            {
                "gateway": fake_gateway,
                "backends": [
                    {
                        "name": "default",
                        "config": {"hosts": [{"host": "http://example.com", "weight": 100}]},
                    }
                ],
                "plugin_configs": [{"type": "test-plugin", "yaml": "enabled: true"}],
            }
        )

        mocked_validate.assert_called_once_with([{"type": "test-plugin", "yaml": "enabled: true"}])
