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

from django.db.models import Q, QuerySet

from .constants import (
    TENANT_ID_OPERATION,
    TenantModeEnum,
)


def gateway_filter_by_user_tenant_id(
    queryset: QuerySet, user_tenant_id: str, gateway_field_prefix: str = ""
) -> QuerySet:
    """按用户租户 ID 过滤网关相关的 QuerySet

    运营租户能看到全租户网关 + 本租户网关，其他租户只能看到本租户网关。

    Args:
        queryset: 待过滤的 QuerySet
        user_tenant_id: 用户租户 ID
        gateway_field_prefix: 网关字段前缀，用于跨模型关联查询。
            例如对 Gateway 自身传 ""，对 AppPermissionApply 传 "gateway__"，
            对 MCPServerAppPermissionApply 传 "mcp_server__gateway__"。

    Returns:
        QuerySet: filtered queryset
    """
    tenant_mode_field = f"{gateway_field_prefix}tenant_mode"
    tenant_id_field = f"{gateway_field_prefix}tenant_id"

    # 运营租户可以看到 全租户网关 + 自己租户网关
    if user_tenant_id == TENANT_ID_OPERATION:
        return queryset.filter(
            Q(**{tenant_mode_field: TenantModeEnum.GLOBAL.value})
            | Q(**{tenant_mode_field: TenantModeEnum.SINGLE.value, tenant_id_field: user_tenant_id})
        )
    # only list the gateways under the tenant
    return queryset.filter(**{tenant_mode_field: TenantModeEnum.SINGLE.value, tenant_id_field: user_tenant_id})


def gateway_filter_by_app_tenant_id(queryset: QuerySet, app_tenant_id: str) -> QuerySet:
    """应用维度/应用开发者 维度查看网关列表，能看到 全租户网关 + 本租户网关

    Args:
        queryset (QuerySet): gateway queryset
        app_tenant_id (str): app tenant id

    Returns:
        QuerySet: filtered queryset
    """
    return queryset.filter(
        Q(tenant_mode=TenantModeEnum.GLOBAL.value)
        | Q(tenant_mode=TenantModeEnum.SINGLE.value, tenant_id=app_tenant_id)
    )


def gateway_mcp_server_filter_by_user_tenant_id(queryset: QuerySet, user_tenant_id: str) -> QuerySet:
    """按用户租户 ID 过滤 MCPServer QuerySet（通过 gateway 关联）

    等同于 gateway_filter_by_user_tenant_id(queryset, user_tenant_id, gateway_field_prefix="gateway__")
    """
    return gateway_filter_by_user_tenant_id(queryset, user_tenant_id, gateway_field_prefix="gateway__")
