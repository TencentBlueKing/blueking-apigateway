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
from unittest.mock import Mock

import pytest

from apigateway.controller.transformer import (
    BaseTransformer,
    GatewayApisixResourceTransformer,
    GlobalApisixResourceTransformer,
)


class TestBaseTransformer:
    """Test BaseTransformer abstract class"""

    def test_base_transformer_is_abstract(self):
        """Test that BaseTransformer cannot be instantiated directly"""
        with pytest.raises(TypeError):
            BaseTransformer()

    def test_base_transformer_abstract_methods(self):
        """Test that BaseTransformer has required abstract methods"""

        # Create a concrete implementation to test abstract methods
        class ConcreteTransformer(BaseTransformer):
            def transform(self):
                pass

            def get_transformed_resources(self):
                return []

        transformer = ConcreteTransformer()
        assert hasattr(transformer, "transform")
        assert hasattr(transformer, "get_transformed_resources")
        assert callable(transformer.transform)
        assert callable(transformer.get_transformed_resources)


class TestGlobalApisixResourceConvertor:
    """Test GlobalApisixResourceConvertor class"""

    def test_initialization(self):
        """Test GlobalApisixResourceConvertor initialization"""
        convertor = GlobalApisixResourceTransformer()
        assert convertor._converted_plugin_metadata == []

    def test_transform_calls_plugin_metadata_convertor(self, mocker):
        """Test that transform() calls PluginMetadataConvertor"""
        mock_plugin_convertor = mocker.patch("apigateway.controller.transformer.PluginMetadataConvertor")
        mock_instance = Mock()
        mock_instance.convert.return_value = [Mock(), Mock()]
        mock_plugin_convertor.return_value = mock_instance

        transformer = GlobalApisixResourceTransformer()
        transformer.transform()

        # Verify PluginMetadataConvertor was instantiated and convert() was called
        mock_plugin_convertor.assert_called_once()
        mock_instance.convert.assert_called_once()
        assert len(transformer._converted_plugin_metadata) == 2

    def test_get_transformed_resources(self, mocker):
        """Test get_transformed_resources() method"""
        mock_plugin_convertor = mocker.patch("apigateway.controller.transformer.PluginMetadataConvertor")
        mock_instance = Mock()
        mock_resource1 = Mock()
        mock_resource2 = Mock()
        mock_instance.convert.return_value = [mock_resource1, mock_resource2]
        mock_plugin_convertor.return_value = mock_instance

        transformer = GlobalApisixResourceTransformer()
        transformer.transform()

        resources = list(transformer.get_transformed_resources())
        assert len(resources) == 2
        assert resources[0] == mock_resource1
        assert resources[1] == mock_resource2

    def test_get_transformed_resources_empty(self):
        """Test get_transformed_resources() when no resources are converted"""
        transformer = GlobalApisixResourceTransformer()
        resources = list(transformer.get_transformed_resources())
        assert resources == []


