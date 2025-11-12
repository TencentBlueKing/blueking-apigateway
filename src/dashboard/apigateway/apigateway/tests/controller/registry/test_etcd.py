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

from apigateway.controller.models import BaseUpstream, Labels, Service
from apigateway.controller.registry.base import Registry
from apigateway.controller.registry.etcd import EtcdRegistry


class TestEtcdRegistry:
    """Test EtcdRegistry class"""

    @pytest.fixture
    def mock_etcd_client(self, mocker):
        """Create a mock etcd client"""
        return mocker.Mock()

    def test_registry_type(self):
        """Test registry type"""
        assert EtcdRegistry.registry_type == "etcd"

    def test_initialization(self, mock_etcd_client):
        """Test EtcdRegistry initialization"""
        registry = EtcdRegistry("/test/", etcd_client=mock_etcd_client)

        assert registry.key_prefix == "/test/"
        assert registry._etcd_client == mock_etcd_client

    def test_initialization_without_client(self, mocker):
        """Test EtcdRegistry initialization without explicit client"""
        mock_get_client = mocker.patch("apigateway.controller.registry.etcd.get_etcd_client")
        mock_client = mocker.Mock()
        mock_get_client.return_value = mock_client

        registry = EtcdRegistry("/test/")

        assert registry._etcd_client == mock_client
        mock_get_client.assert_called_once()

    def test_delete_by_key(self, mock_etcd_client):
        """Test _delete_by_key method"""
        mock_etcd_client.delete.return_value = True

        registry = EtcdRegistry("/test/", etcd_client=mock_etcd_client)
        result = registry._delete_by_key("/test/service/svc-1")

        assert result is True
        mock_etcd_client.delete.assert_called_once_with("/test/service/svc-1")

    def test_apply_resource(self, mock_etcd_client, mocker):
        """Test apply_resource method"""
        labels = Labels(gateway="test", stage="prod")
        upstream = BaseUpstream()
        service = Service(
            id="service-1",
            name="test-service",
            labels=labels,
            upstream=upstream,
        )

        registry = EtcdRegistry("/test/", etcd_client=mock_etcd_client)
        result = registry.apply_resource(service)

        assert result is True
        mock_etcd_client.put.assert_called_once()

        # Verify the key and value
        call_args = mock_etcd_client.put.call_args[0]
        assert call_args[0] == "/test/service/service-1"
        # Value should be JSON string
        assert isinstance(call_args[1], str)
        data = json.loads(call_args[1])
        assert data["id"] == "service-1"

    def test_sync_resources_by_key_prefix(self, mock_etcd_client, mocker):
        """Test sync_resources_by_key_prefix method"""
        # Mock existing keys
        mock_kv = mocker.Mock()
        mock_kv.key = b"/test/service/old-service"
        mock_etcd_client.get_prefix.return_value = [(None, mock_kv)]

        labels = Labels(gateway="test", stage="prod")
        upstream = BaseUpstream()
        service = Service(
            id="service-1",
            name="test-service",
            labels=labels,
            upstream=upstream,
        )

        registry = EtcdRegistry("/test/", etcd_client=mock_etcd_client)
        failed = registry.sync_resources_by_key_prefix([service])

        assert failed == []
        # Should apply the new resource
        mock_etcd_client.put.assert_called()
        # Should delete the old resource
        mock_etcd_client.delete.assert_called_once_with("/test/service/old-service")

    def test_get_exist_keys_by_key_prefix(self, mock_etcd_client, mocker):
        """Test _get_exist_keys_by_key_prefix method"""
        mock_kv1 = mocker.Mock()
        mock_kv1.key = b"/test/service/svc-1"
        mock_kv2 = mocker.Mock()
        mock_kv2.key = b"/test/route/route-1"

        mock_etcd_client.get_prefix.return_value = [
            (None, mock_kv1),
            (None, mock_kv2),
        ]

        registry = EtcdRegistry("/test/", etcd_client=mock_etcd_client)
        keys = registry._get_exist_keys_by_key_prefix()

        assert len(keys) == 2
        assert "/test/service/svc-1" in keys
        assert "/test/route/route-1" in keys

    def test_delete_resources_by_key_prefix(self, mock_etcd_client):
        """Test delete_resources_by_key_prefix method"""
        registry = EtcdRegistry("/test/", etcd_client=mock_etcd_client)
        registry.delete_resources_by_key_prefix()

        mock_etcd_client.delete_prefix.assert_called_once_with("/test/")

    def test_iter_by_type(self, mock_etcd_client, mocker):
        """Test iter_by_type method"""
        # Mock etcd response
        service_data = {
            "id": "service-1",
            "name": "test-service",
            "labels": {"gateway": "test", "stage": "prod"},
            "upstream": {"nodes": []},
        }
        mock_etcd_client.get_prefix.return_value = [
            (json.dumps(service_data).encode(), None),
        ]

        registry = EtcdRegistry("/test/", etcd_client=mock_etcd_client)
        services = list(registry.iter_by_type(Service))

        assert len(services) == 1
        assert services[0].id == "service-1"

    def test_iter_by_type_invalid_data(self, mock_etcd_client, mocker):
        """Test iter_by_type with invalid data"""
        # Mock etcd response with invalid JSON
        mock_etcd_client.get_prefix.return_value = [
            (b"invalid-json", None),
        ]

        registry = EtcdRegistry("/test/", etcd_client=mock_etcd_client)
        services = list(registry.iter_by_type(Service))

        # Should skip invalid data
        assert len(services) == 0

    def test_etcd_registry_is_registry(self, mock_etcd_client):
        """Test that EtcdRegistry is a Registry"""
        registry = EtcdRegistry("/test/", etcd_client=mock_etcd_client)
        assert isinstance(registry, Registry)

    def test_key_prefix_with_trailing_slash(self, mock_etcd_client):
        """Test that key_prefix always ends with slash"""
        registry1 = EtcdRegistry("/test/", etcd_client=mock_etcd_client)
        assert registry1.key_prefix == "/test/"

        registry2 = EtcdRegistry("/test", etcd_client=mock_etcd_client)
        assert registry2.key_prefix == "/test/"
