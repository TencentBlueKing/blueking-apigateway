#
# TencentBlueKing is pleased to support the open source community by making
# 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
# Copyright (C) 2017 THL A29 Limited, a Tencent company. All rights reserved.
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

from apigateway.common.constants import (
    TENANT_ID_OPERATION,
    TenantModeEnum,
)


def gateway_filter_by_tenant_id(queryset: QuerySet, user_tenant_id: str) -> QuerySet:
    # 运营租户可以看到 全租户网关 + 自己租户网关
    if user_tenant_id == TENANT_ID_OPERATION:
        return queryset.filter(
            Q(tenant_mode=TenantModeEnum.GLOBAL.value)
            | Q(tenant_mode=TenantModeEnum.SINGLE.value, tenant_id=user_tenant_id)
        )
    # only list the gateways under the tenant
    return queryset.filter(tenant_mode=TenantModeEnum.SINGLE.value, tenant_id=user_tenant_id)
