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
import json

import pytest
from ddf import G
from django.core.management.base import CommandError

from apigateway.apps.plugin.management.commands.migrate_plugin_models import Command
from apigateway.apps.plugin.models import Plugin, PluginBinding, PluginConfig
from apigateway.utils.yaml import yaml_dumps


class TestCommand:
    @pytest.fixture(autouse=True)
    def test_setup(self, echo_plugin_type):
        pass

    def test_sync_models(self, fake_gateway):
        plugin = G(
            Plugin,
            api=fake_gateway,
            type="echo",
            _config=json.dumps({"foo": "bar", "list": [1, 2], "body": "hi"}),
            target=None,
        )
        G(PluginBinding, api=fake_gateway, plugin=plugin, config=None)
        G(PluginBinding, api=fake_gateway, plugin=plugin, config=None)

        command = Command()
        command._sync_models(plugin, False)

        plugin.refresh_from_db()
        plugin_config = PluginConfig.objects.filter(api=fake_gateway).first()
        assert plugin.target == plugin_config
        assert plugin_config.config == {"foo": "bar", "list": [1, 2], "body": "hi"}
        assert PluginBinding.objects.filter(api=fake_gateway, plugin=plugin, config=plugin_config).count() == 2

    def test_sync_legacy_plugin_to_plugin_config(self, fake_gateway):
        plugin = G(
            Plugin,
            api=fake_gateway,
            type="echo",
            _config=json.dumps({"foo": "bar", "list": [1, 2], "dict": {"a": "b"}, "body": "hi"}),
            target=None,
        )

        command = Command()
        plugin_config = command._sync_legacy_plugin_to_plugin_config(plugin)
        assert "[迁移]" in plugin_config.name
        assert plugin_config.type.code == "echo"
        assert plugin_config.config == {"foo": "bar", "list": [1, 2], "dict": {"a": "b"}, "body": "hi"}
        plugin.refresh_from_db()
        assert plugin.target == plugin_config

        plugin_config2 = command._sync_legacy_plugin_to_plugin_config(plugin)
        assert plugin_config2 == plugin_config

        plugin_config.config = yaml_dumps({"foo": "bar", "body": "hi"})
        plugin_config.save(update_fields=["yaml"])
        plugin.refresh_from_db()
        with pytest.raises(CommandError):
            command._sync_legacy_plugin_to_plugin_config(plugin)

    def test_update_binding_to_plugin_config(self, fake_gateway):
        plugin = G(Plugin, api=fake_gateway)
        binding = G(PluginBinding, api=fake_gateway, plugin=plugin, config=None)
        plugin_config = G(PluginConfig, api=fake_gateway)

        command = Command()
        command._update_binding_to_plugin_config(binding, plugin_config)
        binding.refresh_from_db()
        assert binding.plugin == plugin
        assert binding.config == plugin_config

        command._update_binding_to_plugin_config(binding, plugin_config)
        binding.refresh_from_db()
        assert binding.plugin == plugin
        assert binding.config == plugin_config

        plugin_config2 = G(PluginConfig, api=fake_gateway)
        with pytest.raises(CommandError):
            command._update_binding_to_plugin_config(binding, plugin_config2)

    def test_delete_legacy_models(self, fake_gateway):
        plugin = G(
            Plugin,
            api=fake_gateway,
            type="echo",
            _config=json.dumps({"foo": "bar", "body": "hi"}),
        )
        binding = G(PluginBinding, api=fake_gateway, plugin=plugin, config=None)

        command = Command()
        command._sync_models(plugin, False)

        assert PluginBinding.objects.filter(api=fake_gateway, plugin=plugin).count() == 1
        command._delete_legacy_models(plugin, False)
        assert PluginBinding.objects.filter(api=fake_gateway, plugin=None).count() == 1

    def test_validate_plugin_config(self, echo_plugin):
        command = Command()

        command._validate_plugin_config(echo_plugin)

        echo_plugin.config = yaml_dumps({"foo": "bar"})
        with pytest.raises(CommandError):
            command._validate_plugin_config(echo_plugin)

        # no plugin_type
        plugin_config = G(PluginConfig, type=None)
        command._validate_plugin_config(plugin_config)
