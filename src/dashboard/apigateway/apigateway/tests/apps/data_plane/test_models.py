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
from ddf import G
from django.db import IntegrityError

from apigateway.apps.data_plane.constants import DataPlaneStatusEnum
from apigateway.apps.data_plane.models import DataPlane, GatewayDataPlaneBinding
from apigateway.core.models import Gateway

pytestmark = pytest.mark.django_db


class TestGatewayDataPlaneBindingManager:
    """Test GatewayDataPlaneBindingManager methods"""

    @pytest.fixture(autouse=True)
    def setup_fixtures(self):
        """Setup test fixtures"""
        self.gateway1 = G(Gateway, name="test-gateway-1")
        self.gateway2 = G(Gateway, name="test-gateway-2")
        self.gateway3 = G(Gateway, name="test-gateway-3")

        self.data_plane_active1 = G(DataPlane, name="active-plane-1", status=DataPlaneStatusEnum.ACTIVE.value)
        self.data_plane_active2 = G(DataPlane, name="active-plane-2", status=DataPlaneStatusEnum.ACTIVE.value)
        self.data_plane_inactive = G(DataPlane, name="inactive-plane", status=DataPlaneStatusEnum.INACTIVE.value)

    def test_get_gateway_data_planes_returns_all_bound_planes(self):
        """Test get_gateway_data_planes returns all data planes including inactive ones"""
        # Bind gateway1 to multiple data planes
        G(GatewayDataPlaneBinding, gateway=self.gateway1, data_plane=self.data_plane_active1)
        G(GatewayDataPlaneBinding, gateway=self.gateway1, data_plane=self.data_plane_active2)
        G(GatewayDataPlaneBinding, gateway=self.gateway1, data_plane=self.data_plane_inactive)

        # Bind gateway2 to one data plane
        G(GatewayDataPlaneBinding, gateway=self.gateway2, data_plane=self.data_plane_active1)

        data_planes = GatewayDataPlaneBinding.objects.get_gateway_data_planes(self.gateway1.id)

        assert len(data_planes) == 3
        assert self.data_plane_active1 in data_planes
        assert self.data_plane_active2 in data_planes
        assert self.data_plane_inactive in data_planes

    def test_get_gateway_data_planes_returns_empty_for_unbound_gateway(self):
        """Test get_gateway_data_planes returns empty list for gateway with no bindings"""
        data_planes = GatewayDataPlaneBinding.objects.get_gateway_data_planes(self.gateway3.id)
        assert data_planes == []

    def test_get_gateway_active_data_planes_filters_by_status(self):
        """Test get_gateway_active_data_planes only returns active data planes"""
        # Bind gateway1 to both active and inactive data planes
        G(GatewayDataPlaneBinding, gateway=self.gateway1, data_plane=self.data_plane_active1)
        G(GatewayDataPlaneBinding, gateway=self.gateway1, data_plane=self.data_plane_active2)
        G(GatewayDataPlaneBinding, gateway=self.gateway1, data_plane=self.data_plane_inactive)

        active_planes = GatewayDataPlaneBinding.objects.get_gateway_active_data_planes(self.gateway1.id)

        assert len(active_planes) == 2
        assert self.data_plane_active1 in active_planes
        assert self.data_plane_active2 in active_planes
        assert self.data_plane_inactive not in active_planes

    def test_get_gateway_active_data_planes_returns_empty_for_unbound_gateway(self):
        """Test get_gateway_active_data_planes returns empty list for unbound gateway"""
        active_planes = GatewayDataPlaneBinding.objects.get_gateway_active_data_planes(self.gateway3.id)
        assert active_planes == []

    def test_is_gateway_bound_returns_true_when_bound(self):
        """Test is_gateway_bound returns True when gateway has bindings"""
        G(GatewayDataPlaneBinding, gateway=self.gateway1, data_plane=self.data_plane_active1)

        assert GatewayDataPlaneBinding.objects.is_gateway_bound(self.gateway1.id) is True

    def test_is_gateway_bound_returns_false_when_not_bound(self):
        """Test is_gateway_bound returns False when gateway has no bindings"""
        assert GatewayDataPlaneBinding.objects.is_gateway_bound(self.gateway3.id) is False

    def test_bind_gateway_to_data_plane_creates_binding(self):
        """Test bind_gateway_to_data_plane creates a new binding"""
        binding = GatewayDataPlaneBinding.objects.bind_gateway_to_data_plane(
            gateway=self.gateway1, data_plane=self.data_plane_active1, created_by="test_user"
        )

        assert binding.gateway == self.gateway1
        assert binding.data_plane == self.data_plane_active1
        assert binding.created_by == "test_user"
        assert binding.updated_by == "test_user"

    def test_bind_gateway_to_data_plane_returns_existing_binding(self):
        """Test bind_gateway_to_data_plane returns existing binding if already bound"""
        binding1 = GatewayDataPlaneBinding.objects.bind_gateway_to_data_plane(
            gateway=self.gateway1, data_plane=self.data_plane_active1, created_by="user1"
        )

        binding2 = GatewayDataPlaneBinding.objects.bind_gateway_to_data_plane(
            gateway=self.gateway1, data_plane=self.data_plane_active1, created_by="user2"
        )

        assert binding1.id == binding2.id
        assert binding1.created_by == "user1"  # Should keep original created_by

    def test_unbind_gateway_from_data_plane_deletes_binding(self):
        """Test unbind_gateway_from_data_plane removes the binding"""
        G(GatewayDataPlaneBinding, gateway=self.gateway1, data_plane=self.data_plane_active1)
        G(GatewayDataPlaneBinding, gateway=self.gateway1, data_plane=self.data_plane_active2)

        deleted_count = GatewayDataPlaneBinding.objects.unbind_gateway_from_data_plane(
            self.gateway1.id, self.data_plane_active1.id
        )

        assert deleted_count == 1
        assert not GatewayDataPlaneBinding.objects.filter(
            gateway=self.gateway1, data_plane=self.data_plane_active1
        ).exists()
        assert GatewayDataPlaneBinding.objects.filter(
            gateway=self.gateway1, data_plane=self.data_plane_active2
        ).exists()

    def test_unbind_gateway_from_data_plane_returns_zero_if_not_bound(self):
        """Test unbind_gateway_from_data_plane returns 0 if binding doesn't exist"""
        deleted_count = GatewayDataPlaneBinding.objects.unbind_gateway_from_data_plane(
            self.gateway1.id, self.data_plane_active1.id
        )

        assert deleted_count == 0

    def test_get_gateways_without_binding_returns_unbound_gateways(self):
        """Test get_gateways_without_binding returns only unbound gateways"""
        # Bind gateway1 and gateway2
        G(GatewayDataPlaneBinding, gateway=self.gateway1, data_plane=self.data_plane_active1)
        G(GatewayDataPlaneBinding, gateway=self.gateway2, data_plane=self.data_plane_active1)
        # gateway3 is not bound

        unbound_gateways = GatewayDataPlaneBinding.objects.get_gateways_without_binding()

        assert self.gateway3 in unbound_gateways
        assert self.gateway1 not in unbound_gateways
        assert self.gateway2 not in unbound_gateways

    def test_get_gateways_without_binding_returns_all_when_none_bound(self):
        """Test get_gateways_without_binding returns all gateways when none are bound"""
        unbound_gateways = GatewayDataPlaneBinding.objects.get_gateways_without_binding()

        assert len(unbound_gateways) >= 3
        assert self.gateway1 in unbound_gateways
        assert self.gateway2 in unbound_gateways
        assert self.gateway3 in unbound_gateways


