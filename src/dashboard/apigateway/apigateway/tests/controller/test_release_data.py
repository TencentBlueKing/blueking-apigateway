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
import pytest

from apigateway.controller.release_data import PluginData, ReleaseData


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

    def test_get_stage_backend_configs_empty(self, mock_release, mocker):
        """Test get_stage_backend_configs with no configs"""
        mock_qs = mocker.Mock()
        mock_qs.filter.return_value = mock_qs
        mock_qs.prefetch_related.return_value = mock_qs
        mock_qs.all.return_value = []

        mocker.patch("apigateway.controller.release_data.BackendConfig.objects", mock_qs)

        release_data = ReleaseData(mock_release)
        configs = release_data.get_stage_backend_configs()

        assert configs == {}

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
