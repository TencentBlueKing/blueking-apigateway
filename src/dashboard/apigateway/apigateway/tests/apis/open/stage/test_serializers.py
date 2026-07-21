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

from apigateway.apis.open.stage import serializers


def _custom_instance(name):
    return {
        "name": name,
        "provider": "openai-compatible",
        "auth": {"header": {"X-Api-Key": "secret", "X-Tenant": "tenant"}},
        "override": {"endpoint": "https://llm.example.com/v1/chat/completions"},
    }


def test_ai_backend_config_rejects_non_mapping_instance():
    slz = serializers.AIBackendConfigSLZ(data={"instances": [[{}]]})

    assert not slz.is_valid()
    assert "instances" in slz.errors


def test_automation_defaults_weight_and_accepts_multiple_headers():
    slz = serializers.AIBackendConfigSLZ(data={"instances": [_custom_instance("primary")]})

    slz.is_valid(raise_exception=True)

    assert slz.validated_data["timeout"] == 300
    assert slz.validated_data["instances"][0]["weight"] == 0
    assert slz.validated_data["instances"][0]["auth"]["header"]["X-Tenant"] == "tenant"
    assert "options" not in slz.validated_data["instances"][0]


def test_automation_rejects_multiple_instances_in_first_phase():
    slz = serializers.AIBackendConfigSLZ(
        data={"instances": [_custom_instance("primary"), _custom_instance("fallback")]}
    )

    assert not slz.is_valid()
    assert "instances" in slz.errors


def test_ai_backend_ignores_unknown_outer_field():
    slz = serializers.AIBackendSLZ(
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


class TestStageWithResourceVersionV1SLZ:
    @pytest.mark.parametrize(
        "stage_name, stage_release, expected",
        [
            (
                "prod",
                {},
                [
                    {
                        "name": "prod",
                        "resource_version": None,
                        "released": False,
                    }
                ],
            ),
            (
                "test",
                {
                    "resource_version": {
                        "title": "test",
                        "version": "1.0.1",
                    },
                },
                [
                    {
                        "name": "test",
                        "resource_version": {
                            "version": "1.0.1",
                        },
                        "released": True,
                    }
                ],
            ),
        ],
    )
    def test_to_representation(self, fake_stage, stage_name, stage_release, expected):
        fake_stage.name = stage_name
        slz = serializers.StageWithResourceVersionV1SLZ(
            [fake_stage],
            many=True,
            context={
                "stage_release": {
                    fake_stage.id: stage_release,
                }
            },
        )
        assert slz.data == expected


class TestCheckSLZ:
    def test_active_with_passive_valid(self):
        data = {
            "active": {
                "type": "http",
                "timeout": 5,
                "http_path": "/health",
                "healthy": {"interval": 10, "successes": 2, "http_statuses": [200, 201]},
            },
            "passive": {
                "type": "http",
                "healthy": {"successes": 2, "http_statuses": [200]},
                "unhealthy": {"http_failures": 3, "tcp_failures": 2, "http_statuses": [500, 502]},
            },
        }
        slz = serializers.CheckSLZ(data=data)
        assert slz.is_valid()

    def test_passive_only_invalid(self):
        data = {"passive": {"type": "http", "unhealthy": {"http_failures": 3}}}
        slz = serializers.CheckSLZ(data=data)
        assert not slz.is_valid()
        assert "active" in slz.errors

    def test_null_active_with_passive_invalid(self):
        data = {
            "active": None,
            "passive": {"type": "http", "unhealthy": {"http_failures": 3}},
        }
        slz = serializers.CheckSLZ(data=data)
        assert not slz.is_valid()
        assert "active" in slz.errors


class TestStageSLZ:
    def test_validate_delegates_plugin_validation_to_stage_sync_handler(self, mocker, fake_gateway):
        mocked_validate = mocker.patch(
            "apigateway.apis.open.stage.serializers.StageSyncHandler.validate_plugin_configs"
        )

        slz = serializers.StageSLZ(context={"gateway": fake_gateway})
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
