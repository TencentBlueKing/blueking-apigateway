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

import pytest

from apigateway.controller.constants import DELETE_PUBLISH_ID
from apigateway.controller.models import BaseUpstream, BkRelease, Labels, Service
from apigateway.controller.registry.base import Registry
from apigateway.controller.registry.etcd import EtcdRegistry
from apigateway.tests.controller.fake_etcd import (
    FakeEtcdClient,
    get_delete_ranges,
    get_put_keys,
    in_range,
    ranges_overlap,
)


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

    def test_replace_resources_by_key_prefix_atomically_rejects_unsuccessful_transaction(self, mock_etcd_client):
        mock_etcd_client.transaction.return_value = (False, [])

        with pytest.raises(RuntimeError, match="failed to atomically replace"):
            EtcdRegistry("/prefix/", etcd_client=mock_etcd_client).replace_resources_by_key_prefix_atomically([])

    def test_replace_resources_by_key_prefix_atomically_propagates_client_error(self, mock_etcd_client):
        mock_etcd_client.transaction.side_effect = TimeoutError("etcd timeout")

        with pytest.raises(TimeoutError, match="etcd timeout"):
            EtcdRegistry("/prefix/", etcd_client=mock_etcd_client).replace_resources_by_key_prefix_atomically([])


def make_delete_release(gateway_name="gateway", stage_name="prod", apisix_version="3.13"):
    return BkRelease(
        id=f"bk.release.{gateway_name}.{stage_name}",
        publish_id=DELETE_PUBLISH_ID,
        publish_time="2026-08-06 11:00:00",
        apisix_version=apisix_version,
        resource_version="orphan-cleanup",
        labels=Labels(
            **{
                "gateway.bk.tencent.com/gateway": gateway_name,
                "gateway.bk.tencent.com/stage": stage_name,
                "gateway.bk.tencent.com/publish-id": DELETE_PUBLISH_ID,
                "gateway.bk.tencent.com/apisix-version": apisix_version,
            }
        ),
    )


def make_service(service_id):
    return Service(
        id=service_id,
        name=service_id,
        labels=Labels(gateway="test", stage="prod"),
        upstream=BaseUpstream(),
    )


