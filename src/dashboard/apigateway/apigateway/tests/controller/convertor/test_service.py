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
import base64

import pytest
from django.conf import settings
from django.utils.encoding import force_bytes, force_str

from apigateway.apps.data_plane.constants import DataPlaneApisixVersionEnum
from apigateway.common.constants import DEFAULT_BACKEND_HOST_FOR_MISSING
from apigateway.controller.convertor import ServiceConvertor
from apigateway.controller.convertor.base import GatewayResourceConvertor
from apigateway.controller.convertor.constants import LABEL_KEY_APISIX_VERSION, LABEL_KEY_BACKEND_ID
from apigateway.controller.release_data import PluginData, StageBackendConfig
from apigateway.core.constants import BackendKindEnum, BackendTypeEnum, LoadBalanceTypeEnum

APISIX_VERSION_3_13 = DataPlaneApisixVersionEnum.V3_13.value
APISIX_VERSION_3_16 = DataPlaneApisixVersionEnum.V3_16.value


def _standard_backend_config(backend_id, backend_name, config):
    return StageBackendConfig(
        backend_id=backend_id,
        backend_name=backend_name,
        backend_kind=BackendKindEnum.STANDARD.value,
        backend_type=BackendTypeEnum.HTTP.value,
        config=config,
    )


