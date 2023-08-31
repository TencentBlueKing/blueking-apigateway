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
            gateway=edge_gateway,
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
