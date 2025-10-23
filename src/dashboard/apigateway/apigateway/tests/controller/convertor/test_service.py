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
import base64

import pytest
from django.conf import settings
from django.utils.encoding import force_bytes, force_str

from apigateway.controller.convertor.base import GatewayResourceConvertor
from apigateway.controller.convertor.service import ServiceConvertor


class TestServiceConvertor:
    """Test ServiceConvertor class"""

    @pytest.fixture
    def mock_release_data(self, mocker):
        """Create a mock release data"""
        release_data = mocker.Mock()
        release_data.gateway = mocker.Mock()
        release_data.gateway.pk = 123
        release_data.gateway.name = "test-gateway"
        release_data.stage = mocker.Mock()
        release_data.stage.pk = 456
        release_data.stage.name = "prod"
        release_data.stage.description = "Production environment"
        return release_data

    def test_service_convertor_initialization(self, mock_release_data):
        """Test ServiceConvertor initialization"""
        convertor = ServiceConvertor(mock_release_data, publish_id=123)
        assert convertor is not None
        assert convertor._release_data == mock_release_data
        assert convertor._publish_id == 123

    def test_service_convertor_is_gateway_resource_convertor(self, mock_release_data):
        """Test that ServiceConvertor is a GatewayResourceConvertor"""
        convertor = ServiceConvertor(mock_release_data, publish_id=123)
        assert isinstance(convertor, GatewayResourceConvertor)

    def test_service_convertor_inherits_gateway_properties(self, mock_release_data):
        """Test that ServiceConvertor inherits properties from GatewayResourceConvertor"""
        convertor = ServiceConvertor(mock_release_data, publish_id=123)

        assert convertor.gateway_id == 123
        assert convertor.gateway_name == "test-gateway"
        assert convertor.stage_id == 456
        assert convertor.stage_name == "prod"

    def test_convert_with_no_backend_configs(self, mock_release_data):
        """Test convert with no backend configs"""
        mock_release_data.get_stage_backend_configs.return_value = {}

        convertor = ServiceConvertor(mock_release_data, publish_id=123)
        result = convertor.convert()

        assert result == []

    def test_convert_with_backend_config_no_hosts(self, mock_release_data, mocker):
        """Test convert with backend config but no hosts"""
        mock_release_data.get_stage_backend_configs.return_value = {
            1: {"timeout": 60, "hosts": []},
        }

        convertor = ServiceConvertor(mock_release_data, publish_id=123)

        with pytest.raises(ValueError, match="backend 1 has no hosts"):
            convertor.convert()

    def test_convert_with_valid_backend_config(self, mock_release_data, mocker):
        """Test convert with valid backend config"""
        # Mock Backend model
        mock_backend = mocker.Mock()
        mock_backend.id = 1
        mock_backend.name = "backend-service"
        mock_backend.description = "Test backend"

        mocker.patch(
            "apigateway.controller.convertor.service.Backend.objects.get",
            return_value=mock_backend,
        )

        mock_release_data.get_stage_backend_configs.return_value = {
            1: {
                "timeout": 60,
                "hosts": [
                    {"scheme": "http", "host": "example.com", "weight": 100},
                ],
            },
        }
        mock_release_data.get_stage_plugins.return_value = []
        mock_release_data.jwt_private_key = "test-key"
        mock_release_data.gateway_auth_config = {"auth": "config"}

        convertor = ServiceConvertor(mock_release_data, publish_id=123)
        result = convertor.convert()

        assert len(result) == 1
        assert result[0].id == "test-gateway.prod.456-1"
        assert "backend-service" in result[0].name

    def test_convert_with_multiple_backends(self, mock_release_data, mocker):
        """Test convert with multiple backend configs"""
        mock_backend1 = mocker.Mock()
        mock_backend1.id = 1
        mock_backend1.name = "backend-1"
        mock_backend1.description = "First backend"

        mock_backend2 = mocker.Mock()
        mock_backend2.id = 2
        mock_backend2.name = "backend-2"
        mock_backend2.description = "Second backend"

        def get_backend(id):
            return mock_backend1 if id == 1 else mock_backend2

        mocker.patch(
            "apigateway.controller.convertor.service.Backend.objects.get",
            side_effect=get_backend,
        )

        mock_release_data.get_stage_backend_configs.return_value = {
            1: {"timeout": 60, "hosts": [{"scheme": "http", "host": "example1.com", "weight": 100}]},
            2: {"timeout": 30, "hosts": [{"scheme": "http", "host": "example2.com", "weight": 50}]},
        }
        mock_release_data.get_stage_plugins.return_value = []
        mock_release_data.jwt_private_key = "test-key"
        mock_release_data.gateway_auth_config = {}

        convertor = ServiceConvertor(mock_release_data, publish_id=123)
        result = convertor.convert()

        assert len(result) == 2
        assert result[0].id == "test-gateway.prod.456-1"
        assert result[1].id == "test-gateway.prod.456-2"

    def test_convert_with_https_scheme(self, mock_release_data, mocker):
        """Test convert with HTTPS scheme"""
        mock_backend = mocker.Mock()
        mock_backend.id = 1
        mock_backend.name = "backend-service"
        mock_backend.description = ""

        mocker.patch(
            "apigateway.controller.convertor.service.Backend.objects.get",
            return_value=mock_backend,
        )

        mock_release_data.get_stage_backend_configs.return_value = {
            1: {
                "timeout": 60,
                "hosts": [
                    {"scheme": "https", "host": "secure.example.com", "weight": 100},
                ],
            },
        }
        mock_release_data.get_stage_plugins.return_value = []
        mock_release_data.jwt_private_key = "test-key"
        mock_release_data.gateway_auth_config = {}

        convertor = ServiceConvertor(mock_release_data, publish_id=123)
        result = convertor.convert()

        assert len(result) == 1
        # Verify HTTPS scheme is used
        assert result[0].upstream.scheme.value == "https"
        # port should be 443
        assert result[0].upstream.nodes[0].port == 443

    def test_convert_with_custom_port(self, mock_release_data, mocker):
        """Test convert with custom port"""
        mock_backend = mocker.Mock()
        mock_backend.id = 1
        mock_backend.name = "backend-service"
        mock_backend.description = ""

        mocker.patch(
            "apigateway.controller.convertor.service.Backend.objects.get",
            return_value=mock_backend,
        )

        mock_release_data.get_stage_backend_configs.return_value = {
            1: {
                "timeout": 60,
                "hosts": [
                    {"scheme": "http", "host": "example.com:8080", "weight": 100},
                ],
            },
        }
        mock_release_data.get_stage_plugins.return_value = []
        mock_release_data.jwt_private_key = "test-key"
        mock_release_data.gateway_auth_config = {}

        convertor = ServiceConvertor(mock_release_data, publish_id=123)
        result = convertor.convert()

        assert len(result) == 1
        assert result[0].upstream.nodes[0].port == 8080

    def test_build_service_plugins(self, mock_release_data, mocker):
        """Test _build_service_plugins method"""
        # Mock the three plugin methods
        mock_default_plugins = {"plugin1": mocker.Mock(), "plugin2": mocker.Mock()}
        mock_binding_plugins = {"plugin3": mocker.Mock()}
        mock_extra_plugins = {"plugin4": mocker.Mock()}

        mocker.patch.object(ServiceConvertor, "_get_stage_default_plugins", return_value=mock_default_plugins)
        mocker.patch.object(ServiceConvertor, "_get_stage_binding_plugins", return_value=mock_binding_plugins)
        mocker.patch.object(ServiceConvertor, "_get_stage_extra_plugins", return_value=mock_extra_plugins)

        convertor = ServiceConvertor(mock_release_data, publish_id=123)
        result = convertor._build_service_plugins()

        # Should contain all plugins from the three methods
        assert len(result) == len(mock_default_plugins) + len(mock_binding_plugins) + len(mock_extra_plugins)
        expected_plugins = {**mock_default_plugins, **mock_binding_plugins, **mock_extra_plugins}
        assert result == expected_plugins

    def test_get_stage_default_plugins_basic(self, mock_release_data, mocker):
        """Test _get_stage_default_plugins with basic configuration"""
        # Mock settings
        mocker.patch.object(settings, "GATEWAY_CONCURRENCY_LIMIT_ENABLED", False)
        mocker.patch.object(settings, "ENABLE_MULTI_TENANT_MODE", False)

        # Mock release data properties
        mock_release_data.jwt_private_key = "test-jwt-key"
        mock_release_data.gateway_auth_config = {"auth": "config"}

        convertor = ServiceConvertor(mock_release_data, publish_id=123)
        result = convertor._get_stage_default_plugins()

        # Check that basic plugins are present
        expected_plugins = [
            "prometheus",
            "bk-real-ip",
            "bk-auth-validate",
            "bk-auth-verify",
            "bk-break-recursive-call",
            "bk-delete-sensitive",
            "bk-log-context",
            "bk-delete-cookie",
            "bk-error-wrapper",
            "bk-jwt",
            "bk-request-id",
            "bk-response-check",
            "bk-permission",
            "bk-debug",
            "file-logger",
            "bk-stage-context",
            "bk-default-tenant",
        ]

        for plugin_name in expected_plugins:
            assert plugin_name in result

        # Check that concurrency limit plugin is not present
        assert "bk-concurrency-limit" not in result

        # Check that multi-tenant plugins are not present
        assert "bk-tenant-verify" not in result
        assert "bk-tenant-validate" not in result

        # Check bk-stage-context plugin configuration
        stage_context_plugin = result["bk-stage-context"]
        assert stage_context_plugin.bk_gateway_name == "test-gateway"
        assert stage_context_plugin.bk_gateway_id == 123
        assert stage_context_plugin.bk_stage_name == "prod"
        assert stage_context_plugin.bk_api_auth == {"auth": "config"}

        # Check JWT private key is base64 encoded
        expected_jwt_key = force_str(base64.b64encode(force_bytes("test-jwt-key")))
        assert stage_context_plugin.jwt_private_key == expected_jwt_key

    def test_get_stage_default_plugins_with_concurrency_limit(self, mock_release_data, mocker):
        """Test _get_stage_default_plugins with concurrency limit enabled"""
        mocker.patch.object(settings, "GATEWAY_CONCURRENCY_LIMIT_ENABLED", True)
        mocker.patch.object(settings, "ENABLE_MULTI_TENANT_MODE", False)

        mock_release_data.jwt_private_key = "test-jwt-key"
        mock_release_data.gateway_auth_config = {}

        convertor = ServiceConvertor(mock_release_data, publish_id=123)
        result = convertor._get_stage_default_plugins()

        # Check that concurrency limit plugin is present
        assert "bk-concurrency-limit" in result

    def test_get_stage_default_plugins_multi_tenant_mode(self, mock_release_data, mocker):
        """Test _get_stage_default_plugins with multi-tenant mode enabled"""
        mocker.patch.object(settings, "GATEWAY_CONCURRENCY_LIMIT_ENABLED", False)
        mocker.patch.object(settings, "ENABLE_MULTI_TENANT_MODE", True)

        # Mock gateway with tenant properties
        mock_release_data.gateway.tenant_mode = "shared"
        mock_release_data.gateway.tenant_id = "tenant-123"
        mock_release_data.jwt_private_key = "test-jwt-key"
        mock_release_data.gateway_auth_config = {}

        convertor = ServiceConvertor(mock_release_data, publish_id=123)
        result = convertor._get_stage_default_plugins()

        # Check that multi-tenant plugins are present
        assert "bk-tenant-verify" in result
        assert "bk-tenant-validate" in result
        assert "bk-default-tenant" not in result

        # Check tenant-validate plugin configuration
        tenant_validate_plugin = result["bk-tenant-validate"]
        assert tenant_validate_plugin.tenant_mode == "shared"
        assert tenant_validate_plugin.tenant_id == "tenant-123"

    def test_get_stage_binding_plugins_empty(self, mock_release_data):
        """Test _get_stage_binding_plugins with no stage plugins"""
        mock_release_data.get_stage_plugins.return_value = []

        convertor = ServiceConvertor(mock_release_data, publish_id=123)
        result = convertor._get_stage_binding_plugins()

        assert result == {}

    def test_get_stage_binding_plugins_with_plugins(self, mock_release_data, mocker):
        """Test _get_stage_binding_plugins with stage plugins"""
        # Mock plugin data
        mock_plugin1 = mocker.Mock()
        mock_plugin1.name = "test-plugin-1"
        mock_plugin1.config = {"key1": "value1", "key2": "value2"}

        mock_plugin2 = mocker.Mock()
        mock_plugin2.name = "test-plugin-2"
        mock_plugin2.config = {"key3": "value3"}

        mock_release_data.get_stage_plugins.return_value = [mock_plugin1, mock_plugin2]

        convertor = ServiceConvertor(mock_release_data, publish_id=123)
        result = convertor._get_stage_binding_plugins()

        # Check that plugins are created with correct names and configs
        assert "test-plugin-1" in result
        assert "test-plugin-2" in result

        plugin1 = result["test-plugin-1"]
        assert plugin1.key1 == "value1"
        assert plugin1.key2 == "value2"

        plugin2 = result["test-plugin-2"]
        assert plugin2.key3 == "value3"

    def test_get_stage_extra_plugins_not_legacy_gateway(self, mock_release_data, mocker):
        """Test _get_stage_extra_plugins with non-legacy gateway"""
        mocker.patch.object(settings, "LEGACY_INVALID_PARAMS_GATEWAY_NAMES", ["legacy-gateway"])

        convertor = ServiceConvertor(mock_release_data, publish_id=123)
        result = convertor._get_stage_extra_plugins()

        assert result == {}

    def test_get_stage_extra_plugins_legacy_gateway(self, mock_release_data, mocker):
        """Test _get_stage_extra_plugins with legacy gateway"""
        mocker.patch.object(settings, "LEGACY_INVALID_PARAMS_GATEWAY_NAMES", ["test-gateway", "other-legacy"])

        convertor = ServiceConvertor(mock_release_data, publish_id=123)
        result = convertor._get_stage_extra_plugins()

        assert "bk-legacy-invalid-params" in result
        assert len(result) == 1

    def test_get_stage_extra_plugins_empty_legacy_list(self, mock_release_data, mocker):
        """Test _get_stage_extra_plugins with empty legacy gateway list"""
        mocker.patch.object(settings, "LEGACY_INVALID_PARAMS_GATEWAY_NAMES", [])

        convertor = ServiceConvertor(mock_release_data, publish_id=123)
        result = convertor._get_stage_extra_plugins()

        assert result == {}
