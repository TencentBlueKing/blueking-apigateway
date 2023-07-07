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

from apigateway.apps.plugin.constants import PluginBindingScopeEnum
from apigateway.apps.plugin.models import PluginBinding


class TestStageConvertor:
    def test_convert_stage(
        self,
        edge_gateway,
        edge_gateway_stage,
        micro_gateway,
        micro_gateway_http_domain,
        micro_gateway_http_path,
        fake_stage_convertor,
    ):
        stage = fake_stage_convertor.convert()
        assert stage.spec.name == edge_gateway_stage.name

        metadata = stage.metadata
        assert 0 < len(metadata.name) <= 64

        assert metadata.get_label("gateway") == edge_gateway.name
        assert metadata.get_label("stage") == edge_gateway_stage.name

        spec = stage.spec
        assert spec.description == edge_gateway_stage.description
        assert spec.vars["stage_name"] == edge_gateway_stage.name
        # assert stage.domain == micro_gateway_http_domain
        assert spec.domain == ""
        assert spec.path_prefix == micro_gateway_http_path
        assert spec.rewrite.enabled
        assert spec.rewrite.headers["X-Set-By-Stage"] == edge_gateway_stage.name
        assert spec.rewrite.headers["X-Del-By-Stage"] == ""

    @pytest.mark.parametrize(
        "name",
        [
            "bk-opentelemetry",
            "prometheus",
            "bk-request-id",
            "file-logger",
            "bk-auth-verify",
            "bk-auth-validate",
            "bk-jwt",
            "bk-delete-sensitive",
            "bk-stage-context",
            "bk-concurrency-limit",
            "bk-permission",
            "bk-debug",
        ],
    )
    def test_default_stage_plugins(self, name, fake_stage_convertor):
        plugin = self.get_stage_plugin_by_name(fake_stage_convertor, name)

        assert plugin is not None
        assert plugin.name == name

    def test_stage_global_rate_limit_plugin(self, edge_gateway_stage_context_stage_rate_limit, fake_stage_convertor):
        # The plugin exists when the configuration is enabled by the fixture.
        plugin = self.get_stage_plugin_by_name(fake_stage_convertor, "bk-stage-global-rate-limit")

        assert plugin is not None
        assert plugin.name == "bk-stage-global-rate-limit"

        stage_rate_config = edge_gateway_stage_context_stage_rate_limit.config
        if "enabled" in stage_rate_config:
            stage_rate_config.pop("enabled")
        assert plugin.config == stage_rate_config

    def test_stage_global_rate_limit_plugin__disabled(
        self, edge_gateway_stage_context_stage_rate_limit, fake_stage_convertor
    ):
        # Set the ".enabled" field of the plugin config to false
        g_rate_context = edge_gateway_stage_context_stage_rate_limit
        config = g_rate_context.config
        config["enabled"] = False
        g_rate_context.config = config
        g_rate_context.save(update_fields=["_config"])

        # The plugin should be removed now
        plugin = self.get_stage_plugin_by_name(fake_stage_convertor, "bk-stage-global-rate-limit")
        assert plugin is None

    def test_stage_rate_limit_plugin(
        self, rate_limit_access_strategy, rate_limit_access_strategy_stage_binding, fake_stage_convertor
    ):
        plugin = self.get_stage_plugin_by_name(fake_stage_convertor, "bk-stage-rate-limit")
        assert plugin is not None
        assert plugin.config == rate_limit_access_strategy.config

    def test_convert_ip_restriction_plugin(
        self,
        ip_group,
        ip_access_control_access_strategy,
        ip_access_control_access_strategy_stage_binding,
        fake_stage_convertor,
    ):
        plugin = self.get_stage_plugin_by_name(
            fake_stage_convertor,
            "bk-ip-restriction",
        )

        assert plugin is not None

        access_strategy_config = ip_access_control_access_strategy.config

        # allow to whitelist: [ip]
        assert access_strategy_config["type"] == "allow"

        groups = plugin.config["whitelist"]
        assert len(groups) == 1

        assert groups[0] == ip_group._ips

    def test_stage_plugin(
        self,
        faker,
        edge_gateway,
        edge_gateway_stage,
        fake_stage_convertor,
        echo_plugin,
    ):
        G(
            PluginBinding,
            api=edge_gateway,
            config=echo_plugin,
            scope_type=PluginBindingScopeEnum.STAGE.value,
            scope_id=edge_gateway_stage.id,
        )

        plugin_config = self.get_stage_plugin_by_name(
            fake_stage_convertor,
            echo_plugin.type.code,
        )

        assert plugin_config is not None

        assert plugin_config.name == echo_plugin.type.code
        assert plugin_config.config == echo_plugin.config

    def get_stage_plugin_by_name(self, convertor, name):
        stage = convertor.convert()
        for plugin in stage.spec.plugins:
            if plugin.name == name:
                return plugin
