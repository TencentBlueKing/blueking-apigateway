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

from django.db.models import Q
from django.db.models.query import QuerySet

from apigateway.apps.mcp_server.constants import MCPServerAppPermissionApplyStatusEnum
from apigateway.apps.mcp_server.models import MCPServerAppPermissionApply
from apigateway.apps.permission.constants import ApplyStatusEnum
from apigateway.apps.permission.models import AppPermissionRecord
from apigateway.biz.bk_itsm import ITSM_PERMISSION_APPROVAL_HANDLER
from apigateway.biz.gateway import GatewayHandler
from apigateway.common.tenant.query import (
    gateway_related_filter_by_maintainer_tenant_id,
    mcp_server_related_filter_by_maintainer_tenant_id,
)


class WorkbenchPermissionHandler:
    @staticmethod
    def _get_user_gateway_ids(username: str, tenant_id: str) -> list[int]:
        return [gateway.id for gateway in GatewayHandler.list_gateways_by_user(username, tenant_id)]

    @classmethod
    def get_handled_gateway_permission_record_queryset(cls, username: str, tenant_id: str) -> QuerySet:
        queryset = AppPermissionRecord.objects.filter(
            Q(handled_by=username)
            | Q(
                handled_by=ITSM_PERMISSION_APPROVAL_HANDLER,
                gateway_id__in=cls._get_user_gateway_ids(username, tenant_id),
            )
        ).exclude(status=ApplyStatusEnum.PENDING.value)
        return gateway_related_filter_by_maintainer_tenant_id(queryset, tenant_id)

    @classmethod
    def get_handled_mcp_permission_apply_queryset(cls, username: str, tenant_id: str) -> QuerySet:
        queryset = MCPServerAppPermissionApply.objects.filter(
            Q(handled_by=username)
            | Q(
                handled_by=ITSM_PERMISSION_APPROVAL_HANDLER,
                mcp_server__gateway_id__in=cls._get_user_gateway_ids(username, tenant_id),
            ),
            is_deleted=False,
        ).exclude(status=MCPServerAppPermissionApplyStatusEnum.PENDING.value)
        return mcp_server_related_filter_by_maintainer_tenant_id(queryset, tenant_id)
