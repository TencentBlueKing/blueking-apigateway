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
from jsonschema import validate

from apigateway.apps.plugin.models import Plugin, PluginConfig
from apigateway.controller.crds.release_data.plugin import PluginConvertorFactory
from apigateway.schema.models import Schema
from apigateway.utils.yaml import yaml_dumps


@pytest.fixture()
def legacy_plugin(fake_gateway, echo_plugin, echo_plugin_type):
    return G(
        Plugin,
        api=fake_gateway,
        name=echo_plugin.name,
        type=echo_plugin_type.code,
        _config=json.dumps(echo_plugin.config),
    )


@pytest.fixture()
def related_model_not_exist(legacy_plugin, echo_plugin, echo_plugin_type, echo_plugin_stage_binding):
    echo_plugin_stage_binding.delete()
    echo_plugin.delete()
    echo_plugin_type.delete()
    legacy_plugin.target = None


class TestPluginConfig:
    def test_config_setter(self, fake_plugin_config):
        # no schema
        fake_plugin_config.config = yaml_dumps({"foo": "bar"})
        fake_plugin_config.save()
        assert fake_plugin_config.yaml == "foo: bar\n"
        assert PluginConfig.objects.get(id=fake_plugin_config.id).config == {"foo": "bar"}

        # schema check ok
        fake_plugin_config.type.schema = Schema(
            schema=json.dumps(
                {
                    "type": "object",
                    "properties": {"foo": {"type": "string"}},
                }
            )
        )
        fake_plugin_config.config = yaml_dumps({"foo": "bar2"})
        assert fake_plugin_config.yaml == "foo: bar2\n"

        # schema check error
        with pytest.raises(Exception):
            fake_plugin_config.config = yaml_dumps({"foo": 1})

            convertor = PluginConvertorFactory("")
            _data = convertor.convert(fake_plugin_config)
            validate(_data, schema=fake_plugin_config.type.schema.schema)


class TestPlugin:
    def test_create_without_related_type(self, fake_gateway, related_model_not_exist):
        plugin = G(Plugin, api=fake_gateway)
        assert plugin.target is None

    def test_create_with_related_type(self, clone_model, legacy_plugin, echo_plugin):
        echo_plugin.delete()
        legacy_plugin.delete()

        plugin = clone_model(legacy_plugin, target=None)

        target = plugin.target
        assert target is not None
        assert target.api == plugin.api
        assert target.name == plugin.name
        assert target.config == echo_plugin.config
        assert target.type_id == echo_plugin.type_id

    def test_update_with_related_models(self, faker, legacy_plugin, echo_plugin):
        legacy_plugin.description = faker.pystr()
        legacy_plugin.save()

        echo_plugin.refresh_from_db()
        assert echo_plugin.description == legacy_plugin.description

    def test_rename_with_related_models(self, faker, legacy_plugin, echo_plugin):
        legacy_plugin.name = faker.pystr()
        legacy_plugin.save()

        echo_plugin.refresh_from_db()
        assert echo_plugin.name == legacy_plugin.name

    def test_update_with_related_model_validation(self, faker, legacy_plugin, echo_plugin):

        echo_plugin.refresh_from_db()
        assert echo_plugin.config is not None

        legacy_plugin.refresh_from_db()
        assert legacy_plugin.config is not None

    def test_delete_without_related_models(self, legacy_plugin, related_model_not_exist):
        legacy_plugin.delete()

    def test_delete_with_related_models(self, faker, legacy_plugin, echo_plugin):
        legacy_plugin.delete()
        assert not PluginConfig.objects.filter(pk=echo_plugin.pk).exists()

    def test_update_with_disable_syncing(self, faker, legacy_plugin, echo_plugin):
        legacy_plugin.disable_syncing = True
        legacy_plugin.description = faker.pystr()
        legacy_plugin.save()

        echo_plugin.refresh_from_db()
        assert echo_plugin.description != legacy_plugin.description

    def test_delete_with_disable_syncing(self, faker, legacy_plugin, echo_plugin):
        legacy_plugin.disable_syncing = True
        legacy_plugin.delete()

        echo_plugin.refresh_from_db()


class TestPluginBinding:
    def test_bind_plugin_without_related_models(
        self,
        clone_model,
        legacy_plugin,
        echo_plugin_stage_binding,
        related_model_not_exist,
    ):
        binding = clone_model(echo_plugin_stage_binding, plugin=legacy_plugin, type=legacy_plugin.type, config=None)
        assert binding.config is None

    def test_bind_plugin_with_related_models(
        self,
        clone_model,
        legacy_plugin,
        echo_plugin_stage_binding,
    ):
        binding = clone_model(echo_plugin_stage_binding, plugin=legacy_plugin, type=legacy_plugin.type, config=None)

        assert binding.config is not None

    def test_bind_config_with_related_models(
        self,
        echo_plugin,
        echo_plugin_stage_binding,
    ):
        assert echo_plugin_stage_binding.config == echo_plugin
        assert echo_plugin_stage_binding.type is None
        assert echo_plugin_stage_binding.plugin is None

    def test_bind_plugin_with_disable_syncing(
        self,
        clone_model,
        legacy_plugin,
        echo_plugin_stage_binding,
    ):
        legacy_plugin.disable_syncing = True
        binding = clone_model(echo_plugin_stage_binding, plugin=legacy_plugin, type=legacy_plugin.type, config=None)

        assert binding.config is None

    def test_delete_plugin_with_disable_syncing(
        self,
        clone_model,
        legacy_plugin,
        echo_plugin_stage_binding,
    ):
        binding = clone_model(echo_plugin_stage_binding, plugin=legacy_plugin, type=legacy_plugin.type, config=None)

        legacy_plugin.disable_syncing = True
        legacy_plugin.delete()

        binding.refresh_from_db()

        assert binding.config is not None
        assert binding.plugin is None

    def test_get_config_with_plugin_config(self, echo_plugin, echo_plugin_stage_binding):
        assert echo_plugin_stage_binding.get_config() == echo_plugin.config
        assert echo_plugin_stage_binding.get_type() == echo_plugin.type.code

    def test_get_config_without_plugin_config(self, legacy_plugin, echo_plugin_stage_binding, related_model_not_exist):
        assert echo_plugin_stage_binding.get_config() == legacy_plugin.config
        assert echo_plugin_stage_binding.get_type() == legacy_plugin.type
