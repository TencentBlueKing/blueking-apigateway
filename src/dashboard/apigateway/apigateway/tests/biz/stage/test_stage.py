# -*- coding: utf-8 -*-
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
from django_dynamic_fixture import G
from rest_framework import serializers

from apigateway.apps.plugin.constants import PluginBindingScopeEnum
from apigateway.biz.stage import StageHandler, StageSyncHandler
from apigateway.core.models import Gateway


class TestStageHandler:
    @pytest.fixture(autouse=True)
    def setup_fixtures(self):
        self.gateway = G(Gateway)

    @pytest.mark.parametrize(
        "stage_names, expected, will_error",
        [
            ([], [1, 2], False),
            (["prod"], [1], False),
            (["stag"], None, True),
        ],
    )
    def test_get_stage_ids(self, mocker, fake_request, fake_gateway, stage_names, expected, will_error):
        mocker.patch(
            "apigateway.biz.stage.stage.Stage.objects.get_name_id_map",
            return_value={"prod": 1, "test": 2},
        )

        if will_error:
            with pytest.raises(Exception):
                StageHandler.get_stage_ids(fake_gateway, stage_names)
            return

        result = StageHandler.get_stage_ids(fake_gateway, stage_names)
        assert expected == sorted(result)


def test_stage_sync_preserves_backend_health_checks():
    config = StageSyncHandler.build_backend_config(
        {
            "name": "default",
            "config": {
                "type": "node",
                "timeout": 30,
                "loadbalance": "roundrobin",
                "hosts": [{"host": "http://example.com", "weight": 100}],
                "checks": {"active": {"http_path": "/healthz"}},
            },
        }
    )

    assert config["checks"] == {"active": {"http_path": "/healthz"}}


def test_build_legacy_backend_config():
    config = StageSyncHandler.build_legacy_backend_config(
        {
            "timeout": 30,
            "upstreams": {
                "loadbalance": "roundrobin",
                "hosts": [{"host": "http://example.com", "weight": 100}],
            },
        }
    )

    assert config == {
        "type": "node",
        "timeout": 30,
        "loadbalance": "roundrobin",
        "hosts": [{"scheme": "http", "host": "example.com", "weight": 100}],
    }


def test_build_backend_config_with_chash_and_checks():
    config = StageSyncHandler.build_backend_config(
        {
            "name": "default",
            "config": {
                "timeout": 30,
                "loadbalance": "chash",
                "hash_on": "header",
                "key": "x-bkapi-user-id",
                "hosts": [{"host": "https://example.com", "weight": 100}],
                "checks": {"active": {"http_path": "/healthz"}},
            },
        }
    )

    assert config["hash_on"] == "header"
    assert config["key"] == "x-bkapi-user-id"
    assert config["checks"] == {"active": {"http_path": "/healthz"}}


def test_validate_stage_plugin_configs_rejects_duplicate_types():
    with pytest.raises(serializers.ValidationError, match="插件类型重复"):
        StageSyncHandler.validate_plugin_configs(
            [
                {"type": "bk-test", "yaml": "enabled: true"},
                {"type": "bk-test", "yaml": "enabled: false"},
            ]
        )


def test_validate_stage_plugin_configs_rejects_not_exist_types(mocker):
    mock_queryset = mocker.MagicMock()
    mock_queryset.values_list.return_value = []
    mock_queryset.__iter__.return_value = iter([])
    mocker.patch("apigateway.biz.stage.sync.PluginType.objects.all", return_value=mock_queryset)

    with pytest.raises(serializers.ValidationError, match="不存在"):
        StageSyncHandler.validate_plugin_configs([{"type": "bk-test", "yaml": "enabled: true"}])


def test_validate_stage_plugin_configs_raises_on_yaml_error(mocker):
    fake_plugin_type = mocker.MagicMock()
    fake_plugin_type.code = "bk-test"
    fake_plugin_type.schema = None

    mock_queryset = mocker.MagicMock()
    mock_queryset.values_list.return_value = ["bk-test"]
    mock_queryset.__iter__.return_value = iter([fake_plugin_type])
    mocker.patch("apigateway.biz.stage.sync.PluginType.objects.all", return_value=mock_queryset)

    mocker.patch(
        "apigateway.biz.stage.sync.PluginConfigYamlValidator.validate",
        side_effect=Exception("invalid yaml"),
    )

    with pytest.raises(serializers.ValidationError, match="插件配置校验失败"):
        StageSyncHandler.validate_plugin_configs([{"type": "bk-test", "yaml": "enabled: true"}])


def test_sync_stage_plugin_configs_clears_when_plugin_configs_none(mocker):
    mocked_sync = mocker.patch("apigateway.biz.stage.sync.PluginSynchronizer.sync")

    StageSyncHandler.sync_plugin_configs(gateway_id=1, stage_id=2, plugin_configs=None)

    mocked_sync.assert_called_once()
    kwargs = mocked_sync.call_args.kwargs
    assert kwargs["gateway_id"] == 1
    assert kwargs["scope_type"] == PluginBindingScopeEnum.STAGE
    assert kwargs["scope_id_to_plugin_configs"] == {2: []}
