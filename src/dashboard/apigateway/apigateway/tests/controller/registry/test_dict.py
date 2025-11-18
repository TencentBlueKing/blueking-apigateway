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

from apigateway.controller.models.base import BaseUpstream, Labels, Route, Service
from apigateway.controller.registry.dict import DictRegistry


class TestDictRegistry:
    """Test DictRegistry class"""

    @pytest.fixture
    def registry(self):
        """Create a test registry"""
        return DictRegistry("/test/")

    @pytest.fixture
    def sample_service(self):
        """Create a sample service"""
        labels = Labels(gateway="test-gateway", stage="prod")
        upstream = BaseUpstream()
        return Service(
            id="service-1",
            name="test-service",
            labels=labels,
            upstream=upstream,
        )

    def test_registry_type(self):
        """Test registry type"""
        assert DictRegistry.registry_type == "dict"

    def test_initialization(self):
        """Test DictRegistry initialization"""
        registry = DictRegistry("/test/")
        assert registry.key_prefix == "/test/"
        assert isinstance(registry._registry_dict, dict)
        assert len(registry._registry_dict) == 0

    def test_initialization_empty_prefix(self):
        """Test DictRegistry initialization with empty prefix"""
        registry = DictRegistry()
        assert registry.key_prefix == "/"

    def test_apply_resource(self, registry, sample_service):
        """Test apply_resource method"""
        result = registry.apply_resource(sample_service)
        assert result is True

        # Check that resource is stored
        key = registry._get_key("service", "service-1")
        assert key in registry._registry_dict
        assert registry._registry_dict[key].id == "service-1"

    def test_apply_resource_creates_copy(self, registry, sample_service):
        """Test that apply_resource creates a deep copy"""
        registry.apply_resource(sample_service)

        key = registry._get_key("service", "service-1")
        stored_resource = registry._registry_dict[key]

        # Modify original
        sample_service.name = "modified-name"

        # Stored copy should not be affected
        assert stored_resource.name == "test-service"

    def test_apply_resource_overwrites_existing(self, registry):
        """Test that apply_resource overwrites existing resource"""
        labels = Labels(gateway="test", stage="prod")
        upstream = BaseUpstream()

        service1 = Service(id="service-1", name="first", labels=labels, upstream=upstream)
        registry.apply_resource(service1)

        service2 = Service(id="service-1", name="second", labels=labels, upstream=upstream)
        registry.apply_resource(service2)

        key = registry._get_key("service", "service-1")
        assert registry._registry_dict[key].name == "second"

    def test_sync_resources_by_key_prefix(self, registry):
        """Test sync_resources_by_key_prefix method"""
        labels = Labels(gateway="test", stage="prod")
        upstream = BaseUpstream()

        services = [
            Service(id="service-1", name="svc-1", labels=labels, upstream=upstream),
            Service(id="service-2", name="svc-2", labels=labels, upstream=upstream),
        ]

        failed = registry.sync_resources_by_key_prefix(services)

        assert failed == []
        assert len(registry._registry_dict) == 2

    def test_sync_resources_clears_existing(self, registry, sample_service):
        """Test that sync_resources clears existing resources"""
        # Add initial resource
        registry.apply_resource(sample_service)
        assert len(registry._registry_dict) == 1

        # Sync with empty list
        registry.sync_resources_by_key_prefix([])

        assert len(registry._registry_dict) == 0

    def test_delete_resources_by_key_prefix(self, registry, sample_service):
        """Test delete_resources_by_key_prefix method"""
        registry.apply_resource(sample_service)
        assert len(registry._registry_dict) == 1

        registry.delete_resources_by_key_prefix()

        assert len(registry._registry_dict) == 0

    def test_iter_by_type(self, registry):
        """Test iter_by_type method"""
        labels = Labels(gateway="test", stage="prod")
        upstream = BaseUpstream()

        services = [
            Service(id="service-1", name="svc-1", labels=labels, upstream=upstream),
            Service(id="service-2", name="svc-2", labels=labels, upstream=upstream),
        ]

        for svc in services:
            registry.apply_resource(svc)

        # Iterate and collect
        result = list(registry.iter_by_type(Service))

        assert len(result) == 2
        assert all(isinstance(r, Service) for r in result)

    def test_iter_by_type_returns_copy(self, registry, sample_service):
        """Test that iter_by_type returns deep copies"""
        registry.apply_resource(sample_service)

        result = list(registry.iter_by_type(Service))
        assert len(result) == 1

        # Modify returned resource
        result[0].name = "modified"

        # Original should not be affected
        key = registry._get_key("service", "service-1")
        assert registry._registry_dict[key].name == "test-service"

    def test_iter_by_type_empty(self, registry):
        """Test iter_by_type with no matching resources"""
        result = list(registry.iter_by_type(Service))
        assert len(result) == 0

    def test_get_exist_keys_by_key_prefix(self, registry, sample_service):
        """Test _get_exist_keys_by_key_prefix method"""
        registry.apply_resource(sample_service)

        keys = registry._get_exist_keys_by_key_prefix()

        assert isinstance(keys, dict)
        assert len(keys) == 1

        key = registry._get_key("service", "service-1")
        assert key in keys
        assert keys[key] is True

    def test_multiple_resource_types(self, registry):
        """Test registry with multiple resource types"""
        labels = Labels(gateway="test", stage="prod")
        upstream = BaseUpstream()

        service = Service(id="service-1", name="svc", labels=labels, upstream=upstream)
        route = Route(id="route-1", name="rt", labels=labels)

        registry.apply_resource(service)
        registry.apply_resource(route)

        assert len(registry._registry_dict) == 2

        # Check services
        services = list(registry.iter_by_type(Service))
        assert len(services) == 1

        # Check routes
        routes = list(registry.iter_by_type(Route))
        assert len(routes) == 1

    def test_key_prefix_isolation(self):
        """Test that key prefix provides isolation"""
        registry1 = DictRegistry("/gateway1/")
        registry2 = DictRegistry("/gateway2/")

        labels = Labels(gateway="test", stage="prod")
        upstream = BaseUpstream()
        service = Service(id="service-1", name="svc", labels=labels, upstream=upstream)

        registry1.apply_resource(service)

        # registry2 should have different keys
        assert len(registry1._registry_dict) == 1
        assert len(registry2._registry_dict) == 0