def _ai_backend_config(
    backend_id=10,
    *,
    provider="openai-compatible",
    auth=None,
    options=None,
    override=None,
    model_endpoint=None,
):
    instance = {
        "name": "primary",
        "provider": provider,
        "weight": 1,
        "options": options or {"model": "gpt-4.1-mini", "temperature": 0.2},
    }
    if auth is not None:
        instance["auth"] = auth
    if override is not None:
        instance["override"] = override
    if model_endpoint is not None:
        instance["model_endpoint"] = model_endpoint
    return StageBackendConfig(
        backend_id=backend_id,
        backend_name="model-service",
        backend_kind=BackendKindEnum.AI.value,
        backend_type=BackendTypeEnum.HTTP.value,
        config={"timeout": 45, "instances": [instance]},
    )


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
        release_data.stage.vars = {}
        release_data.stage_backend_configs = {}
        release_data.get_stage_plugins.return_value = []
        release_data.jwt_private_key = "test-key"
        release_data.gateway_auth_config = {}
        return release_data

    def test_service_convertor_initialization(self, mock_release_data):
        """Test ServiceConvertor initialization"""
        convertor = ServiceConvertor(mock_release_data, publish_id=123, apisix_version=APISIX_VERSION_3_13)
        assert convertor is not None
        assert convertor._release_data == mock_release_data
        assert convertor._publish_id == 123

    def test_service_convertor_requires_apisix_version(self, mock_release_data):
        """Test ServiceConvertor requires apisix_version."""
        with pytest.raises(TypeError):
            ServiceConvertor(mock_release_data, publish_id=123)

    def test_service_convertor_is_gateway_resource_convertor(self, mock_release_data):
        """Test that ServiceConvertor is a GatewayResourceConvertor"""
        convertor = ServiceConvertor(mock_release_data, publish_id=123, apisix_version=APISIX_VERSION_3_13)
        assert isinstance(convertor, GatewayResourceConvertor)

    def test_service_labels_carry_apisix_version(self, mock_release_data):
        """ServiceConvertor labels should reflect the configured apisix_version"""
        convertor = ServiceConvertor(mock_release_data, publish_id=123, apisix_version=APISIX_VERSION_3_16)
        labels = convertor.get_labels()
        assert labels.get_label(LABEL_KEY_APISIX_VERSION) == APISIX_VERSION_3_16

    def test_service_convertor_inherits_gateway_properties(self, mock_release_data):
        """Test that ServiceConvertor inherits properties from GatewayResourceConvertor"""
        convertor = ServiceConvertor(mock_release_data, publish_id=123, apisix_version=APISIX_VERSION_3_13)

        assert convertor.gateway_id == 123
        assert convertor.gateway_name == "test-gateway"
        assert convertor.stage_id == 456
        assert convertor.stage_name == "prod"

    def test_convert_with_no_backend_configs(self, mock_release_data):
        """Test convert with no backend configs"""
        mock_release_data.stage_backend_configs = {}

        convertor = ServiceConvertor(mock_release_data, publish_id=123, apisix_version=APISIX_VERSION_3_13)
        result = convertor.convert()

        assert result == []

    def test_build_standard_service_requires_hosts(self, mock_release_data):
        convertor = ServiceConvertor(mock_release_data, publish_id=123, apisix_version=APISIX_VERSION_3_13)
        backend_config = _standard_backend_config(1, "backend-service", {"timeout": 60, "hosts": []})

        with pytest.raises(ValueError, match="backend 1 has no hosts"):
            convertor._build_standard_service(backend_config)

    def test_build_standard_service(self, mock_release_data):
        mock_release_data.stage.vars = {"domain": "example.com"}
        backend_config = _standard_backend_config(
            1,
            "backend-service",
            {
                "timeout": 30,
                "hosts": [{"scheme": "https", "host": "{env.domain}:8443", "weight": 100}],
            },
        )

        convertor = ServiceConvertor(mock_release_data, publish_id=123, apisix_version=APISIX_VERSION_3_13)
        service = convertor._build_standard_service(backend_config)

        assert service.id == "test-gateway.prod.456-1"
        assert service.name == "test-gateway.prod.backend-service"
        assert "kind" not in service.model_dump(mode="json", exclude_none=True)
        assert service.labels.get_label(LABEL_KEY_BACKEND_ID) == "1"
        assert service.plugins["bk-backend-context"].bk_backend_id == 1
        assert service.plugins["bk-backend-context"].bk_backend_name == "backend-service"
        assert (
            service.plugins["bk-backend-context"].model_dump(mode="json", exclude_none=True)["bk_backend_kind"]
            == BackendKindEnum.STANDARD.value
        )
        assert service.upstream.type.value == "roundrobin"
        assert service.upstream.scheme.value == "https"
        assert service.upstream.timeout.model_dump() == {"connect": 30, "send": 30, "read": 30}
        assert service.upstream.nodes[0].model_dump() == {"host": "example.com", "port": 8443, "weight": 100}

    def test_convert_with_revoke_flag(self, mock_release_data):
        convertor = ServiceConvertor(
            mock_release_data,
            publish_id=123,
            apisix_version=APISIX_VERSION_3_13,
            revoke_flag=True,
        )
        assert convertor.convert() == []

    @pytest.mark.parametrize(
        ("loadbalance", "expected_type"),
        [
            ("roundrobin", "roundrobin"),
            (LoadBalanceTypeEnum.WRR.value, "roundrobin"),
        ],
    )
    def test_build_standard_service_normalizes_loadbalance(self, mock_release_data, loadbalance, expected_type):
        backend_config = _standard_backend_config(
            1,
            "backend-service",
            {"loadbalance": loadbalance, "hosts": [{"scheme": "http", "host": "example.com"}]},
        )
        convertor = ServiceConvertor(mock_release_data, publish_id=123, apisix_version=APISIX_VERSION_3_13)

        service = convertor._build_standard_service(backend_config)

        assert service.upstream.type.value == expected_type
        assert service.upstream.timeout.model_dump() == {"connect": 60, "send": 60, "read": 60}
        assert service.upstream.nodes[0].model_dump() == {"host": "example.com", "port": 80, "weight": 1}

    def test_build_standard_service_with_chash(self, mock_release_data):
        backend_config = _standard_backend_config(
            1,
            "backend-service",
            {
                "loadbalance": "chash",
                "hash_on": "header",
                "key": "content-type",
                "hosts": [{"scheme": "http", "host": "example.com"}],
            },
        )
        convertor = ServiceConvertor(mock_release_data, publish_id=123, apisix_version=APISIX_VERSION_3_13)

        service = convertor._build_standard_service(backend_config)

        assert service.upstream.type.value == "chash"
        assert service.upstream.hash_on.value == "header"
        assert service.upstream.key == "content-type"

    def test_build_standard_service_uses_default_host_for_empty_host(self, mock_release_data):
        backend_config = _standard_backend_config(
            1,
            "backend-service",
            {"hosts": [{"scheme": "http", "host": ""}]},
        )
        convertor = ServiceConvertor(mock_release_data, publish_id=123, apisix_version=APISIX_VERSION_3_13)

        service = convertor._build_standard_service(backend_config)

        assert service.upstream.nodes[0].host == DEFAULT_BACKEND_HOST_FOR_MISSING

    def test_build_standard_service_rejects_unsupported_scheme(self, mock_release_data):
        backend_config = _standard_backend_config(
            1,
            "backend-service",
            {"hosts": [{"scheme": "ftp", "host": "example.com"}]},
        )
        convertor = ServiceConvertor(mock_release_data, publish_id=123, apisix_version=APISIX_VERSION_3_13)

        with pytest.raises(ValueError, match="scheme 'ftp' of host 'example.com'"):
            convertor._build_standard_service(backend_config)

    def test_convert_with_ai_backend_config(self, mock_release_data):
        mock_release_data.stage_backend_configs = {
            10: _ai_backend_config(
                auth={"header": {"Authorization": "Bearer must-not-log"}},
                override={"endpoint": "https://models.example.com/v1/chat/completions"},
                model_endpoint="https://models.example.com/v1/models",
            )
        }
        mock_release_data.get_stage_plugins.return_value = []
        mock_release_data.jwt_private_key = "test-key"
        mock_release_data.gateway_auth_config = {}

        service = ServiceConvertor(
            mock_release_data,
            publish_id=123,
            apisix_version=APISIX_VERSION_3_16,
        ).convert()[0]

        assert service.upstream is None
        assert "kind" not in service.model_dump(mode="json", exclude_none=True)
        assert service.plugins["ai-proxy"].model_dump(exclude_none=True) == {
            "provider": "openai-compatible",
            "auth": {"header": {"Authorization": "Bearer must-not-log"}},
            "options": {"model": "gpt-4.1-mini", "temperature": 0.2},
            "override": {"endpoint": "https://models.example.com/v1/chat/completions"},
            "timeout": 45000,
            "ssl_verify": True,
            "logging": {"summaries": True, "payloads": False},
        }
        assert service.plugins["bk-backend-context"].bk_backend_id == 10
        assert (
            service.plugins["bk-backend-context"].model_dump(mode="json", exclude_none=True)["bk_backend_kind"]
            == BackendKindEnum.AI.value
        )

    def test_ai_proxy_omits_override_for_builtin_provider(self, mock_release_data):
        mock_release_data.stage_backend_configs = {
            10: _ai_backend_config(
                provider="openai",
                auth={"header": {"Authorization": "Bearer must-not-log"}},
            )
        }
        mock_release_data.get_stage_plugins.return_value = []
        mock_release_data.jwt_private_key = "test-key"
        mock_release_data.gateway_auth_config = {}

        service = ServiceConvertor(
            mock_release_data,
            publish_id=123,
            apisix_version=APISIX_VERSION_3_16,
        ).convert()[0]

        assert "override" not in service.plugins["ai-proxy"].model_dump(exclude_none=True)

    def test_ai_proxy_emits_empty_auth_when_omitted(self, mock_release_data):
        mock_release_data.stage_backend_configs = {
            10: _ai_backend_config(override={"endpoint": "https://models.example.com/v1/chat/completions"})
        }
        mock_release_data.get_stage_plugins.return_value = []
        mock_release_data.jwt_private_key = "test-key"
        mock_release_data.gateway_auth_config = {}

        service = ServiceConvertor(
            mock_release_data,
            publish_id=123,
            apisix_version=APISIX_VERSION_3_16,
        ).convert()[0]

        assert service.plugins["ai-proxy"].auth == {}

    def test_ai_service_uses_ai_proxy_multi_for_multiple_instances(self, mock_release_data):
        instances = [
            {
                "name": "primary",
                "provider": "openai",
                "weight": 80,
                "auth": {"header": {"Authorization": "Bearer primary"}},
                "options": {"model": "gpt-4.1-mini"},
            },
            {
                "name": "fallback",
                "provider": "openai-compatible",
                "weight": 20,
                "auth": {"header": {"Authorization": "Bearer fallback"}},
                "options": {"model": "fallback-model"},
                "override": {"endpoint": "https://models.example.com/v1/chat/completions"},
                "model_endpoint": "https://models.example.com/v1/models",
            },
        ]
        mock_release_data.stage_backend_configs = {
            10: StageBackendConfig(
                backend_id=10,
                backend_name="model-service",
                backend_kind=BackendKindEnum.AI.value,
                backend_type=BackendTypeEnum.HTTP.value,
                config={
                    "timeout": 60,
                    "instances": instances,
                    "balancer": {"algorithm": "roundrobin"},
                    "fallback_strategy": ["http_429", "http_5xx"],
                },
            )
        }

        service = ServiceConvertor(
            mock_release_data,
            publish_id=123,
            apisix_version=APISIX_VERSION_3_16,
        ).convert()[0]

        assert "ai-proxy" not in service.plugins
        expected_instances = [dict(instance) for instance in instances]
        expected_instances[1].pop("model_endpoint")
        assert service.plugins["ai-proxy-multi"].model_dump(exclude_none=True) == {
            "instances": expected_instances,
            "balancer": {"algorithm": "roundrobin"},
            "fallback_strategy": ["http_429", "http_5xx"],
            "timeout": 60000,
            "ssl_verify": True,
            "logging": {"summaries": True, "payloads": False},
        }

    def test_standard_and_ai_services_use_explicit_plugin_profiles(self, mock_release_data):
        mock_release_data.stage_backend_configs = {
            1: _standard_backend_config(
                1,
                "standard-service",
                {"timeout": 60, "hosts": [{"scheme": "http", "host": "example.com", "weight": 100}]},
            ),
            10: _ai_backend_config(
                auth={"header": {"Authorization": "Bearer must-not-log"}},
                override={"endpoint": "https://models.example.com/v1/chat/completions"},
            ),
        }
        mock_release_data.get_stage_plugins.return_value = []
        mock_release_data.jwt_private_key = "test-key"
        mock_release_data.gateway_auth_config = {}

        standard_service, ai_service = ServiceConvertor(
            mock_release_data,
            publish_id=123,
            apisix_version=APISIX_VERSION_3_16,
        ).convert()

        for plugin_name in ("bk-jwt", "bk-break-recursive-call", "bk-log-context", "bk-error-wrapper"):
            assert plugin_name in standard_service.plugins
            assert plugin_name in ai_service.plugins

        assert standard_service.upstream is not None
        assert "ai-proxy" not in standard_service.plugins
        assert ai_service.upstream is None
        assert "ai-proxy" in ai_service.plugins

    def test_ai_service_filters_incompatible_stage_plugins(self, mock_release_data, caplog):
        mock_release_data.stage_backend_configs = {
            1: _standard_backend_config(
                1,
                "standard-service",
                {"timeout": 60, "hosts": [{"scheme": "http", "host": "example.com", "weight": 100}]},
            ),
            10: _ai_backend_config(
                auth={"header": {"Authorization": "Bearer must-not-log"}},
                override={"endpoint": "https://models.example.com/v1/chat/completions"},
            ),
        }
        mock_release_data.get_stage_plugins.return_value = [
            PluginData("bk-cors", {}, "stage"),
            PluginData("bk-header-rewrite", {}, "stage"),
            PluginData("ai-rate-limiting", {}, "stage"),
            PluginData("response-rewrite", {"body": "must-not-log"}, "stage"),
        ]
        mock_release_data.jwt_private_key = "test-key"
        mock_release_data.gateway_auth_config = {}

        standard_service, ai_service = ServiceConvertor(
            mock_release_data,
            publish_id=123,
            apisix_version=APISIX_VERSION_3_16,
        ).convert()

        assert "bk-cors" in standard_service.plugins
        assert "bk-cors" in ai_service.plugins
        assert "bk-stage-header-rewrite" in standard_service.plugins
        assert "bk-stage-header-rewrite" in ai_service.plugins
        assert "ai-rate-limiting" in standard_service.plugins
        assert "ai-rate-limiting" in ai_service.plugins
        assert "response-rewrite" in standard_service.plugins
        assert "response-rewrite" not in ai_service.plugins
        assert "gateway_id=123" in caplog.text
        assert "stage_id=456" in caplog.text
        assert "response-rewrite" in caplog.text
        assert "must-not-log" not in caplog.text

    def test_controller_generated_ai_proxy_takes_precedence(self, mock_release_data):
        mock_release_data.stage_backend_configs = {
            10: _ai_backend_config(
                auth={"header": {"Authorization": "Bearer must-not-log"}},
                override={"endpoint": "https://models.example.com/v1/chat/completions"},
            )
        }
        mock_release_data.get_stage_plugins.return_value = [
            PluginData("ai-proxy", {"provider": "must-not-win"}, "stage")
        ]
        mock_release_data.jwt_private_key = "test-key"
        mock_release_data.gateway_auth_config = {}

        service = ServiceConvertor(
            mock_release_data,
            publish_id=123,
            apisix_version=APISIX_VERSION_3_16,
        ).convert()[0]

        assert service.plugins["ai-proxy"].provider == "openai-compatible"

    def test_ai_service_uses_default_file_logger_without_log_format(self, mock_release_data):
        mock_release_data.stage_backend_configs = {10: _ai_backend_config()}

        service = ServiceConvertor(
            mock_release_data,
            publish_id=123,
            apisix_version=APISIX_VERSION_3_16,
        ).convert()[0]

        assert service.plugins["file-logger"].model_dump(exclude_none=True) == {"path": "logs/access.log"}

    def test_convert_with_multiple_backends(self, mock_release_data):
        """Test convert with multiple backend configs"""
        mock_release_data.stage_backend_configs = {
            1: _standard_backend_config(
                1,
                "backend-1",
                {"timeout": 60, "hosts": [{"scheme": "http", "host": "example1.com", "weight": 100}]},
            ),
            2: _standard_backend_config(
                2,
                "backend-2",
                {"timeout": 30, "hosts": [{"scheme": "http", "host": "example2.com", "weight": 50}]},
            ),
        }
        mock_release_data.get_stage_plugins.return_value = []
        mock_release_data.jwt_private_key = "test-key"
        mock_release_data.gateway_auth_config = {}

        convertor = ServiceConvertor(mock_release_data, publish_id=123, apisix_version=APISIX_VERSION_3_13)
        result = convertor.convert()

        assert len(result) == 2
        assert result[0].id == "test-gateway.prod.456-1"
        assert result[1].id == "test-gateway.prod.456-2"

    def test_build_service_plugins(self, mock_release_data, mocker):
        """Test _build_service_plugins method"""
        mock_common_plugins = {"plugin1": mocker.Mock()}
        mock_binding_plugins = {"plugin3": mocker.Mock()}
        mock_extra_plugins = {"plugin4": mocker.Mock()}

        mocker.patch.object(ServiceConvertor, "_get_common_default_plugins", return_value=mock_common_plugins)
        mocker.patch.object(ServiceConvertor, "_get_stage_binding_plugins", return_value=mock_binding_plugins)
        mocker.patch.object(ServiceConvertor, "_get_stage_extra_plugins", return_value=mock_extra_plugins)

        convertor = ServiceConvertor(mock_release_data, publish_id=123, apisix_version=APISIX_VERSION_3_13)
        result = convertor._build_service_plugins(BackendKindEnum.STANDARD.value)

        assert len(result) == 3
        expected_plugins = {
            **mock_common_plugins,
            **mock_binding_plugins,
            **mock_extra_plugins,
        }
        assert result == expected_plugins

    def test_get_common_default_plugins_basic(self, mock_release_data, mocker):
        """Test common and standard default plugins with basic configuration"""
        # Mock settings
        mocker.patch.object(settings, "GATEWAY_CONCURRENCY_LIMIT_ENABLED", False)
        mocker.patch.object(settings, "ENABLE_MULTI_TENANT_MODE", False)

        # Mock release data properties
        mock_release_data.jwt_private_key = "test-jwt-key"
        mock_release_data.gateway_auth_config = {"auth": "config"}

        convertor = ServiceConvertor(mock_release_data, publish_id=123, apisix_version=APISIX_VERSION_3_13)
        result = convertor._get_common_default_plugins()

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

    def test_get_common_default_plugins_with_concurrency_limit(self, mock_release_data, mocker):
        """Test common default plugins with concurrency limit enabled"""
        mocker.patch.object(settings, "GATEWAY_CONCURRENCY_LIMIT_ENABLED", True)
        mocker.patch.object(settings, "ENABLE_MULTI_TENANT_MODE", False)

        mock_release_data.jwt_private_key = "test-jwt-key"
        mock_release_data.gateway_auth_config = {}

        convertor = ServiceConvertor(mock_release_data, publish_id=123, apisix_version=APISIX_VERSION_3_13)
        result = convertor._get_common_default_plugins()

        # Check that concurrency limit plugin is present
        assert "bk-concurrency-limit" in result

    def test_get_common_default_plugins_multi_tenant_mode(self, mock_release_data, mocker):
        """Test common default plugins with multi-tenant mode enabled"""
        mocker.patch.object(settings, "GATEWAY_CONCURRENCY_LIMIT_ENABLED", False)
        mocker.patch.object(settings, "ENABLE_MULTI_TENANT_MODE", True)

        # Mock gateway with tenant properties
        mock_release_data.gateway.tenant_mode = "shared"
        mock_release_data.gateway.tenant_id = "tenant-123"
        mock_release_data.jwt_private_key = "test-jwt-key"
        mock_release_data.gateway_auth_config = {}

        convertor = ServiceConvertor(mock_release_data, publish_id=123, apisix_version=APISIX_VERSION_3_13)
        result = convertor._get_common_default_plugins()

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

        convertor = ServiceConvertor(mock_release_data, publish_id=123, apisix_version=APISIX_VERSION_3_13)
        result = convertor._get_stage_binding_plugins(BackendKindEnum.STANDARD.value)

        assert result == {}

    def test_get_stage_binding_plugins_with_plugins(self, mock_release_data, mocker):
        """Test _get_stage_binding_plugins with stage plugins"""
        # Mock plugin data
        mock_plugin1 = mocker.Mock()
        mock_plugin1.name = "test-plugin-1"
        mock_plugin1.type_code = "test-plugin-1"
        mock_plugin1.config = {"key1": "value1", "key2": "value2"}

        mock_plugin2 = mocker.Mock()
        mock_plugin2.name = "test-plugin-2"
        mock_plugin2.type_code = "test-plugin-2"
        mock_plugin2.config = {"key3": "value3"}

        mock_release_data.get_stage_plugins.return_value = [mock_plugin1, mock_plugin2]

        convertor = ServiceConvertor(mock_release_data, publish_id=123, apisix_version=APISIX_VERSION_3_13)
        result = convertor._get_stage_binding_plugins(BackendKindEnum.STANDARD.value)

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

        convertor = ServiceConvertor(mock_release_data, publish_id=123, apisix_version=APISIX_VERSION_3_13)
        result = convertor._get_stage_extra_plugins(BackendKindEnum.STANDARD.value)

        assert result == {}

    def test_get_stage_extra_plugins_legacy_gateway(self, mock_release_data, mocker):
        """Test _get_stage_extra_plugins with legacy gateway"""
        mocker.patch.object(settings, "LEGACY_INVALID_PARAMS_GATEWAY_NAMES", ["test-gateway", "other-legacy"])

        convertor = ServiceConvertor(mock_release_data, publish_id=123, apisix_version=APISIX_VERSION_3_13)
        result = convertor._get_stage_extra_plugins(BackendKindEnum.STANDARD.value)

        assert "bk-legacy-invalid-params" in result
        assert len(result) == 1

    def test_get_stage_extra_plugins_empty_legacy_list(self, mock_release_data, mocker):
        """Test _get_stage_extra_plugins with empty legacy gateway list"""
        mocker.patch.object(settings, "LEGACY_INVALID_PARAMS_GATEWAY_NAMES", [])

        convertor = ServiceConvertor(mock_release_data, publish_id=123, apisix_version=APISIX_VERSION_3_13)
        result = convertor._get_stage_extra_plugins(BackendKindEnum.STANDARD.value)

        assert result == {}

    def test_get_stage_extra_plugins_omits_legacy_plugin_for_ai(self, mock_release_data, mocker):
        mocker.patch.object(settings, "LEGACY_INVALID_PARAMS_GATEWAY_NAMES", ["test-gateway"])

        convertor = ServiceConvertor(mock_release_data, publish_id=123, apisix_version=APISIX_VERSION_3_16)

        assert convertor._get_stage_extra_plugins(BackendKindEnum.AI.value) == {}
