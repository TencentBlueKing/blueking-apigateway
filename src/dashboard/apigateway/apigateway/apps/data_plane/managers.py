#
# TencentBlueKing is pleased to support the open source community by making
# 蓝鲸智云 - API 网关 (BlueKing - APIGateway) available.
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
from typing import TYPE_CHECKING, List

from django.db import models

from apigateway.core.models import Gateway

from .constants import (
    DEFAULT_DATA_PLANE_NAME,
    DataPlaneStatusEnum,
    get_ai_gateway_apisix_version_error,
)

if TYPE_CHECKING:
    from .models import DataPlane, GatewayDataPlaneBinding


class DataPlaneManager(models.Manager):
    def get_default(self) -> "DataPlane":
        """Get the default data plane"""
        return self.get(name=DEFAULT_DATA_PLANE_NAME)

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

    def bind_gateway_to_data_plane(
        self, gateway: Gateway, data_plane: "DataPlane", created_by: str = ""
    ) -> "GatewayDataPlaneBinding":
        """Bind a gateway to a data plane"""
        if gateway.is_ai_gateway:
            compatibility_error = get_ai_gateway_apisix_version_error(data_plane.apisix_version)
            if compatibility_error:
                raise ValueError(compatibility_error)

        binding, _ = self.get_or_create(
            gateway=gateway,
            data_plane=data_plane,
            defaults={"created_by": created_by, "updated_by": created_by},
        )
        return binding

    def unbind_gateway_from_data_plane(self, gateway_id: int, data_plane_id: int) -> int:
        """Unbind a gateway from a data plane"""
        return self.filter(gateway_id=gateway_id, data_plane_id=data_plane_id).delete()[0]

    def list_gateways_without_binding(self) -> List[Gateway]:
        """Get all gateways that are not bound to any data plane"""
        bound_gateway_ids = self.values_list("gateway_id", flat=True).distinct()
        return list(Gateway.objects.exclude(id__in=bound_gateway_ids))
