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
