#
# TencentBlueKing is pleased to support the open source community by making
# 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
# Copyright (C) Tencent. All rights reserved.
# Licensed under the MIT License (the "License"); you may not use this file except
# in compliance with the License. You may obtain a copy of the License at
#
# https://opensource.org/licenses/MIT
#
# Unless required by applicable law or agreed to in writing, software distributed under
# the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND,
# either express or implied. See the License for the specific language governing permissions and
# limitations under the License.
#
# We undertake not to change the open source license (MIT license) applicable
# to the current version of the project delivered to anyone in the future.
#

from typing import TYPE_CHECKING

from rest_framework.exceptions import ValidationError

from apigateway.apps.data_plane.constants import (
    AI_GATEWAY_MIN_APISIX_VERSION,
    is_apisix_version_supported_for_ai_gateway,
)

if TYPE_CHECKING:
    from collections.abc import Iterable

    from apigateway.apps.data_plane.models import DataPlane
    from apigateway.core.models import Gateway


def validate_gateway_data_plane_compatibility(gateway: Gateway, data_planes: Iterable[DataPlane]) -> None:
    if not gateway.is_ai_gateway:
        return

    incompatible_data_planes = [
        f"{data_plane.name} ({data_plane.apisix_version})"
        for data_plane in data_planes
        if not is_apisix_version_supported_for_ai_gateway(data_plane.apisix_version)
    ]
    if incompatible_data_planes:
        raise ValidationError(
            {
                "data_planes": (
                    f"AI Gateway requires APISIX {AI_GATEWAY_MIN_APISIX_VERSION} or later; "
                    f"incompatible data planes: {', '.join(incompatible_data_planes)}"
                )
            }
        )