class TestGatewayDataPlaneBindingModel:
    """Test GatewayDataPlaneBinding model"""

    def test_str_representation(self):
        """Test string representation of GatewayDataPlaneBinding"""
        gateway = G(Gateway, name="test-gateway")
        data_plane = G(DataPlane, name="test-plane")
        binding = G(GatewayDataPlaneBinding, gateway=gateway, data_plane=data_plane)

        expected = f"<GatewayDataPlaneBinding: gateway={gateway.id}, data_plane={data_plane.id}>"
        assert str(binding) == expected

    def test_unique_constraint_prevents_duplicate_bindings(self):
        """Test unique_together constraint prevents duplicate gateway-dataplane bindings"""
        gateway = G(Gateway, name="test-gateway")
        data_plane = G(DataPlane, name="test-plane")

        G(GatewayDataPlaneBinding, gateway=gateway, data_plane=data_plane)

        # Trying to create duplicate binding should fail
        with pytest.raises(IntegrityError):
            GatewayDataPlaneBinding.objects.create(gateway=gateway, data_plane=data_plane)

    def test_cascade_delete_on_gateway_deletion(self):
        """Test bindings are deleted when gateway is deleted"""
        gateway = G(Gateway, name="test-gateway")
        data_plane = G(DataPlane, name="test-plane")
        binding = G(GatewayDataPlaneBinding, gateway=gateway, data_plane=data_plane)

        gateway.delete()

        assert not GatewayDataPlaneBinding.objects.filter(id=binding.id).exists()

    def test_cascade_delete_on_data_plane_deletion(self):
        """Test bindings are deleted when data plane is deleted"""
        gateway = G(Gateway, name="test-gateway")
        data_plane = G(DataPlane, name="test-plane")
        binding = G(GatewayDataPlaneBinding, gateway=gateway, data_plane=data_plane)

        data_plane.delete()

        assert not GatewayDataPlaneBinding.objects.filter(id=binding.id).exists()
