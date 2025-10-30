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
from pydantic import ValidationError

from apigateway.controller.models.base import (
    SSL,
    ActiveCheck,
    ActiveHealthy,
    ActiveUnhealthy,
    BaseUpstream,
    Check,
    Labels,
    Node,
    PassiveCheck,
    PassiveHealthy,
    PassiveUnhealthy,
    Plugin,
    PluginMetadata,
    Proto,
    Route,
    Service,
    SSLClient,
    Timeout,
    Tls,
)
from apigateway.controller.models.constants import (
    CheckActiveTypeEnum,
    HttpMethodEnum,
    UpstreamPassHostEnum,
    UpstreamSchemeEnum,
    UpstreamTypeEnum,
)


class TestLabels:
    """Test Labels model"""

    def test_labels_creation(self):
        """Test creating labels"""
        labels = Labels(gateway="test-gateway", stage="prod")
        assert labels.gateway == "test-gateway"
        assert labels.stage == "prod"

    def test_labels_converts_to_string(self):
        """Test that labels convert all values to strings"""
        labels = Labels(id=123, count=456)
        assert labels.id == "123"
        assert labels.count == "456"

    def test_labels_add_label(self):
        """Test adding a label dynamically"""
        labels = Labels(gateway="test-gateway")
        labels.add_label("version", "v1")
        assert labels.version == "v1"

    def test_labels_get_label_with_default(self):
        """Test getting a label with default value"""
        labels = Labels(gateway="test-gateway")
        assert labels.get_label("missing", "default") == "default"
        assert labels.get_label("missing") is None

    def test_labels_get_existing_label(self):
        """Test getting an existing label"""
        labels = Labels(gateway="test-gateway", stage="prod")
        assert labels.get_label("gateway") == "test-gateway"
        assert labels.get_label("stage") == "prod"


class TestNode:
    """Test Node model"""

    def test_node_creation(self):
        """Test creating a node"""
        node = Node(host="example.com", port=8080, weight=100)
        assert node.host == "example.com"
        assert node.port == 8080
        assert node.weight == 100

    def test_node_creation_with_invalid_host(self):
        """Test creating a node with invalid host"""
        with pytest.raises(ValidationError):
            Node(host="", port=8080, weight=100)

    def test_node_default_values(self):
        """Test node default values"""
        node = Node(host="example.com", port=80)
        assert node.weight == 1  # Default weight

    def test_node_invalid_port(self):
        """Test node with invalid port"""
        with pytest.raises(ValidationError):
            Node(host="example.com", port=0)  # Port should be >= 1

        with pytest.raises(ValidationError):
            Node(host="example.com", port=70000)  # Port should be <= 65535

    def test_node_invalid_weight(self):
        """Test node with invalid weight"""
        with pytest.raises(ValidationError):
            Node(host="example.com", port=80, weight=0)  # Weight should be > 0


class TestTimeout:
    """Test Timeout model"""

    def test_timeout_creation(self):
        """Test creating a timeout"""
        timeout = Timeout(connect=10, send=20, read=30)
        assert timeout.connect == 10
        assert timeout.send == 20
        assert timeout.read == 30

    def test_timeout_default_values(self):
        """Test timeout default values"""
        timeout = Timeout()
        assert timeout.connect == 60
        assert timeout.send == 60
        assert timeout.read == 60

    def test_timeout_invalid_values(self):
        """Test timeout with invalid values"""
        with pytest.raises(ValidationError):
            Timeout(connect=0)  # Should be > 0

        with pytest.raises(ValidationError):
            Timeout(send=-1)  # Should be > 0


class TestPlugin:
    """Test Plugin model"""

    def test_plugin_creation(self):
        """Test creating a plugin"""
        plugin = Plugin()
        assert plugin is not None

    def test_plugin_with_data(self):
        """Test creating a plugin with data"""
        plugin = Plugin(key="value", count=123)
        assert plugin.key == "value"
        assert plugin.count == 123


