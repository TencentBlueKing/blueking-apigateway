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
from ddf import G

from apigateway.apps.plugin.constants import PluginBindingScopeEnum
from apigateway.apps.plugin.models import PluginBinding
from apigateway.controller.crds.constants import ResourceRewriteHeadersStrategyEnum
from apigateway.controller.crds.v1beta1.models.gateway_resource import BkGatewayResource


class TestHttpResourceConvertor:
    def test_convert(self):
        pass

    def get_resource_plugin_by_name(self, fake_http_resource_convertor, resource, name):
        plugins = fake_http_resource_convertor._convert_http_resource_plugins(resource)
        for plugin in plugins:
            if plugin.name == name:
                return plugin
        return None

    def test_convert_http_resource_plugin_bk_resource_context(
        self, edge_resource_inherit_stage_snapshot, fake_http_resource_convertor
    ):
        plugin = self.get_resource_plugin_by_name(
            fake_http_resource_convertor, edge_resource_inherit_stage_snapshot, "bk-resource-context"
        )

        assert plugin is not None
        assert plugin.config["bk_resource_id"] == edge_resource_inherit_stage_snapshot["id"]
        assert plugin.config["bk_resource_name"] == edge_resource_inherit_stage_snapshot["name"]

    def test_convert_http_resource_plugin(
        self,
        faker,
        edge_gateway,
        edge_gateway_stage,
        edge_resource_inherit_stage,
        edge_resource_inherit_stage_snapshot,
        fake_http_resource_convertor,
        echo_plugin,
    ):
        G(
            PluginBinding,
            gateway=edge_gateway,
            config=echo_plugin,
            scope_type=PluginBindingScopeEnum.RESOURCE.value,
            scope_id=edge_resource_inherit_stage.id,
        )

        plugin_config = self.get_resource_plugin_by_name(
            fake_http_resource_convertor,
            edge_resource_inherit_stage_snapshot,
            echo_plugin.type.code,
        )

        assert plugin_config is not None

        assert plugin_config.name == echo_plugin.type.code
        assert plugin_config.config == echo_plugin.config

    def test_convert_http_resources_with_edge_resource_inherit_stage(
        self,
        edge_gateway,
        edge_gateway_stage,
        edge_gateway_stage_context_proxy_http,
        edge_resource_inherit_stage,
        edge_resource_inherit_stage_proxy,
        fake_http_resource_convertor,
    ):
        resource = None

        for r in fake_http_resource_convertor.convert():
            if r.spec.name == edge_resource_inherit_stage.name:
                resource = r
                break

        assert resource is not None
        assert isinstance(resource, BkGatewayResource)

        metadata = resource.metadata
        assert 0 < len(metadata.name) <= 64

        assert metadata.get_label("gateway") == edge_gateway.name
        assert metadata.get_label("stage") == edge_gateway_stage.name

        spec = resource.spec
        assert spec.id == edge_resource_inherit_stage.id
        assert spec.description == edge_resource_inherit_stage.description
        assert spec.uri == edge_resource_inherit_stage.path
        assert spec.methods == [edge_resource_inherit_stage.method]
        assert spec.match_subpath == edge_resource_inherit_stage.match_subpath
        assert spec.timeout is not None
        assert spec.service != ""
        assert spec.upstream is None

        resource_config = edge_resource_inherit_stage_proxy.config
        assert spec.timeout.connect != resource_config["timeout"]
        assert spec.timeout.read != resource_config["timeout"]
        assert spec.timeout.send != resource_config["timeout"]

        stage_config = edge_gateway_stage_context_proxy_http.config
        assert spec.timeout.connect == stage_config["timeout"]
        assert spec.timeout.read == stage_config["timeout"]
        assert spec.timeout.send == stage_config["timeout"]

        assert spec.rewrite.enabled
        assert spec.rewrite.method == resource_config["method"]
        assert spec.rewrite.path == resource_config["path"]
        assert spec.rewrite.stage_headers == ResourceRewriteHeadersStrategyEnum.APPEND
        assert "X-Set-By-Resource" not in spec.rewrite.headers
        assert "X-Del-By-Resource" not in spec.rewrite.headers
        assert spec.rewrite.headers["X-Set-By-Stage"] == edge_gateway_stage.name
        assert spec.rewrite.headers["X-Del-By-Stage"] == ""

    def test_convert_http_resources_with_edge_resource_overwrite_stage(
        self,
        edge_gateway,
        edge_gateway_stage,
        edge_gateway_stage_context_proxy_http,
        edge_resource_overwrite_stage,
        edge_resource_overwrite_stage_proxy,
        fake_http_resource_convertor,
    ):
        resource = None
        for r in fake_http_resource_convertor.convert():
            if r.spec.name == edge_resource_overwrite_stage.name:
                resource = r
                break

        assert resource is not None
        assert isinstance(resource, BkGatewayResource)

        metadata = resource.metadata
        assert 0 < len(metadata.name) <= 64

        assert metadata.get_label("gateway") == edge_gateway.name
        assert metadata.get_label("stage") == edge_gateway_stage.name

        spec = resource.spec
        assert spec.id == edge_resource_overwrite_stage.id
        assert spec.description == edge_resource_overwrite_stage.description
        assert spec.uri == edge_resource_overwrite_stage.path
        assert spec.methods == [edge_resource_overwrite_stage.method]
        assert spec.match_subpath == edge_resource_overwrite_stage.match_subpath
        assert spec.timeout is not None
        assert spec.service != ""
        assert spec.upstream is not None

        resource_config = edge_resource_overwrite_stage_proxy.config
        assert spec.timeout.connect == resource_config["timeout"]
        assert spec.timeout.read == resource_config["timeout"]
        assert spec.timeout.send == resource_config["timeout"]

        assert spec.rewrite.enabled
        assert spec.rewrite.method == resource_config["method"]
        assert spec.rewrite.path == resource_config["path"]
        assert spec.rewrite.stage_headers == ResourceRewriteHeadersStrategyEnum.APPEND
        assert spec.rewrite.headers["X-Set-By-Stage"] == edge_gateway_stage.name
        assert spec.rewrite.headers["X-Del-By-Stage"] == ""
        assert spec.rewrite.headers["X-Set-By-Resource"] == edge_resource_overwrite_stage.name
        assert spec.rewrite.headers["X-Del-By-Resource"] == ""
