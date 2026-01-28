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

from apigateway.controller.constants import DELETE_PUBLISH_ID
from apigateway.controller.distributor.base import BaseDistributor
from apigateway.controller.distributor.etcd import GatewayResourceDistributor, GlobalResourceDistributor, SyncFail


class TestSyncFail:
    """Test SyncFail exception"""

    def test_sync_fail_creation(self):
        """Test creating SyncFail exception"""
        resources = ["resource1", "resource2"]
        exc = SyncFail(resources)

        assert exc.resources == resources
        assert "sync resources failed" in str(exc)
        assert "resource1" in str(exc)

    def test_sync_fail_empty_resources(self):
        """Test SyncFail with empty resources"""
        exc = SyncFail([])
        assert exc.resources == []
        assert "sync resources failed" in str(exc)


class TestGatewayResourceDistributor:
    """Test GatewayResourceDistributor class"""

    def test_etcd_distributor_is_base_distributor(self, mocker):
        """Test that EtcdDistributor is a BaseDistributor"""
        mock_release = mocker.Mock()
        mock_release.gateway = mocker.Mock()
        mock_release.gateway.name = "test-gateway"
        mock_release.stage = mocker.Mock()
        mock_release.stage.name = "prod"
        mock_data_plane = mocker.Mock()
        mocker.patch("apigateway.controller.distributor.etcd.new_etcd_client")
        distributor = GatewayResourceDistributor(mock_release, mock_data_plane)
        assert isinstance(distributor, BaseDistributor)

    def test_gateway_property(self, mocker):
        """Test gateway property"""
        mock_release = mocker.Mock()
        mock_release.gateway = mocker.Mock()
        mock_release.gateway.name = "test-gateway"
        mock_data_plane = mocker.Mock()
        mocker.patch("apigateway.controller.distributor.etcd.new_etcd_client")
        distributor = GatewayResourceDistributor(mock_release, mock_data_plane)
        assert distributor.gateway == mock_release.gateway

    def test_stage_property(self, mocker):
        """Test stage property"""
        mock_release = mocker.Mock()
        mock_release.stage = mocker.Mock()
        mock_release.stage.name = "prod"
        mock_data_plane = mocker.Mock()
        mocker.patch("apigateway.controller.distributor.etcd.new_etcd_client")
        distributor = GatewayResourceDistributor(mock_release, mock_data_plane)
        assert distributor.stage == mock_release.stage

    def test_get_registry(self, mocker):
        """Test _get_registry method"""
        mock_gateway = mocker.Mock()
        mock_gateway.name = "test-gateway"

        mock_stage = mocker.Mock()
        mock_stage.name = "prod"

        # Mock EtcdRegistry
        mock_etcd_registry = mocker.patch("apigateway.controller.distributor.etcd.EtcdRegistry")

        mock_release = mocker.Mock()
        mock_release.gateway = mock_gateway
        mock_release.stage = mock_stage
        mock_data_plane = mocker.Mock()
        mocker.patch("apigateway.controller.distributor.etcd.new_etcd_client")
        # FIXME: mock release
        distributor = GatewayResourceDistributor(mock_release, mock_data_plane)
        registry = distributor._get_registry(mock_gateway, mock_stage)

        # Verify EtcdRegistry was called with correct key_prefix
        mock_etcd_registry.assert_called_once()
        call_args = mock_etcd_registry.call_args[1]
        assert "key_prefix" in call_args
        assert "test-gateway" in call_args["key_prefix"]
        assert "prod" in call_args["key_prefix"]

    def test_distribute_success(self, mocker):
        """Test distribute method success case"""
        mock_release = mocker.Mock()
        mock_release.gateway = mocker.Mock()
        mock_release.gateway.name = "test-gateway"
        mock_release.stage = mocker.Mock()
        mock_release.stage.name = "prod"

        # Mock dependencies
        mock_convertor = mocker.patch("apigateway.controller.distributor.etcd.GatewayApisixResourceTransformer")
        mock_convertor_instance = mock_convertor.return_value
        mock_convertor_instance.get_apisix_resources.return_value = []

        mock_registry = mocker.patch("apigateway.controller.distributor.etcd.EtcdRegistry")
        mock_registry_instance = mock_registry.return_value
        mock_registry_instance.sync_resources_by_key_prefix.return_value = []

        mocker.patch("apigateway.controller.distributor.etcd.ReleaseProcedureLogger")

        mock_data_plane = mocker.Mock()
        mocker.patch("apigateway.controller.distributor.etcd.new_etcd_client")
        distributor = GatewayResourceDistributor(mock_release, mock_data_plane)
        success, message = distributor.distribute(release_task_id="test-task-id", publish_id=123)

        assert success is True
        assert message == ""

    def test_distribute_failure(self, mocker):
        """Test distribute method failure case"""
        mock_release = mocker.Mock()
        mock_release.gateway = mocker.Mock()
        mock_release.gateway.name = "test-gateway"
        mock_release.stage = mocker.Mock()
        mock_release.stage.name = "prod"

        # Mock dependencies to raise exception
        mock_convertor = mocker.patch("apigateway.controller.distributor.etcd.GatewayApisixResourceTransformer")
        mock_convertor.return_value.transform.side_effect = Exception("Test error")

        mocker.patch("apigateway.controller.distributor.etcd.EtcdRegistry")
        mocker.patch("apigateway.controller.distributor.etcd.ReleaseProcedureLogger")

        mock_data_plane = mocker.Mock()
        mocker.patch("apigateway.controller.distributor.etcd.new_etcd_client")
        distributor = GatewayResourceDistributor(mock_release, mock_data_plane)
        success, message = distributor.distribute(release_task_id="test-task-id", publish_id=123)

        assert success is False
        assert "distribute gateway resources to etcd failed" in message
        assert "Test error" in message

    def test_revoke_with_delete_publish_id(self, mocker):
        """Test revoke method with DELETE_PUBLISH_ID"""
        mock_release = mocker.Mock()
        mock_release.gateway = mocker.Mock()
        mock_release.gateway.name = "test-gateway"
        mock_release.stage = mocker.Mock()
        mock_release.stage.name = "prod"
        mock_release.resource_version = mocker.Mock()
        mock_release.resource_version.version = "1.0.0"

        # mock_registry = mocker.patch("apigateway.controller.distributor.etcd.EtcdRegistry")
        # mock_registry_instance = mock_registry.return_value
        mock_registry = mocker.patch("apigateway.controller.distributor.etcd.EtcdRegistry")
        mock_registry_instance = mock_registry.return_value
        mock_registry_instance.sync_resources_by_key_prefix.return_value = []

        mocker.patch("apigateway.controller.distributor.etcd.ReleaseProcedureLogger")

        mock_data_plane = mocker.Mock()
        mocker.patch("apigateway.controller.distributor.etcd.new_etcd_client")
        distributor = GatewayResourceDistributor(mock_release, mock_data_plane)
        success, message = distributor.revoke(release_task_id="test-task-id", publish_id=DELETE_PUBLISH_ID)

        assert success is True
        assert message == "ok"
        mock_registry_instance.delete_resources_by_key_prefix.assert_called_once()

    def test_revoke_with_regular_publish_id(self, mocker):
        """Test revoke method with regular publish_id"""
        mock_release = mocker.Mock()
        mock_release.gateway = mocker.Mock()
        mock_release.gateway.name = "test-gateway"
        mock_release.stage = mocker.Mock()
        mock_release.stage.name = "prod"

        mock_convertor = mocker.patch("apigateway.controller.distributor.etcd.GatewayApisixResourceTransformer")
        mock_convertor_instance = mock_convertor.return_value
        mock_convertor_instance.get_apisix_resources.return_value = []

        mock_registry = mocker.patch("apigateway.controller.distributor.etcd.EtcdRegistry")
        mock_registry_instance = mock_registry.return_value
        mock_registry_instance.sync_resources_by_key_prefix.return_value = []

        mocker.patch("apigateway.controller.distributor.etcd.ReleaseProcedureLogger")

        mock_data_plane = mocker.Mock()
        mocker.patch("apigateway.controller.distributor.etcd.new_etcd_client")
        distributor = GatewayResourceDistributor(mock_release, mock_data_plane)
        success, message = distributor.revoke(release_task_id="test-task-id", publish_id=123)

        assert success is True
        assert message == "ok"
        mock_registry_instance.delete_resources_by_key_prefix.assert_called_once()

    def test_revoke_failure(self, mocker):
        """Test revoke method failure case"""
        mock_release = mocker.Mock()
        mock_release.gateway = mocker.Mock()
        mock_release.gateway.name = "test-gateway"
        mock_release.stage = mocker.Mock()
        mock_release.stage.name = "prod"

        mock_registry = mocker.patch("apigateway.controller.distributor.etcd.EtcdRegistry")
        mock_registry_instance = mock_registry.return_value
        mock_registry_instance.delete_resources_by_key_prefix.side_effect = Exception("Delete error")

        mocker.patch("apigateway.controller.distributor.etcd.ReleaseProcedureLogger")

        mock_data_plane = mocker.Mock()
        mocker.patch("apigateway.controller.distributor.etcd.new_etcd_client")
        distributor = GatewayResourceDistributor(mock_release, mock_data_plane)
        success, message = distributor.revoke(release_task_id="test-task-id", publish_id=123)

        assert success is False
        assert "revoke gateway resources from etcd failed" in message
        assert "Delete error" in message


