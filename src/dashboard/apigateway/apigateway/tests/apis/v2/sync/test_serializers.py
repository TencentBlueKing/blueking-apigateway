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

from apigateway.apis.v2.sync.serializers import (
    AIBackendConfigSLZ,
    AIBackendSLZ,
    GatewaySyncInputSLZ,
    SDKGenerateInputSLZ,
    StageSyncInputSLZ,
)
from apigateway.core.constants import GatewayKindEnum, GatewayTypeEnum


def _custom_instance(name):
    return {
        "name": name,
        "provider": "openai-compatible",
        "auth": {"header": {"X-Api-Key": "secret", "X-Tenant": "tenant"}},
        "override": {"endpoint": "https://llm.example.com/v1/chat/completions"},
    }


def test_ai_backend_config_rejects_non_mapping_instance():
    slz = AIBackendConfigSLZ(data={"instances": [[{}]]})

    assert not slz.is_valid()
    assert "instances" in slz.errors


def test_automation_defaults_weight_and_accepts_multiple_headers():
    slz = AIBackendConfigSLZ(data={"instances": [_custom_instance("primary")]})

    slz.is_valid(raise_exception=True)

    assert slz.validated_data["timeout"] == 300
    assert slz.validated_data["instances"][0]["weight"] == 0
    assert slz.validated_data["instances"][0]["auth"]["header"]["X-Tenant"] == "tenant"
    assert "options" not in slz.validated_data["instances"][0]


def test_automation_rejects_multiple_instances_in_first_phase():
    slz = AIBackendConfigSLZ(data={"instances": [_custom_instance("primary"), _custom_instance("fallback")]})

    assert not slz.is_valid()
    assert "instances" in slz.errors


def test_ai_backend_ignores_unknown_outer_field():
    slz = AIBackendSLZ(
        data={
            "name": "openai-primary",
            "config": {
                "instances": [
                    {
                        "name": "primary",
                        "provider": "openai",
                        "weight": 1,
                        "auth": {"header": {"Authorization": "Bearer secret"}},
                        "options": {"model": "gpt-4o"},
                    }
                ]
            },
            "unknown": True,
        }
    )

    slz.is_valid(raise_exception=True)

    assert "unknown" not in slz.validated_data


def test_gateway_sync_input_maps_ai_kind():
    slz = GatewaySyncInputSLZ(data={"name": "bkai-gateway", "kind": "ai"})

    slz.is_valid(raise_exception=True)

    assert slz.validated_data["kind"] == GatewayKindEnum.AI.value


class TestGatewaySyncInputSLZ:
    @pytest.mark.parametrize(
        ("data", "is_valid"),
        [
            ({"name": "bkai-gateway", "kind": "ai"}, True),
            ({"name": "bkaidev", "kind": "ai"}, True),
            ({"name": "bkaidev-demo", "kind": "ai"}, True),
            ({"name": "bkaidevx", "kind": "ai"}, False),
            ({"name": "bkaidevfoo", "kind": "ai"}, False),
            ({"name": "gateway", "kind": "ai"}, False),
            ({"name": "bkai-gateway", "kind": "normal"}, False),
            ({"name": "bkaidev", "kind": "normal"}, True),
            ({"name": "bkai-official", "kind": "ai", "api_type": 1}, True),
            ({"name": "bkaidev", "kind": "ai", "api_type": 1}, True),
        ],
    )
    def test_validate_gateway_name_kind_when_creating(self, data, is_valid):
        slz = GatewaySyncInputSLZ(data=data)

        assert slz.is_valid() is is_valid

    def test_update_legacy_ai_gateway_skips_create_name_validation(self, fake_gateway):
        fake_gateway.name = "legacy-ai-gateway"
        fake_gateway.kind = GatewayKindEnum.AI.value
        fake_gateway.save()
        slz = GatewaySyncInputSLZ(
            fake_gateway,
            data={"name": fake_gateway.name, "kind": "ai", "api_type": 1},
        )

        slz.is_valid(raise_exception=True)

    def test_validate_name_allows_whitelisted_official_gateway(self, settings):
        settings.IGNORE_GATEWAY_NAME_CHECK_WHITELIST = ["paasv3"]
        settings.OFFICIAL_GATEWAY_NAME_PREFIXES = ["bk-"]

        slz = GatewaySyncInputSLZ()

        slz._validate_name("paasv3", GatewayTypeEnum.OFFICIAL_API.value)


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