class TestGatewayApisixResourceConvertor:
    """Test GatewayApisixResourceConvertor class"""

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
        resource_version.is_schema_v2 = True
        resource_version.data = []
        resource_version.version = "v1"
        release.resource_version = resource_version

        return release

    def test_initialization(self, mock_release):
        """Test GatewayApisixResourceTransformer initialization with various parameters"""
        # Test default initialization
        convertor = GatewayApisixResourceTransformer(mock_release)
        assert convertor._release_data._release == mock_release
        assert convertor.publish_id is None
        assert convertor.revoke_flag is False

        # Test with publish_id
        convertor_with_publish_id = GatewayApisixResourceTransformer(mock_release, publish_id=999)
        assert convertor_with_publish_id.publish_id == 999

        # Test with revoke_flag
        convertor_with_revoke = GatewayApisixResourceTransformer(mock_release, revoke_flag=True)
        assert convertor_with_revoke.revoke_flag is True

        # Test schema v2 requirement
        mock_release.resource_version.is_schema_v2 = False
        with pytest.raises(ValueError) as exc_info:
            GatewayApisixResourceTransformer(mock_release)
        assert "Only support resource_version schema v2" in str(exc_info.value)

    def test_transform_workflow(self, mock_release, mocker):
        """Test complete transform workflow with all convertors"""
        # Mock ReleaseData
        mock_release_data = mocker.Mock()
        mock_release_data.gateway.name = "test-gateway"
        mock_release_data.stage.name = "prod"
        mock_release_data.resource_version.version = "v1"
        mocker.patch("apigateway.controller.transformer.ReleaseData", return_value=mock_release_data)

        # Create mock services with backend IDs
        mock_service1 = Mock()
        mock_service1.id = "service-1"
        mock_service1.labels.get_label.return_value = "123"

        mock_service2 = Mock()
        mock_service2.id = "service-2"
        mock_service2.labels.get_label.return_value = "456"

        # Mock convertors
        mock_service_convertor = mocker.patch("apigateway.controller.transformer.ServiceConvertor")
        mock_service_convertor.return_value.convert.return_value = [mock_service1, mock_service2]

        mock_route_convertor = mocker.patch("apigateway.controller.transformer.RouteConvertor")
        mock_route_convertor.return_value.convert.return_value = [Mock(), Mock()]

        mock_bk_release_convertor = mocker.patch("apigateway.controller.transformer.BkReleaseConvertor")
        mock_bk_release_convertor.return_value.convert.return_value = [Mock()]

        # Execute transform
        transformer = GatewayApisixResourceTransformer(mock_release, publish_id=123, revoke_flag=True)
        transformer.transform()

        # Verify all convertors were called with correct parameters
        mock_service_convertor.assert_called_once_with(mock_release_data, 123)
        expected_mapping = {123: "service-1", 456: "service-2"}
        mock_route_convertor.assert_called_once_with(mock_release_data, expected_mapping, 123, True)
        mock_bk_release_convertor.assert_called_once_with(mock_release_data, 123)

        # Verify internal state
        assert len(transformer._converted_services) == 2
        assert len(transformer._converted_routes) == 2
        assert len(transformer._converted_bk_releases) == 1
        assert transformer.publish_id == 123
        assert transformer.revoke_flag is True

        # Verify get_transformed_resources returns resources
        resources = list(transformer.get_transformed_resources())
        assert len(resources) == 5  # 2 services + 2 routes + 1 bk_release

    def test_backend_service_mapping(self, mock_release, mocker):
        """Test backend service mapping creation and edge cases"""
        mock_release_data = mocker.Mock()
        mock_release_data.gateway.name = "test-gateway"
        mock_release_data.stage.name = "prod"
        mock_release_data.resource_version.version = "v1"
        mocker.patch("apigateway.controller.transformer.ReleaseData", return_value=mock_release_data)

        # Test normal case with backend IDs
        mock_service1 = Mock()
        mock_service1.id = "service-1"
        mock_service1.labels.get_label.return_value = "123"

        mock_service2 = Mock()
        mock_service2.id = "service-2"
        mock_service2.labels.get_label.return_value = "456"

        mock_service_convertor = mocker.patch("apigateway.controller.transformer.ServiceConvertor")
        mock_service_convertor.return_value.convert.return_value = [mock_service1, mock_service2]

        mock_route_convertor = mocker.patch("apigateway.controller.transformer.RouteConvertor")
        mock_route_convertor.return_value.convert.return_value = []

        mock_bk_release_convertor = mocker.patch("apigateway.controller.transformer.BkReleaseConvertor")
        mock_bk_release_convertor.return_value.convert.return_value = []

        transformer = GatewayApisixResourceTransformer(mock_release, publish_id=123)
        transformer.transform()

        # Verify correct mapping was created
        expected_mapping = {123: "service-1", 456: "service-2"}
        call_args = mock_route_convertor.call_args
        # RouteConvertor is called with positional args: (release_data, backend_service_mapping, publish_id, revoke_flag)
        assert call_args[0][1] == expected_mapping  # backend_service_mapping is the 2nd positional argument

        # Test edge case: invalid backend ID
        mock_service_invalid = Mock()
        mock_service_invalid.id = "service-invalid"
        mock_service_invalid.labels.get_label.return_value = "invalid-id"

        mock_service_convertor.return_value.convert.return_value = [mock_service_invalid]

        transformer_invalid = GatewayApisixResourceTransformer(mock_release, publish_id=123)
        with pytest.raises(ValueError):
            transformer_invalid.transform()

    def test_error_handling(self, mock_release, mocker):
        """Test error handling scenarios"""
        mock_release_data = mocker.Mock()
        mock_release_data.gateway.name = "test-gateway"
        mock_release_data.stage.name = "prod"
        mock_release_data.resource_version.version = "v1"
        mocker.patch("apigateway.controller.transformer.ReleaseData", return_value=mock_release_data)

        # Test convertor error propagation
        mock_service_convertor = mocker.patch("apigateway.controller.transformer.ServiceConvertor")
        mock_service_convertor.return_value.convert.side_effect = Exception("Service conversion failed")

        transformer = GatewayApisixResourceTransformer(mock_release, publish_id=123)
        with pytest.raises(Exception, match="Service conversion failed"):
            transformer.transform()

        # Test invalid release structure
        mock_release_invalid = mocker.Mock()
        del mock_release_invalid.resource_version
        with pytest.raises(AttributeError):
            GatewayApisixResourceTransformer(mock_release_invalid)
