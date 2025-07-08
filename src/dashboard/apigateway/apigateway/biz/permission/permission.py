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

from typing import List

from apigateway.apps.permission.constants import (
    GrantTypeEnum,
)
from apigateway.apps.permission.models import (
    AppGatewayPermission,
    AppResourcePermission,
)
from apigateway.core.models import Gateway


class ResourcePermissionHandler:
    @staticmethod
    def grant_or_renewal_expire_soon(
        gateway: Gateway, resource_id: int, bk_app_code: str, expire_days: int, expires_soon_seconds: int = 300
    ):
        app_resource_permission = AppResourcePermission.objects.get_permission_or_none(
            gateway=gateway,
            resource_id=resource_id,
            bk_app_code=bk_app_code,
        )
        if not app_resource_permission or app_resource_permission.will_expired_in(seconds=expires_soon_seconds):
            AppResourcePermission.objects.save_permissions(
                gateway=gateway,
                resource_ids=[resource_id],
                bk_app_code=bk_app_code,
                grant_type=GrantTypeEnum.INITIALIZE.value,
                expire_days=expire_days,
            )

    @staticmethod
    def sync_from_gateway_permission(gateway: Gateway, bk_app_code: str, resource_ids: List[int]):
        api_perm = AppGatewayPermission.objects.filter(bk_app_code=bk_app_code, gateway_id=gateway.id).first()
        if not api_perm or api_perm.has_expired:
            return

        has_perm_resource_ids = list(
            AppResourcePermission.objects.filter(
                bk_app_code=bk_app_code, gateway_id=gateway.id, resource_id__in=resource_ids
            ).values_list("resource_id", flat=True)
        )

        for resource_id in set(resource_ids) - set(has_perm_resource_ids):
            # 此处使用 get_or_create, 其它功能同时添加权限时，可跳过此处的同步
            AppResourcePermission.objects.get_or_create(
                gateway=gateway,
                resource_id=resource_id,
                bk_app_code=bk_app_code,
                defaults={
                    "expires": api_perm.expires,
                    "grant_type": GrantTypeEnum.SYNC.value,
                },
            )
