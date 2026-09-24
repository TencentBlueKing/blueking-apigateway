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

import itertools
import operator
from typing import List, Optional, Tuple

from django.conf import settings
from django.utils.translation import gettext as _
from rest_framework import serializers

from apigateway.apps.permission.constants import (
    OAUTH2_BUILTIN_APP_CODES,
    ApplyStatusEnum,
    GrantDimensionEnum,
    GrantTypeEnum,
)
from apigateway.apps.permission.models import (
    AppGatewayPermission,
    AppPermissionApply,
    AppResourcePermission,
)
from apigateway.apps.rbac.models import GatewayMember
from apigateway.common.tenant.constants import (
    TENANT_ID_OPERATION,
    TenantModeEnum,
)
from apigateway.common.tenant.query import gateway_filter_by_maintainer_tenant_id
from apigateway.common.tenant.request import get_tenant_id_for_gateway_maintainers
from apigateway.components.bkauth import get_app_tenant_info_cached
from apigateway.components.bkuser import query_display_names_cached, query_display_names_for_readonly
from apigateway.core.models import Gateway, Release, ReleasedResource, Resource


class ResourcePermissionHandler:
    @staticmethod
    def validate_user_managed_app_code(bk_app_code: str):
        if bk_app_code in OAUTH2_BUILTIN_APP_CODES:
            raise serializers.ValidationError(
                _("应用【{app_code}】的 API 权限由系统管理。").format(app_code=bk_app_code)
            )

    @staticmethod
    def validate_user_managed_permissions(queryset):
        builtin_app_codes = sorted(
            set(queryset.filter(bk_app_code__in=OAUTH2_BUILTIN_APP_CODES).values_list("bk_app_code", flat=True))
        )
        if builtin_app_codes:
            raise serializers.ValidationError(
                _("应用【{app_codes}】的 API 权限由系统管理。").format(app_codes=", ".join(builtin_app_codes))
            )

    @staticmethod
    def get_pending_apply_queryset_for_maintainer(username: str, tenant_id: str):
        """获取指定用户作为当前审批责任人的 API 网关权限申请列表"""
        gateway_ids = GatewayMember.objects.list_gateway_ids_by_approver(username)
        if tenant_id:
            queryset = Gateway.objects.filter(id__in=gateway_ids)
            queryset = gateway_filter_by_maintainer_tenant_id(queryset, tenant_id)
            gateway_ids = queryset.values_list("id", flat=True)
        return AppPermissionApply.objects.filter(
            gateway_id__in=gateway_ids,
            status=ApplyStatusEnum.PENDING.value,
        )

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
        # 无论网关维度权限是否过期，都继续同步到资源维度权限，避免已过期的资源权限无法续期
        if not api_perm:
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

    @staticmethod
    def renew_resource_permissions_by_resource_ids(
        bk_app_code: str,
        resource_ids: List[int],
        expire_days: int,
    ):
        grouped_resources = (
            Resource.objects.filter(id__in=resource_ids).values("gateway_id", "id").order_by("gateway_id")
        )
        for gateway_id, grouped in itertools.groupby(grouped_resources, key=operator.itemgetter("gateway_id")):
            grouped_resource_ids = [item["id"] for item in grouped]
            gateway = Gateway.objects.get(id=gateway_id)
            ResourcePermissionHandler.sync_from_gateway_permission(
                gateway=gateway,
                bk_app_code=bk_app_code,
                resource_ids=grouped_resource_ids,
            )
            AppResourcePermission.objects.renew_by_resource_ids(
                gateway=gateway,
                bk_app_code=bk_app_code,
                resource_ids=grouped_resource_ids,
                grant_type=GrantTypeEnum.RENEW.value,
                expire_days=expire_days,
            )

    @staticmethod
    def renew_resource_permissions_by_ids(gateway: Gateway, ids: List[int], expire_days: int, handled_by: str = ""):
        if not ids:
            return [], [], []

        queryset = AppResourcePermission.objects.filter(
            gateway=gateway,
            id__in=ids,
        )
        ResourcePermissionHandler.validate_user_managed_permissions(queryset)
        data_before = list(queryset)
        AppResourcePermission.objects.renew_by_ids(
            gateway=gateway,
            ids=ids,
            expires=expire_days,
            handled_by=handled_by,
        )
        data_after = list(
            AppResourcePermission.objects.filter(
                gateway=gateway,
                id__in=ids,
            )
        )
        bk_app_codes = [perm.bk_app_code for perm in data_before]

        return data_before, data_after, bk_app_codes

    @staticmethod
    def renew_gateway_permissions_by_ids(gateway: Gateway, ids: List[int], expire_days: int, handled_by: str = ""):
        if not ids:
            return [], [], []

        queryset = AppGatewayPermission.objects.filter(
            gateway=gateway,
            id__in=ids,
        )
        ResourcePermissionHandler.validate_user_managed_permissions(queryset)
        data_before = list(queryset)
        AppGatewayPermission.objects.renew_by_ids(
            gateway=gateway,
            ids=ids,
            expires=expire_days,
            handled_by=handled_by,
        )
        data_after = list(
            AppGatewayPermission.objects.filter(
                gateway=gateway,
                id__in=ids,
            )
        )
        bk_app_codes = [perm.bk_app_code for perm in data_before]

        return data_before, data_after, bk_app_codes

    @staticmethod
    def revoke_permissions(
        gateway: Gateway,
        bk_app_codes: List[str],
        grant_dimension: str,
        resource_names: Optional[List[str]] = None,
    ) -> Tuple[List[AppGatewayPermission], List[AppResourcePermission]]:
        """
        回收应用的权限，返回被回收的按网关权限、资源权限
        - 按网关回收：回收按网关权限，及由按网关权限同步产生的资源权限
        - 按资源回收：回收指定资源的权限，与授权接口一致，忽略不存在的资源名称
        """
        gateway_permissions: List[AppGatewayPermission] = []
        resource_queryset = AppResourcePermission.objects.filter(gateway=gateway, bk_app_code__in=bk_app_codes)
        if grant_dimension == GrantDimensionEnum.API.value:
            gateway_permissions = list(
                AppGatewayPermission.objects.filter(gateway=gateway, bk_app_code__in=bk_app_codes)
            )
            resource_queryset = resource_queryset.filter(grant_type=GrantTypeEnum.SYNC.value)
        else:
            # 资源名称对应的资源 ID，取当前编辑区资源与各环境已发布版本中资源的并集，
            # 资源从编辑区删除后，已发布版本中仍可能包含该资源，其权限仍然生效
            resource_names = resource_names or []
            resource_ids = set(
                Resource.objects.filter(gateway=gateway, name__in=resource_names).values_list("id", flat=True)
            )
            resource_ids.update(
                ReleasedResource.objects.filter(
                    gateway=gateway,
                    resource_version_id__in=Release.objects.get_released_resource_version_ids(gateway.id),
                    resource_name__in=resource_names,
                ).values_list("resource_id", flat=True)
            )
            resource_queryset = resource_queryset.filter(resource_id__in=resource_ids)
        resource_permissions = list(resource_queryset)

        # 按 ID 删除，保证删除的权限与返回的权限一致
        AppGatewayPermission.objects.filter(id__in=[perm.id for perm in gateway_permissions]).delete()
        AppResourcePermission.objects.filter(id__in=[perm.id for perm in resource_permissions]).delete()

        return gateway_permissions, resource_permissions

    @staticmethod
    def convert_applied_by_to_display_name(
        bk_app_code: str,
        applied_by: str,
        gateway_tenant_mode: str,
        gateway_tenant_id: str,
        force_convert: bool = False,
    ) -> str:
        """
        将申请人转换为显示名称，用于非 global 租户申请 global 网关权限时前端用户的展示
        """
        if not settings.ENABLE_MULTI_TENANT_MODE:
            return applied_by

        try:
            app_tenant_mode, app_tenant_id = get_app_tenant_info_cached(bk_app_code)
            if not force_convert and app_tenant_mode == gateway_tenant_mode and app_tenant_id == gateway_tenant_id:
                return applied_by

            if app_tenant_mode == TenantModeEnum.GLOBAL.value:
                app_tenant_id = TENANT_ID_OPERATION

            display_names = query_display_names_cached(app_tenant_id, applied_by)
            if display_names:
                return display_names[0].get("display_name", applied_by)
        except Exception:  # pylint: disable=broad-except
            return applied_by

        return applied_by

    @staticmethod
    def convert_gateway_maintainers_to_display_names(
        gateway_tenant_mode: str,
        gateway_tenant_id: str,
        maintainers: List[str],
    ) -> List[str]:
        """
        将网关维护人转换为查看态展示名称

        已知问题：list 场景仍会在序列化阶段按网关同步查询 bk-user。
        这次先保留现状，后续如需优化再改为视图层批量预取。
        """
        if not settings.ENABLE_MULTI_TENANT_MODE:
            return maintainers

        tenant_id = get_tenant_id_for_gateway_maintainers(gateway_tenant_mode, gateway_tenant_id)
        try:
            return query_display_names_for_readonly(tenant_id, maintainers)
        except Exception:  # pylint: disable=broad-except
            return maintainers
