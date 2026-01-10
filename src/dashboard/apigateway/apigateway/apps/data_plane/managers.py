#
# TencentBlueKing is pleased to support the open source community by making
# 蓝鲸智云 - API 网关 (BlueKing - APIGateway) available.
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
from typing import TYPE_CHECKING, List, Optional

from django.db import models

from apigateway.core.models import Gateway

from .constants import DEFAULT_DATA_PLANE_NAME, DataPlaneStatusEnum

if TYPE_CHECKING:
    from .models import DataPlane, GatewayDataPlaneBinding


class DataPlaneManager(models.Manager):
    def get_default(self) -> Optional["DataPlane"]:
        """Get the default data plane"""
        return self.filter(name=DEFAULT_DATA_PLANE_NAME).first()

    def get_recommended(self) -> Optional["DataPlane"]:
        """Get the recommended data plane for new gateways"""
        # First try to get an active recommended data plane
        data_plane = self.filter(is_recommend=True, status=DataPlaneStatusEnum.ACTIVE.value).first()
        if data_plane:
            return data_plane
        # Fall back to the default data plane
        return self.get_default()

    def get_active_data_planes(self) -> List["DataPlane"]:
        """Get all active data planes"""
        return list(self.filter(status=DataPlaneStatusEnum.ACTIVE.value))


class GatewayDataPlaneBindingManager(models.Manager):
    def get_gateway_data_planes(self, gateway_id: int) -> List["DataPlane"]:
        """Get all data planes bound to a gateway"""
        bindings = self.filter(gateway_id=gateway_id).select_related("data_plane")
        return [binding.data_plane for binding in bindings]

    def get_gateway_active_data_planes(self, gateway_id: int) -> List["DataPlane"]:
        """Get all active data planes bound to a gateway"""
        bindings = self.filter(
            gateway_id=gateway_id,
            data_plane__status=DataPlaneStatusEnum.ACTIVE.value,
        ).select_related("data_plane")
        return [binding.data_plane for binding in bindings]

    def is_gateway_bound(self, gateway_id: int) -> bool:
        """Check if a gateway is bound to any data plane"""
        return self.filter(gateway_id=gateway_id).exists()

    def bind_gateway_to_data_plane(
        self, gateway: Gateway, data_plane: "DataPlane", created_by: str = ""
    ) -> "GatewayDataPlaneBinding":
        """Bind a gateway to a data plane"""
        binding, _ = self.get_or_create(
            gateway=gateway,
            data_plane=data_plane,
            defaults={"created_by": created_by, "updated_by": created_by},
        )
        return binding

    def unbind_gateway_from_data_plane(self, gateway_id: int, data_plane_id: int) -> int:
        """Unbind a gateway from a data plane"""
        return self.filter(gateway_id=gateway_id, data_plane_id=data_plane_id).delete()[0]

    def get_gateways_without_binding(self) -> List[Gateway]:
        """Get all gateways that are not bound to any data plane"""
        bound_gateway_ids = self.values_list("gateway_id", flat=True).distinct()
        return list(Gateway.objects.exclude(id__in=bound_gateway_ids))
