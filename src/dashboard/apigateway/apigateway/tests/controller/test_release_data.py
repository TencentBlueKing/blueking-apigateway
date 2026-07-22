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
import dataclasses

import pytest
from django_dynamic_fixture import G

from apigateway.controller.release_data import PluginData, ReleaseData, StageBackendConfig
from apigateway.core.constants import BackendKindEnum
from apigateway.core.models import Backend, BackendConfig


class TestPluginData:
    """Test PluginData class"""

    def test_plugin_data_creation(self):
        """Test creating PluginData"""
        plugin = PluginData(
            type_code="bk-cors",
            config={"allow_origins": "*"},
            binding_scope_type="stage",
        )

        assert plugin.type_code == "bk-cors"
        assert plugin.config == {"allow_origins": "*"}
        assert plugin.binding_scope_type == "stage"

    def test_plugin_data_name_default(self):
        """Test plugin name defaults to type_code"""
        plugin = PluginData(
            type_code="bk-cors",
            config={},
            binding_scope_type="stage",
        )

        assert plugin.name == "bk-cors"

    def test_plugin_data_name_rate_limit_stage(self):
        """Test plugin name mapping for rate limit at stage level"""
        plugin = PluginData(
            type_code="bk-rate-limit",
            config={},
            binding_scope_type="stage",
        )

        assert plugin.name == "bk-stage-rate-limit"

    def test_plugin_data_name_rate_limit_resource(self):
        """Test plugin name mapping for rate limit at resource level"""
        plugin = PluginData(
            type_code="bk-rate-limit",
            config={},
            binding_scope_type="resource",
        )

        assert plugin.name == "bk-resource-rate-limit"

    def test_plugin_data_name_header_rewrite_stage(self):
        """Test plugin name mapping for header rewrite at stage level"""
        plugin = PluginData(
            type_code="bk-header-rewrite",
            config={},
            binding_scope_type="stage",
        )

        assert plugin.name == "bk-stage-header-rewrite"

    def test_plugin_data_name_header_rewrite_resource(self):
        """Test plugin name mapping for header rewrite at resource level"""
        plugin = PluginData(
            type_code="bk-header-rewrite",
            config={},
            binding_scope_type="resource",
        )

        assert plugin.name == "bk-resource-header-rewrite"

    def test_plugin_data_type_code_to_name_mapping(self):
        """Test _type_code_to_name class variable"""
        expected_mappings = {
            "bk-rate-limit:stage": "bk-stage-rate-limit",
            "bk-rate-limit:resource": "bk-resource-rate-limit",
            "bk-header-rewrite:stage": "bk-stage-header-rewrite",
            "bk-header-rewrite:resource": "bk-resource-header-rewrite",
        }

        assert PluginData._type_code_to_name == expected_mappings