class TestEtcdRegistryAtomicReplace:
    """真实 etcd 拒绝同一事务内 PUT key 落在 DELETE range 内，这里锁定安全的 range 切分"""

    @pytest.fixture
    def mock_etcd_client(self, mocker):
        client = mocker.Mock()
        client.transaction.return_value = (True, [])
        return client

    def test_builds_gap_delete_ranges_around_sorted_put_keys(self, mock_etcd_client):
        mock_etcd_client.transactions.delete.side_effect = ["delete-0", "delete-1", "delete-2"]
        mock_etcd_client.transactions.put.side_effect = ["put-0", "put-1"]

        EtcdRegistry("/prefix/", etcd_client=mock_etcd_client).replace_resources_by_key_prefix_atomically(
            [make_service("svc-b"), make_service("svc-a")]
        )

        assert [(call.args, call.kwargs) for call in mock_etcd_client.transactions.delete.call_args_list] == [
            ((b"/prefix/",), {"range_end": b"/prefix/service/svc-a"}),
            ((b"/prefix/service/svc-a\x00",), {"range_end": b"/prefix/service/svc-b"}),
            ((b"/prefix/service/svc-b\x00",), {"range_end": b"/prefix0"}),
        ]
        assert [call.args[0] for call in mock_etcd_client.transactions.put.call_args_list] == [
            "/prefix/service/svc-a",
            "/prefix/service/svc-b",
        ]
        mock_etcd_client.transaction.assert_called_once_with(
            compare=[],
            success=["delete-0", "delete-1", "delete-2", "put-0", "put-1"],
            failure=[],
        )

    def test_builds_single_tombstone_gap_ranges(self, mock_etcd_client):
        mock_etcd_client.transactions.delete.side_effect = ["delete-0", "delete-1"]
        mock_etcd_client.transactions.put.side_effect = ["put-0"]
        release = make_delete_release()

        EtcdRegistry("/prefix/", etcd_client=mock_etcd_client).replace_resources_by_key_prefix_atomically([release])

        tombstone_key = "/prefix/_bk_release/bk.release.gateway.prod"
        assert [(call.args, call.kwargs) for call in mock_etcd_client.transactions.delete.call_args_list] == [
            ((b"/prefix/",), {"range_end": tombstone_key.encode()}),
            ((tombstone_key.encode() + b"\x00",), {"range_end": b"/prefix0"}),
        ]
        put_args = mock_etcd_client.transactions.put.call_args.args
        assert put_args[0] == tombstone_key
        assert json.loads(put_args[1])["publish_id"] == DELETE_PUBLISH_ID

    def test_deletes_whole_prefix_range_when_no_resources(self, mock_etcd_client):
        mock_etcd_client.transactions.delete.side_effect = ["delete-0"]

        EtcdRegistry("/prefix/", etcd_client=mock_etcd_client).replace_resources_by_key_prefix_atomically([])

        assert [(call.args, call.kwargs) for call in mock_etcd_client.transactions.delete.call_args_list] == [
            ((b"/prefix/",), {"range_end": b"/prefix0"})
        ]
        mock_etcd_client.transactions.put.assert_not_called()
        mock_etcd_client.transaction.assert_called_once_with(compare=[], success=["delete-0"], failure=[])

    def test_transaction_satisfies_etcd_duplicate_key_rules(self):
        fake_client = FakeEtcdClient(
            {
                "/prefix/route/route-1": "route-1-value",
                "/prefix/service/svc-1": "svc-1-value",
                "/prefix/_bk_release/bk.release.gateway.prod": "stale-release-value",
            }
        )

        EtcdRegistry("/prefix/", etcd_client=fake_client).replace_resources_by_key_prefix_atomically(
            [make_delete_release()]
        )

        ops = fake_client.transaction_ops[-1]
        delete_ranges = get_delete_ranges(ops)
        put_keys = get_put_keys(ops)
        assert put_keys == [b"/prefix/_bk_release/bk.release.gateway.prod"]
        assert not [(start, end) for start, end in delete_ranges for key in put_keys if in_range(key, start, end)]
        assert not [
            (first, second)
            for index, first in enumerate(delete_ranges)
            for second in delete_ranges[index + 1 :]
            if ranges_overlap(first, second)
        ]
        assert fake_client.keys == ["/prefix/_bk_release/bk.release.gateway.prod"]
        payload, _ = fake_client.get("/prefix/_bk_release/bk.release.gateway.prod")
        assert json.loads(payload)["publish_id"] == DELETE_PUBLISH_ID

    def test_preserves_keys_outside_key_prefix(self):
        fake_client = FakeEtcdClient(
            {
                "/prefix/route/route-1": "route-1-value",
                "/prefix-sibling/route/route-1": "sibling-before-value",
                "/prefixz/route/route-1": "sibling-after-value",
                "/prefix0/route/route-1": "range-end-neighbour-value",
            }
        )

        EtcdRegistry("/prefix/", etcd_client=fake_client).replace_resources_by_key_prefix_atomically(
            [make_delete_release()]
        )

        assert fake_client.keys == [
            "/prefix-sibling/route/route-1",
            "/prefix/_bk_release/bk.release.gateway.prod",
            "/prefix0/route/route-1",
            "/prefixz/route/route-1",
        ]

    def test_empty_resources_deletes_every_key_under_prefix_only(self):
        fake_client = FakeEtcdClient(
            {
                "/prefix/route/route-1": "route-1-value",
                "/prefix/service/svc-1": "svc-1-value",
                "/prefixz/route/route-1": "sibling-after-value",
            }
        )

        EtcdRegistry("/prefix/", etcd_client=fake_client).replace_resources_by_key_prefix_atomically([])

        assert fake_client.keys == ["/prefixz/route/route-1"]

    def test_rejects_duplicated_resource_keys(self, mock_etcd_client):
        with pytest.raises(ValueError, match="duplicated resource key"):
            EtcdRegistry("/prefix/", etcd_client=mock_etcd_client).replace_resources_by_key_prefix_atomically(
                [make_service("svc-1"), make_service("svc-1")]
            )

        mock_etcd_client.transaction.assert_not_called()

    def test_rejects_resource_key_outside_key_prefix(self, mock_etcd_client):
        class EscapingRegistry(EtcdRegistry):
            def _get_key(self, kind: str, id: str) -> str:
                return "/other-prefix/service/svc-1"

        with pytest.raises(ValueError, match="outside of the registry key prefix"):
            EscapingRegistry("/prefix/", etcd_client=mock_etcd_client).replace_resources_by_key_prefix_atomically(
                [make_service("svc-1")]
            )

        mock_etcd_client.transaction.assert_not_called()
