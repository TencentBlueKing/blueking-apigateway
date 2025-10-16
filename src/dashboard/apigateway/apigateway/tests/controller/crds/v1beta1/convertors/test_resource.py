#
# TencentBlueKing is pleased to support the open source community by making
# 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
# Copyright (C) 2025 Tencent. All rights reserved.
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

from apigateway.apps.plugin.constants import PluginBindingScopeEnum
from apigateway.apps.plugin.models import PluginBinding
from apigateway.controller.crds.v1beta1.models.gateway_resource import BkGatewayResource
from apigateway.controller.release_data import PluginData


class TestHttpResourceConvertor:
    def test_convert(self):
        pass

    def test_stage_backend_service_name(self, fake_http_resource_convertor, fake_service_convertor, fake_backend):
        service_name = fake_http_resource_convertor._stage_backend_service_name(fake_backend.id)
        assert service_name == fake_service_convertor.convert()[0].metadata.name

        with pytest.raises(NameError):
            fake_http_resource_convertor._stage_backend_service_name(100)

    def test_get_release_version_route_resource_crd(self, fake_http_resource_convertor):
        resource = fake_http_resource_convertor._get_release_version_route_resource_crd()
        # assert resource.metadata.name == "apigw_builtin__mock_release_version"
        assert resource.spec.id == -1
        assert resource.spec.name == "apigw_builtin__mock_release_version"
        assert resource.spec.description == "获取发布信息，用于检查版本发布结果"
        assert resource.spec.uri == "/__apigw_version"
        assert resource.spec.methods == ["GET"]
        assert len(resource.spec.plugins) == 1
        plugin = resource.spec.plugins[0]
        assert plugin.name == "bk-mock"

    def test_convert_http_resource_timeout(self, fake_http_resource_convertor):
        timeout = fake_http_resource_convertor._convert_http_resource_timeout({})
        assert timeout is None

        timeout = fake_http_resource_convertor._convert_http_resource_timeout({"timeout": 30})
        assert timeout.connect == 30
        assert timeout.read == 30
        assert timeout.send == 30

    def test_convert_http_resource_rewrite(self, fake_http_resource_convertor):
        rewrite = fake_http_resource_convertor._convert_http_resource_rewrite(
            {
                "method": "GET",
                "path": "/test",
            }
        )
        assert rewrite.enabled is True
        assert rewrite.method == "GET"
        assert rewrite.path == "/test"

    def get_resource_plugin_by_name(self, fake_http_resource_convertor, resource, name):
        plugins = fake_http_resource_convertor._convert_http_resource_plugins(resource)
        for plugin in plugins:
            if plugin.name == name:
                return plugin
        return None

    def test_convert_http_resource_plugins(self, fake_http_resource_convertor):
        plugins = fake_http_resource_convertor._convert_http_resource_plugins(
            {
                "id": 1,
                "name": "test",
                "contexts": {
                    "resource_auth": {
                        "config": json.dumps(
                            {
                                "app_verified_required": True,
                                "auth_verified_required": True,
                                "resource_perm_required": True,
                                "skip_auth_verification": False,
                            }
                        )
                    }
                },
            }
        )
        assert len(plugins) == 1
        plugin = plugins[0]
        assert plugin.name == "bk-resource-context"
        assert plugin.config["bk_resource_id"] == 1
        assert plugin.config["bk_resource_name"] == "test"
        assert plugin.config["bk_resource_auth"]["verified_app_required"] is True
        assert plugin.config["bk_resource_auth"]["verified_user_required"] is True
        assert plugin.config["bk_resource_auth"]["resource_perm_required"] is True
        assert plugin.config["bk_resource_auth"]["skip_user_verification"] is False

    def test_convert_http_resource_plugin(
        self,
        faker,
        edge_gateway,
        edge_gateway_stage,
        fake_http_resource_convertor,
        fake_plugin_bk_header_rewrite,
        fake_resource,
    ):
        binding = G(
            PluginBinding,
            gateway=edge_gateway,
            config=fake_plugin_bk_header_rewrite,
            scope_type=PluginBindingScopeEnum.RESOURCE.value,
            scope_id=fake_resource.id,
        )
        # should make_version after the PluginBinding is created
        # patch the self._release_data.get_resource_plugins here
        fake_http_resource_convertor._release_data.get_resource_plugins = lambda x: [
            PluginData(
                type_code=binding.get_type(),
                config={},
                binding_scope_type=PluginBindingScopeEnum.RESOURCE.value,
            )
        ]

        plugins = fake_http_resource_convertor._convert_http_resource_plugins(
            {
                "id": fake_resource.id,
                "name": fake_resource.name,
                "contexts": {
                    "resource_auth": {
                        "config": json.dumps(
                            {
                                "app_verified_required": True,
                                "auth_verified_required": True,
                                "resource_perm_required": True,
                                "skip_auth_verification": False,
                            }
                        )
                    }
                },
            }
        )
        assert len(plugins) == 2
        assert plugins[0].name == "bk-resource-context"
        assert plugins[1].name == "bk-resource-header-rewrite"

    def test_convert_http_resource_wrong_proxy_type(self, fake_http_resource_convertor):
        resource = {"proxy": {"type": "grpc"}}
        assert fake_http_resource_convertor._convert_http_resource(resource) is None

    def test_convert_http_resource_disabled_stage(self, fake_http_resource_convertor):
        resource = {
            "proxy": {"type": "http"},
            "disabled_stages": [fake_http_resource_convertor._release_data.stage.name],
        }
        assert fake_http_resource_convertor._convert_http_resource(resource) is None

    def test_convert_http_resource_disabled_resource(self, fake_http_resource_convertor, fake_service_convertor):
        resource = fake_http_resource_convertor._release_data.resource_version.data[0]

        # services = fake_http_resource_convertor.convert()
        # service = services[0]
        # service_name = service.metadata.name
        service_name = fake_http_resource_convertor._stage_backend_service_name(resource["proxy"]["backend_id"])

        data = fake_http_resource_convertor._convert_http_resource(resource)
        assert isinstance(data, BkGatewayResource)

        assert data is not None

        metadata = data.metadata
        assert 0 < len(metadata.name) <= 64

        assert data.spec.id == resource["id"]
        assert data.spec.name == resource["name"]
        assert data.spec.description == resource["description"]
        assert data.spec.uri == resource["path"]
        assert data.spec.methods == [resource["method"]]
        assert data.spec.match_subpath == resource["match_subpath"]
        assert data.spec.service == service_name
        assert data.spec.upstream is None

        assert metadata.get_label("gateway") == fake_http_resource_convertor._release_data.gateway.name
        assert metadata.get_label("stage") == fake_http_resource_convertor._release_data.stage.name
