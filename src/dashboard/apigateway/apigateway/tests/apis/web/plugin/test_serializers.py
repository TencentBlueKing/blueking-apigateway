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
from pathlib import Path

import pytest
from ddf import G
from django.conf import settings
from django.utils import translation
from rest_framework.exceptions import ValidationError

from apigateway.apis.web.plugin.serializers import (
    PluginConfigCreateInputSLZ,
    PluginConfigRetrieveUpdateInputSLZ,
    PluginTypeOutputSLZ,
)
from apigateway.apps.plugin.constants import PluginTypeCodeEnum
from apigateway.apps.plugin.models import PluginType
from apigateway.utils.yaml import yaml_dumps, yaml_loads

pytestmark = pytest.mark.django_db


class TestPluginTypeOutputSLZ:
    @pytest.mark.parametrize(
        ("language", "name", "prerequisite"),
        [
            (
                "zh-cn",
                "应用频率控制",
                "前置条件：资源需要开启应用认证；绑定在环境上时，请确保需要限流的资源已开启应用认证。",
            ),
            (
                "en",
                "Application Rate Limit",
                "Prerequisite: resources must have application authentication enabled. "
                "When bound to a stage, ensure that resources requiring rate limiting have "
                "application authentication enabled.",
            ),
        ],
    )
    def test_rate_limit_fixture_display(self, language, name, prerequisite):
        fixture_path = Path(settings.BASE_DIR) / "fixtures/plugins.yaml"
        records = yaml_loads(fixture_path.read_text(encoding="utf-8"))
        fields = next(
            record["fields"]
            for record in records
            if record["model"] == "plugin.plugintype" and record["fields"]["code"] == "bk-rate-limit"
        )
        plugin_type = PluginType(**{**fields, "schema": None})

        with translation.override(language):
            result = PluginTypeOutputSLZ(plugin_type).data
            assert str(PluginTypeCodeEnum.get_choice_label("bk-rate-limit")) == name

        assert result["code"] == "bk-rate-limit"
        assert result["name"] == name
        assert result["description"].splitlines()[0] == prerequisite
        assert result["notes"] == result["description"]
        if language == "en":
            assert result["description"].splitlines()[1].startswith("Rate limit")


class TestPluginConfigCreateInputSLZ:
    def test_create_with_private_plugin_error(self, fake_gateway, faker):
        plugin_type = G(PluginType, is_public=False, schema=None)

        params = {
            "gateway": fake_gateway,
            "type_id": plugin_type.id,
            "name": faker.pystr(),
            "description": faker.pystr(),
            "yaml": "{}",
        }
        slz = PluginConfigCreateInputSLZ(data=params, context={"gateway": fake_gateway})
        slz.is_valid(raise_exception=True)

        with pytest.raises(ValidationError):
            slz.save()


class TestPluginConfigRetrieveUpdateInputSLZ:
    def test_update_with_plugin_type_change_error(self, fake_gateway, faker, fake_plugin_config):
        new_plugin_type = G(PluginType, schema=None)

        params = {
            "gateway": fake_gateway,
            "type_id": new_plugin_type.id,
            "name": "name",
            "description": "description",
            "yaml": "{}",
        }
        slz = PluginConfigRetrieveUpdateInputSLZ(
            data=params, instance=fake_plugin_config, context={"gateway": fake_gateway}
        )
        slz.is_valid(raise_exception=True)

        with pytest.raises(ValidationError):
            slz.save()

    def test_update_plugin__error(self, fake_gateway, faker, fake_plugin_config):
        fake_plugin_config.type.code = "bk-cors"

        params = {
            "gateway": fake_gateway,
            "name": "name",
            "description": "description",
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

        slz = PluginConfigRetrieveUpdateInputSLZ()
        with pytest.raises(ValidationError):
            slz._update_plugin(fake_plugin_config, params)
