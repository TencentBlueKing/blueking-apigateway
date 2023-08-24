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
from ddf import G
from rest_framework.exceptions import ValidationError

from apigateway.apps.plugin.models import PluginType
from apigateway.apps.plugin.plugin.serializers import PluginConfigSLZ
from apigateway.utils.yaml import yaml_dumps

pytestmark = pytest.mark.django_db


class TestPluginConfigSLZ:
    def test_create_with_private_plugin_error(self, fake_gateway, faker):
        plugin_type = G(PluginType, is_public=False, schema=None)

        params = {
            "api": fake_gateway,
            "type_id": plugin_type.id,
            "name": faker.pystr(),
            "description": faker.pystr(),
            "yaml": "{}",
        }
        slz = PluginConfigSLZ(data=params, context={"gateway": fake_gateway})
        slz.is_valid(raise_exception=True)

        with pytest.raises(ValidationError):
            slz.save()

    def test_update_with_plugin_type_change_error(self, fake_gateway, faker, fake_plugin_config):
        new_plugin_type = G(PluginType, schema=None)

        params = {
            "api": fake_gateway,
            "type_id": new_plugin_type.id,
            "name": faker.pystr(),
            "description": faker.pystr(),
            "yaml": "{}",
        }
        slz = PluginConfigSLZ(data=params, instance=fake_plugin_config, context={"gateway": fake_gateway})
        slz.is_valid(raise_exception=True)

        with pytest.raises(ValidationError):
            slz.save()

    def test_update_plugin__error(self, fake_gateway, faker, fake_plugin_config):
        fake_plugin_config.type.code = "bk-cors"

        params = {
            "api": fake_gateway,
            "name": faker.pystr(),
            "description": faker.pystr(),
            "yaml": yaml_dumps(
                {
                    "allow_origins": "*",
                    "allow_methods": "*",
                    "allow_headers": "*",
                    "expose_headers": "",
                    "max_age": 100,
                    "allow_credential": True,
                }
            ),
        }

        slz = PluginConfigSLZ()
        with pytest.raises(ValidationError):
            slz._update_plugin(fake_plugin_config, params)