class TestHealthyModels:
    """Test healthy/unhealthy models"""

    def test_passive_healthy_creation(self):
        """Test creating passive healthy"""
        healthy = PassiveHealthy(http_statuses=[200, 201], successes=3)
        assert healthy.http_statuses == [200, 201]
        assert healthy.successes == 3

    def test_active_healthy_creation(self):
        """Test creating active healthy"""
        healthy = ActiveHealthy(http_statuses=[200], successes=2, interval=10)
        assert healthy.http_statuses == [200]
        assert healthy.successes == 2
        assert healthy.interval == 10

    def test_passive_unhealthy_creation(self):
        """Test creating passive unhealthy"""
        unhealthy = PassiveUnhealthy(
            http_statuses=[500, 502],
            http_failures=3,
            tcp_failures=2,
            timeouts=5,
        )
        assert unhealthy.http_statuses == [500, 502]
        assert unhealthy.http_failures == 3
        assert unhealthy.tcp_failures == 2
        assert unhealthy.timeouts == 5

    def test_active_unhealthy_creation(self):
        """Test creating active unhealthy"""
        unhealthy = ActiveUnhealthy(http_failures=3, interval=10)
        assert unhealthy.http_failures == 3
        assert unhealthy.interval == 10


class TestActiveCheck:
    """Test ActiveCheck model"""

    def test_active_check_creation(self):
        """Test creating active check"""
        check = ActiveCheck(
            type=CheckActiveTypeEnum.HTTP,
            timeout=5,
            http_path="/health",
            host="example.com",
        )
        assert check.type == CheckActiveTypeEnum.HTTP
        assert check.timeout == 5
        assert check.http_path == "/health"
        assert check.host == "example.com"

    def test_active_check_default_type(self):
        """Test active check default type"""
        check = ActiveCheck()
        assert check.type == CheckActiveTypeEnum.HTTP


class TestPassiveCheck:
    """Test PassiveCheck model"""

    def test_passive_check_creation(self):
        """Test creating passive check"""
        healthy = PassiveHealthy(http_statuses=[200], successes=2)
        check = PassiveCheck(healthy=healthy)
        assert check.healthy == healthy


class TestCheck:
    """Test Check model"""

    def test_check_with_active(self):
        """Test check with active check"""
        active = ActiveCheck()
        check = Check(active=active)
        assert check.active == active
        assert check.passive is None

    def test_check_with_passive(self):
        """Test check with passive check"""
        passive = PassiveCheck()
        check = Check(passive=passive)
        assert check.passive == passive
        assert check.active is None

    def test_check_requires_active_or_passive(self):
        """Test that check requires either active or passive"""
        with pytest.raises(ValidationError) as exc_info:
            Check()
        assert "either active or passive must be set" in str(exc_info.value)


class TestTls:
    """Test Tls model"""

    def test_tls_with_cert_and_key(self):
        """Test TLS with cert and key"""
        tls = Tls(cert="cert-data", key="key-data")
        assert tls.cert == "cert-data"
        assert tls.key == "key-data"

    def test_tls_with_client_cert_id(self):
        """Test TLS with client cert ID"""
        tls = Tls(client_cert_id="client-cert-123")
        assert tls.client_cert_id == "client-cert-123"


class TestBaseUpstream:
    """Test BaseUpstream model"""

    def test_upstream_creation(self):
        """Test creating an upstream"""
        node = Node(host="example.com", port=80)
        upstream = BaseUpstream(nodes=[node])
        assert upstream.type == UpstreamTypeEnum.ROUNDROBIN
        assert len(upstream.nodes) == 1
        assert upstream.nodes[0].host == "example.com"

    def test_upstream_default_values(self):
        """Test upstream default values"""
        upstream = BaseUpstream()
        assert upstream.type == UpstreamTypeEnum.ROUNDROBIN
        assert upstream.scheme == UpstreamSchemeEnum.HTTP
        assert upstream.pass_host == UpstreamPassHostEnum.NODE
        assert upstream.nodes == []

    def test_upstream_with_timeout(self):
        """Test upstream with timeout"""
        timeout = Timeout(connect=5, send=5, read=5)
        upstream = BaseUpstream(timeout=timeout)
        assert upstream.timeout == timeout


class TestSSLClient:
    """Test SSLClient model"""

    def test_ssl_client_creation(self):
        """Test creating SSL client"""
        # CA requires at least 128 characters
        ca_data = "x" * 128
        ssl_client = SSLClient(ca=ca_data, depth=2)
        assert ssl_client.ca == ca_data
        assert ssl_client.depth == 2


