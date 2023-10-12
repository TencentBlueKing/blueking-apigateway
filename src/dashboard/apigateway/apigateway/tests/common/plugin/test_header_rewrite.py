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

from apigateway.apps.plugin.models import PluginBinding, PluginConfig
from apigateway.common.plugin.header_rewrite import HeaderRewriteConvertor


class TestHeaderRewriteConvertor:
    @pytest.mark.parametrize(
        "transform_headers, expected",
        [
            (None, None),
            ({"set": {}, "delete": []}, None),
            (
                {"set": {"key1": "value1"}, "delete": ["key2"]},
                {"set": [{"key": "key1", "value": "value1"}], "remove": [{"key": "key2"}]},
            ),
        ],
    )
    def test_transform_headers_to_plugin_config(self, transform_headers, expected):
        assert HeaderRewriteConvertor.transform_headers_to_plugin_config(transform_headers) == expected

    def test_sync_plugins(self, fake_gateway, fake_resource, fake_plugin_type_bk_header_rewrite):
        HeaderRewriteConvertor.sync_plugins(fake_gateway.id, "resource", {}, "admin")
        assert not PluginConfig.objects.filter(gateway=fake_gateway).exists()
        assert not PluginBinding.objects.filter(gateway=fake_gateway).exists()

        # add
        scope_id_to_plugin_config = {
            fake_resource.id: {
                "set": [{"key": "x-token", "value": "test"}],
                "remove": [{"key": "x-token"}],
            }
        }
        HeaderRewriteConvertor.sync_plugins(fake_gateway.id, "resource", scope_id_to_plugin_config, "admin")

        plugin_config = PluginConfig.objects.get(gateway=fake_gateway, type__code="bk-header-rewrite")
        assert plugin_config.config == {"set": [{"key": "x-token", "value": "test"}], "remove": [{"key": "x-token"}]}
        assert PluginBinding.objects.filter(
            gateway=fake_gateway, scope_type="resource", scope_id=fake_resource.id
        ).exists()

        # update
        scope_id_to_plugin_config = {
            fake_resource.id: {
                "set": [{"key": "x-foo", "value": "test"}],
                "remove": [{"key": "x-bar"}],
            }
        }
        HeaderRewriteConvertor.sync_plugins(fake_gateway.id, "resource", scope_id_to_plugin_config, "admin")

        plugin_config = PluginConfig.objects.get(gateway=fake_gateway, type__code="bk-header-rewrite")
        assert plugin_config.config == {"set": [{"key": "x-foo", "value": "test"}], "remove": [{"key": "x-bar"}]}
        assert PluginBinding.objects.filter(
            gateway=fake_gateway, scope_type="resource", scope_id=fake_resource.id
        ).exists()

        # delete
        scope_id_to_plugin_config = {fake_resource.id: None}
        HeaderRewriteConvertor.sync_plugins(fake_gateway.id, "resource", scope_id_to_plugin_config, "admin")

        assert not PluginConfig.objects.filter(gateway=fake_gateway).exists()
        assert not PluginBinding.objects.filter(gateway=fake_gateway).exists()