class TestReleaseData:
    """Test ReleaseData class"""

    @pytest.fixture
    def mock_release(self, mocker):
        """Create a mock release"""
        release = mocker.Mock()
        release.pk = 123

        # Mock gateway
        gateway = mocker.Mock()
        gateway.pk = 456
        gateway.name = "test-gateway"
        release.gateway = gateway

        # Mock stage
        stage = mocker.Mock()
        stage.pk = 789
        stage.name = "prod"
        release.stage = stage

        # Mock resource version
        resource_version = mocker.Mock()
        resource_version.pk = 101
        resource_version.data = []
        release.resource_version = resource_version

        return release

    def test_release_data_gateway_property(self, mock_release):
        """Test gateway cached property"""
        release_data = ReleaseData(mock_release)
        gateway = release_data.gateway

        assert gateway == mock_release.gateway
        assert gateway.pk == 456

    def test_release_data_stage_property(self, mock_release):
        """Test stage cached property"""
        release_data = ReleaseData(mock_release)
        stage = release_data.stage

        assert stage == mock_release.stage
        assert stage.pk == 789

    def test_release_data_resource_version_property(self, mock_release):
        """Test resource_version cached property"""
        release_data = ReleaseData(mock_release)
        resource_version = release_data.resource_version

        assert resource_version == mock_release.resource_version
        assert resource_version.pk == 101

    def test_resource_configs_reuses_parsed_resource_version_data(self, mock_release, mocker):
        """Large releases should parse resource_version.data once per release publish."""

        class ResourceVersionStub:
            pk = 101

        data_property = mocker.PropertyMock(return_value=[{"id": 1, "plugins": []}])
        ResourceVersionStub.data = data_property
        mock_release.resource_version = ResourceVersionStub()

        release_data = ReleaseData(mock_release)

        assert release_data.resource_configs == [{"id": 1, "plugins": []}]
        assert release_data.resource_configs == [{"id": 1, "plugins": []}]
        assert data_property.call_count == 1

    def test_release_data_jwt_private_key(self, mock_release, mocker):
        """Test jwt_private_key cached property"""
        mocker.patch(
            "apigateway.controller.release_data.GatewayJWTHandler.get_private_key",
            return_value="test-private-key",
        )

        release_data = ReleaseData(mock_release)
        private_key = release_data.jwt_private_key

        assert private_key == "test-private-key"

    def test_release_data_gateway_auth_config(self, mock_release, mocker):
        """Test gateway_auth_config cached property"""
        mock_context = mocker.patch("apigateway.controller.release_data.GatewayAuthContext")
        mock_context.return_value.get_config.return_value = {"auth": "config"}

        release_data = ReleaseData(mock_release)
        auth_config = release_data.gateway_auth_config

        assert auth_config == {"auth": "config"}

    def test_get_stage_plugins_empty(self, mock_release, mocker):
        """Test get_stage_plugins with no plugins"""
        mocker.patch(
            "apigateway.controller.release_data.PluginBinding.objects.query_scope_id_to_bindings",
            return_value={},
        )

        release_data = ReleaseData(mock_release)
        plugins = release_data.get_stage_plugins()

        assert plugins == []

    def test_stage_backend_configs_are_typed_cached_snapshots(
        self,
        mocker,
        fake_gateway,
        fake_stage,
        django_assert_num_queries,
    ):
        standard_config = {
            "type": "node",
            "timeout": 30,
            "loadbalance": "roundrobin",
            "hosts": [{"scheme": "http", "host": "example.com", "weight": 100}],
        }
        standard_backend = G(
            Backend,
            gateway=fake_gateway,
            name="standard-service",
            kind=BackendKindEnum.STANDARD.value,
        )
        ai_backend = G(
            Backend,
            gateway=fake_gateway,
            name="model-service",
            kind=BackendKindEnum.AI.value,
        )
        standard_backend_config = BackendConfig.objects.create(
            gateway=fake_gateway,
            stage=fake_stage,
            backend=standard_backend,
            config=standard_config,
        )
        ai_backend_config = {
            "timeout": 300,
            "instances": [
                {
                    "name": "primary",
                    "provider": "openai",
                    "weight": 1,
                    "auth": {"header": {"Authorization": "Bearer secret"}},
                    "options": {"model": "gpt-4o"},
                }
            ],
        }
        ai_backend_config_model = BackendConfig.objects.create(
            gateway=fake_gateway,
            stage=fake_stage,
            backend=ai_backend,
            config=ai_backend_config,
        )
        release = mocker.Mock(gateway=fake_gateway, stage=fake_stage)
        release_data = ReleaseData(release)

        with django_assert_num_queries(1):
            configs = release_data.stage_backend_configs
            assert release_data.stage_backend_configs is configs

        assert configs[standard_backend.id] == StageBackendConfig(
            backend_id=standard_backend.id,
            backend_name=standard_backend.name,
            backend_kind=BackendKindEnum.STANDARD.value,
            backend_type=standard_backend.type,
            config=standard_backend_config.config,
        )
        assert configs[ai_backend.id] == StageBackendConfig(
            backend_id=ai_backend.id,
            backend_name=ai_backend.name,
            backend_kind=BackendKindEnum.AI.value,
            backend_type=ai_backend.type,
            config=ai_backend_config_model.config,
        )

        with pytest.raises(dataclasses.FrozenInstanceError):
            configs[ai_backend.id].backend_name = "changed"

    def test_get_resource_plugins_empty(self, mock_release):
        """Test get_resource_plugins with no plugins"""
        release_data = ReleaseData(mock_release)
        plugins = release_data.get_resource_plugins(1)

        assert plugins == []

    def test_release_data_resources_plugins_property(self, mock_release, mocker):
        """Test _resources_plugins property"""
        # Mock the convertor factory
        mock_convertor = mocker.Mock()
        mock_convertor.convert.return_value = {"key": "value"}

        mocker.patch(
            "apigateway.controller.release_data.PluginConvertorFactory.get_convertor",
            return_value=mock_convertor,
        )

        # Set up resource version data with plugins
        mock_release.resource_version.data = [
            {
                "id": 1,
                "plugins": [
                    {
                        "type": "bk-cors",
                        "config": {"allow_origins": "*"},
                    }
                ],
            }
        ]

        release_data = ReleaseData(mock_release)
        resources_plugins = release_data._resources_plugins

        assert 1 in resources_plugins
        assert len(resources_plugins[1]) > 0

        resource_plugins2 = release_data._resources_plugins
        assert resource_plugins2 == resources_plugins