class TestService:
    """Test Service model"""

    def test_service_creation(self):
        """Test creating a service"""
        labels = Labels(gateway="test-gateway", stage="prod")
        node = Node(host="example.com", port=80)
        upstream = BaseUpstream(nodes=[node])

        service = Service(
            id="service-1",
            name="test-service",
            labels=labels,
            upstream=upstream,
        )

        assert service.id == "service-1"
        assert service.name == "test-service"
        assert service.kind == "service"
        assert service.labels == labels
        assert service.upstream == upstream

    def test_service_with_plugins(self):
        """Test service with plugins"""
        labels = Labels(gateway="test-gateway")
        upstream = BaseUpstream()
        plugin = Plugin(key="value")

        service = Service(
            id="service-1",
            name="test-service",
            labels=labels,
            upstream=upstream,
            plugins={"test-plugin": plugin},
        )

        assert "test-plugin" in service.plugins
        assert service.plugins["test-plugin"] == plugin


class TestRoute:
    """Test Route model"""

    def test_route_creation(self):
        """Test creating a route"""
        labels = Labels(gateway="test-gateway", stage="prod")
        route = Route(
            id="route-1",
            name="test-route",
            labels=labels,
            uris=["/api/test"],
            methods=[HttpMethodEnum.GET, HttpMethodEnum.POST],
        )

        assert route.id == "route-1"
        assert route.name == "test-route"
        assert route.kind == "route"
        assert route.uris == ["/api/test"]
        assert HttpMethodEnum.GET in route.methods

    def test_route_with_service_id(self):
        """Test route with service_id"""
        labels = Labels(gateway="test-gateway")
        route = Route(
            id="route-1",
            name="test-route",
            labels=labels,
            service_id="service-1",
        )

        assert route.service_id == "service-1"

    def test_route_with_priority(self):
        """Test route with priority"""
        labels = Labels(gateway="test-gateway")
        route = Route(
            id="route-1",
            name="test-route",
            labels=labels,
            priority=100,
        )

        assert route.priority == 100


class TestSSL:
    """Test SSL model"""

    def test_ssl_creation(self):
        """Test creating SSL"""
        labels = Labels(gateway="test-gateway")
        # Create long enough cert and key to pass validation (min 128 chars)
        cert = "x" * 128
        key = "y" * 128

        ssl = SSL(
            id="ssl-1",
            labels=labels,
            cert=cert,
            key=key,
        )

        assert ssl.id == "ssl-1"
        assert ssl.kind == "ssl"
        assert ssl.cert == cert
        assert ssl.key == key


class TestProto:
    """Test Proto model"""

    def test_proto_creation(self):
        """Test creating proto"""
        labels = Labels(gateway="test-gateway")
        proto = Proto(
            id="proto-1",
            labels=labels,
            content="proto-content",
            name="test-proto",
        )

        assert proto.id == "proto-1"
        assert proto.kind == "proto"
        assert proto.content == "proto-content"
        assert proto.name == "test-proto"


class TestPluginMetadata:
    """Test PluginMetadata model"""

    def test_plugin_metadata_creation(self):
        """Test creating plugin metadata"""
        metadata = PluginMetadata(
            id="plugin-metadata-1",
            config={"key": "value"},
        )

        assert metadata.id == "plugin-metadata-1"
        assert metadata.kind == "plugin_metadata"
        assert metadata.config == {"key": "value"}


class TestApisixModelValidation:
    """Test Apisix model ID validation"""

    def test_valid_id_patterns(self):
        """Test valid ID patterns"""
        labels = Labels(gateway="test")
        upstream = BaseUpstream()

        # Test various valid patterns
        valid_ids = ["service-1", "test_service", "service.v1", "service-123_test.v2"]

        for valid_id in valid_ids:
            service = Service(id=valid_id, name="test", labels=labels, upstream=upstream)
            assert service.id == valid_id

    def test_invalid_id_too_long(self):
        """Test ID that is too long"""
        labels = Labels(gateway="test")
        upstream = BaseUpstream()

        with pytest.raises(ValidationError):
            Service(id="x" * 65, name="test", labels=labels, upstream=upstream)  # Max is 64

    def test_invalid_id_empty(self):
        """Test empty ID"""
        labels = Labels(gateway="test")
        upstream = BaseUpstream()

        with pytest.raises(ValidationError):
            Service(id="", name="test", labels=labels, upstream=upstream)

    def test_invalid_id_special_chars(self):
        """Test ID with invalid special characters"""
        labels = Labels(gateway="test")
        upstream = BaseUpstream()

        with pytest.raises(ValidationError):
            Service(id="service@123", name="test", labels=labels, upstream=upstream)
