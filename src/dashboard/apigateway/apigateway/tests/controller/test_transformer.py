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
import json
from unittest.mock import Mock

import pytest

from apigateway.apps.data_plane.constants import DataPlaneApisixVersionEnum
from apigateway.controller.convertor.constants import LABEL_KEY_APISIX_VERSION, LABEL_KEY_BACKEND_ID
from apigateway.controller.release_data import StageBackendConfig
from apigateway.controller.transformer import (
    BaseTransformer,
    GatewayApisixResourceTransformer,
    GlobalApisixResourceTransformer,
)
from apigateway.core.constants import BackendKindEnum, BackendTypeEnum, ProxyTypeEnum, ResourceKindEnum

APISIX_VERSION_3_13 = DataPlaneApisixVersionEnum.V3_13.value
APISIX_VERSION_3_16 = DataPlaneApisixVersionEnum.V3_16.value
APISIX_VERSION_3_17 = "3.17"


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

    def test_initialization_requires_apisix_version(self):
        """Global transformer should get apisix_version from data_plane callers."""
        with pytest.raises(TypeError):
            GlobalApisixResourceTransformer()

    def test_initialization(self):
        """Test GlobalApisixResourceConvertor initialization"""
        convertor = GlobalApisixResourceTransformer(APISIX_VERSION_3_13)
        assert convertor._converted_plugin_metadata == []

    def test_transform_calls_plugin_metadata_convertor(self, mocker):
        """Test that transform() calls PluginMetadataConvertor"""
        mock_plugin_convertor = mocker.patch("apigateway.controller.transformer.PluginMetadataConvertor")
        mock_instance = Mock()
        mock_instance.convert.return_value = [Mock(), Mock()]
        mock_plugin_convertor.return_value = mock_instance

        transformer = GlobalApisixResourceTransformer(APISIX_VERSION_3_13)
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

        transformer = GlobalApisixResourceTransformer(APISIX_VERSION_3_13)
        transformer.transform()

        resources = list(transformer.get_transformed_resources())
        assert len(resources) == 2
        assert resources[0] == mock_resource1
        assert resources[1] == mock_resource2

    def test_get_transformed_resources_empty(self):
        """Test get_transformed_resources() when no resources are converted"""
        transformer = GlobalApisixResourceTransformer(APISIX_VERSION_3_13)
        resources = list(transformer.get_transformed_resources())
        assert resources == []

    def test_transform_passes_apisix_version(self, mocker):
        """Test that transform() passes the apisix_version into PluginMetadataConvertor"""
        mock_plugin_convertor = mocker.patch("apigateway.controller.transformer.PluginMetadataConvertor")
        mock_plugin_convertor.return_value.convert.return_value = []

        transformer = GlobalApisixResourceTransformer(APISIX_VERSION_3_16)
        assert transformer.apisix_version == APISIX_VERSION_3_16
        transformer.transform()

        assert mock_plugin_convertor.call_args.args[0] == APISIX_VERSION_3_16


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
        gateway.is_ai_gateway = False
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

    def test_standard_gateway_still_accepts_3_13(self, mock_release):
        mock_release.gateway.is_ai_gateway = False

        GatewayApisixResourceTransformer(mock_release, APISIX_VERSION_3_13)

    def test_ai_gateway_accepts_3_16_or_later(self, mock_release):
        mock_release.gateway.is_ai_gateway = True

        GatewayApisixResourceTransformer(mock_release, APISIX_VERSION_3_16)
        GatewayApisixResourceTransformer(mock_release, APISIX_VERSION_3_17)

        with pytest.raises(ValueError, match="APISIX 3.16"):
            GatewayApisixResourceTransformer(mock_release, APISIX_VERSION_3_13)

    def test_ai_gateway_revoke_skips_apisix_version_check(self, mock_release):
        mock_release.gateway.is_ai_gateway = True

        GatewayApisixResourceTransformer(mock_release, APISIX_VERSION_3_13, revoke_flag=True)

    def test_transform_ai_gateway_resources(self, mock_release, mocker):
        mock_release.gateway.is_ai_gateway = True

        release_data = mocker.Mock()
        release_data.gateway = mock_release.gateway
        release_data.stage = mock_release.stage
        release_data.stage.vars = {}
        release_data.resource_version = mock_release.resource_version
        release_data.stage_backend_configs = {
            10: StageBackendConfig(
                backend_id=10,
                backend_name="model-service",
                backend_kind=BackendKindEnum.AI.value,
                backend_type=BackendTypeEnum.HTTP.value,
                config={
                    "timeout": 45000,
                    "instances": [
                        {
                            "name": "primary",
                            "provider": "openai-compatible",
                            "weight": 1,
                            "auth": {"header": {"Authorization": "Bearer test"}},
                            "options": {"model": "gpt-4.1-mini", "temperature": 0.2},
                            "override": {"endpoint": "https://models.example.com/v1/chat/completions"},
                        }
                    ],
                },
            )
        }
        release_data.resource_configs = [
            {
                "id": 11,
                "name": "chat-completions",
                "kind": ResourceKindEnum.AI.value,
                "method": "ANY",
                "path": "/v1/chat/completions",
                "enable_websocket": True,
                "disabled_stages": [],
                "proxy": {
                    "type": ProxyTypeEnum.HTTP.value,
                    "backend_id": 10,
                    "config": json.dumps({"path": "/ignored", "method": "GET", "match_subpath": True, "timeout": 99}),
                },
                "contexts": {"resource_auth": {"config": json.dumps({})}},
                "plugins": [],
            }
        ]
        release_data.get_stage_plugins.return_value = []
        release_data.get_resource_plugins.return_value = []
        release_data.jwt_private_key = "test-key"
        release_data.gateway_auth_config = {}
        mocker.patch("apigateway.controller.transformer.ReleaseData", return_value=release_data)

        transformer = GatewayApisixResourceTransformer(mock_release, APISIX_VERSION_3_16, publish_id=123)
        transformer.transform()
        resources = list(transformer.get_transformed_resources())
        service = next(resource for resource in resources if resource.kind == "service")
        route = next(resource for resource in resources if resource.kind == "route" and resource.service_id)
        service_payload = service.model_dump(mode="json", exclude_none=True)
        route_payload = route.model_dump(mode="json", exclude_none=True)

        assert "upstream" not in service_payload
        assert "bk-error-wrapper" in service_payload["plugins"]
        assert service_payload["plugins"]["ai-proxy"]["options"]["temperature"] == 0.2
        assert service_payload["plugins"]["ai-proxy"]["logging"] == {
            "summaries": True,
            "payloads": False,
        }
        assert service.labels.get_label(LABEL_KEY_BACKEND_ID) == "10"
        assert service.labels.get_label(LABEL_KEY_APISIX_VERSION) == APISIX_VERSION_3_16
        assert route_payload["service_id"] == service_payload["id"]
        assert route_payload["methods"] == ["POST"]
        assert "bk-proxy-rewrite" not in route_payload["plugins"]

    def test_initialization_requires_apisix_version(self, mock_release):
        """Gateway transformer should get apisix_version from data_plane callers."""
        with pytest.raises(TypeError):
            GatewayApisixResourceTransformer(mock_release)

    def test_initialization(self, mock_release):
        """Test GatewayApisixResourceTransformer initialization with various parameters"""
        # Test initialization
        convertor = GatewayApisixResourceTransformer(mock_release, APISIX_VERSION_3_13)
        assert convertor._release_data._release == mock_release
        assert convertor.publish_id is None
        assert convertor.revoke_flag is False

        # Test with publish_id
        convertor_with_publish_id = GatewayApisixResourceTransformer(mock_release, APISIX_VERSION_3_13, publish_id=999)
        assert convertor_with_publish_id.publish_id == 999

        # Test with revoke_flag
        convertor_with_revoke = GatewayApisixResourceTransformer(mock_release, APISIX_VERSION_3_13, revoke_flag=True)
        assert convertor_with_revoke.revoke_flag is True

        # Test schema v2 requirement
        mock_release.resource_version.is_schema_v2 = False
        with pytest.raises(ValueError) as exc_info:
            GatewayApisixResourceTransformer(mock_release, APISIX_VERSION_3_13)
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
        transformer = GatewayApisixResourceTransformer(
            mock_release, APISIX_VERSION_3_13, publish_id=123, revoke_flag=True
        )
        transformer.transform()

        # Verify all convertors were called with correct parameters
        mock_service_convertor.assert_called_once_with(mock_release_data, 123, APISIX_VERSION_3_13, True)
        expected_mapping = {123: "service-1", 456: "service-2"}
        mock_route_convertor.assert_called_once_with(
            mock_release_data, expected_mapping, 123, APISIX_VERSION_3_13, True
        )
        mock_bk_release_convertor.assert_called_once_with(mock_release_data, 123, APISIX_VERSION_3_13)

        # Verify internal state
        assert len(transformer._converted_services) == 2
        assert len(transformer._converted_routes) == 2
        assert len(transformer._converted_bk_releases) == 1
        assert transformer.publish_id == 123
        assert transformer.revoke_flag is True

        # Verify get_transformed_resources returns resources
        resources = list(transformer.get_transformed_resources())
        assert len(resources) == 5  # 2 services + 2 routes + 1 bk_release

    def test_transform_passes_apisix_version(self, mock_release, mocker):
        """transform() should pass the apisix_version into service/route/bk_release convertors"""
        mock_release_data = mocker.Mock()
        mock_release_data.gateway.name = "test-gateway"
        mock_release_data.stage.name = "prod"
        mock_release_data.resource_version.version = "v1"
        mocker.patch("apigateway.controller.transformer.ReleaseData", return_value=mock_release_data)

        mock_service_convertor = mocker.patch("apigateway.controller.transformer.ServiceConvertor")
        mock_service_convertor.return_value.convert.return_value = []
        mock_route_convertor = mocker.patch("apigateway.controller.transformer.RouteConvertor")
        mock_route_convertor.return_value.convert.return_value = []
        mock_bk_release_convertor = mocker.patch("apigateway.controller.transformer.BkReleaseConvertor")
        mock_bk_release_convertor.return_value.convert.return_value = []

        transformer = GatewayApisixResourceTransformer(mock_release, APISIX_VERSION_3_16, publish_id=123)
        assert transformer.apisix_version == APISIX_VERSION_3_16
        transformer.transform()

        assert mock_service_convertor.call_args.args[2] == APISIX_VERSION_3_16
        assert mock_route_convertor.call_args.args[3] == APISIX_VERSION_3_16
        assert mock_bk_release_convertor.call_args.args[2] == APISIX_VERSION_3_16

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

        transformer = GatewayApisixResourceTransformer(mock_release, APISIX_VERSION_3_13, publish_id=123)
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

        transformer_invalid = GatewayApisixResourceTransformer(mock_release, APISIX_VERSION_3_13, publish_id=123)
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

        transformer = GatewayApisixResourceTransformer(mock_release, APISIX_VERSION_3_13, publish_id=123)
        with pytest.raises(Exception, match="Service conversion failed"):
            transformer.transform()

        # Test invalid release structure
        mock_release_invalid = mocker.Mock()
        mock_release_invalid.gateway.is_ai_gateway = False
        del mock_release_invalid.resource_version
        with pytest.raises(AttributeError):
            GatewayApisixResourceTransformer(mock_release_invalid, APISIX_VERSION_3_13)
