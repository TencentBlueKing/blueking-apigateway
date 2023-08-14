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
from jsonschema import validate

from apigateway.apps.plugin.models import PluginConfig
from apigateway.controller.crds.release_data.plugin import PluginConvertorFactory
from apigateway.schema.models import Schema
from apigateway.utils.yaml import yaml_dumps


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


class TestPluginBinding:
    def test_get_config_with_plugin_config(self, echo_plugin, echo_plugin_stage_binding):
        assert echo_plugin_stage_binding.get_config() == echo_plugin.config
        assert echo_plugin_stage_binding.get_type() == echo_plugin.type.code