class TestGlobalResourceDistributor:
    """Test GlobalResourceDistributor class"""

    def test_global_distributor_is_base_distributor(self):
        """Test that GlobalResourceDistributor is a BaseDistributor"""
        distributor = GlobalResourceDistributor()
        assert isinstance(distributor, BaseDistributor)

    def test_get_registry(self, mocker):
        """Test _get_registry method returns EtcdRegistry with correct key prefix"""
        # Mock GlobalKeyPrefixHandler
        mock_key_prefix_handler = mocker.patch("apigateway.controller.distributor.etcd.GlobalKeyPrefixHandler")
        mock_handler_instance = mock_key_prefix_handler.return_value
        mock_handler_instance.get_release_key_prefix.return_value = "test/global/prefix/"

        # Mock EtcdRegistry
        mock_etcd_registry = mocker.patch("apigateway.controller.distributor.etcd.EtcdRegistry")

        distributor = GlobalResourceDistributor()
        registry = distributor._get_registry()

        # Verify GlobalKeyPrefixHandler was called
        mock_key_prefix_handler.assert_called_once()
        mock_handler_instance.get_release_key_prefix.assert_called_once()

        # Verify EtcdRegistry was called with correct key_prefix
        mock_etcd_registry.assert_called_once_with(key_prefix="test/global/prefix/")
        assert registry == mock_etcd_registry.return_value

    def test_distribute_success(self, mocker):
        """Test distribute method success case"""
        # Mock GlobalApisixResourceTransformer
        mock_transformer = mocker.patch("apigateway.controller.distributor.etcd.GlobalApisixResourceTransformer")
        mock_transformer_instance = mock_transformer.return_value
        mock_transformer_instance.get_transformed_resources.return_value = [
            {"type": "route", "name": "test-route"},
            {"type": "service", "name": "test-service"},
        ]

        # Mock EtcdRegistry
        mock_registry = mocker.patch("apigateway.controller.distributor.etcd.EtcdRegistry")
        mock_registry_instance = mock_registry.return_value
        mock_registry_instance.sync_resources_by_key_prefix.return_value = []

        # Mock ReleaseProcedureLogger
        mock_logger = mocker.patch("apigateway.controller.distributor.etcd.ReleaseProcedureLogger")

        distributor = GlobalResourceDistributor()
        success, message = distributor.distribute(release_task_id="test-task-id", publish_id=123)

        # Verify success
        assert success is True
        assert message == "ok"

        # Verify transformer was called
        mock_transformer_instance.transform.assert_called_once()
        mock_transformer_instance.get_transformed_resources.assert_called_once()

        # Verify registry sync was called with correct resources
        mock_registry_instance.sync_resources_by_key_prefix.assert_called_once()
        call_args = mock_registry_instance.sync_resources_by_key_prefix.call_args[0][0]
        assert len(call_args) == 2
        assert {"type": "route", "name": "test-route"} in call_args
        assert {"type": "service", "name": "test-service"} in call_args

    def test_distribute_sync_fail(self, mocker):
        """Test distribute method when sync fails with SyncFail exception"""
        # Mock GlobalApisixResourceTransformer
        mock_transformer = mocker.patch("apigateway.controller.distributor.etcd.GlobalApisixResourceTransformer")
        mock_transformer_instance = mock_transformer.return_value
        mock_transformer_instance.get_transformed_resources.return_value = [{"type": "route", "name": "test-route"}]

        # Mock EtcdRegistry to return failed resources
        mock_registry = mocker.patch("apigateway.controller.distributor.etcd.EtcdRegistry")
        mock_registry_instance = mock_registry.return_value
        mock_registry_instance.sync_resources_by_key_prefix.return_value = [{"type": "route", "name": "failed-route"}]

        # Mock ReleaseProcedureLogger
        mocker.patch("apigateway.controller.distributor.etcd.ReleaseProcedureLogger")

        distributor = GlobalResourceDistributor()
        success, message = distributor.distribute(release_task_id="test-task-id", publish_id=123)

        # Verify failure
        assert success is False
        assert "distribute global resources to etcd failed" in message
        assert "SyncFail" in message

    def test_distribute_transformer_exception(self, mocker):
        """Test distribute method when transformer raises exception"""
        # Mock GlobalApisixResourceTransformer to raise exception
        mock_transformer = mocker.patch("apigateway.controller.distributor.etcd.GlobalApisixResourceTransformer")
        mock_transformer_instance = mock_transformer.return_value
        mock_transformer_instance.transform.side_effect = Exception("Transformer error")

        # Mock EtcdRegistry
        mocker.patch("apigateway.controller.distributor.etcd.EtcdRegistry")

        # Mock ReleaseProcedureLogger
        mocker.patch("apigateway.controller.distributor.etcd.ReleaseProcedureLogger")

        distributor = GlobalResourceDistributor()
        success, message = distributor.distribute(release_task_id="test-task-id", publish_id=123)

        # Verify failure
        assert success is False
        assert "distribute global resources to etcd failed" in message
        assert "Transformer error" in message

    def test_distribute_registry_exception(self, mocker):
        """Test distribute method when registry operations raise exception"""
        # Mock GlobalApisixResourceTransformer
        mock_transformer = mocker.patch("apigateway.controller.distributor.etcd.GlobalApisixResourceTransformer")
        mock_transformer_instance = mock_transformer.return_value
        mock_transformer_instance.get_transformed_resources.return_value = []

        # Mock EtcdRegistry to raise exception
        mock_registry = mocker.patch("apigateway.controller.distributor.etcd.EtcdRegistry")
        mock_registry_instance = mock_registry.return_value
        mock_registry_instance.sync_resources_by_key_prefix.side_effect = Exception("Registry error")

        # Mock ReleaseProcedureLogger
        mocker.patch("apigateway.controller.distributor.etcd.ReleaseProcedureLogger")

        distributor = GlobalResourceDistributor()
        success, message = distributor.distribute(release_task_id="test-task-id", publish_id=123)

        # Verify failure
        assert success is False
        assert "distribute global resources to etcd failed" in message
        assert "Registry error" in message

    def test_revoke_not_implemented(self):
        """Test that revoke method raises NotImplementedError"""
        distributor = GlobalResourceDistributor()

        with pytest.raises(NotImplementedError):
            distributor.revoke(release_task_id="test-task-id", publish_id=123)
