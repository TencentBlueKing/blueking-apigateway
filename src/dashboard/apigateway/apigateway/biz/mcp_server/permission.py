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
import datetime
import logging
from typing import List, Optional

from django.utils.translation import gettext_lazy as _

from apigateway.apps.mcp_server.constants import (
    MCPServerAppPermissionApplyExpireDaysEnum,
    MCPServerAppPermissionApplyStatusEnum,
    MCPServerStatusEnum,
)
from apigateway.apps.mcp_server.models import MCPServer, MCPServerAppPermissionApply
from apigateway.common.error_codes import error_codes
from apigateway.core.constants import GatewayStatusEnum, StageStatusEnum
from apigateway.utils.time import now_datetime

logger = logging.getLogger(__name__)


class MCPServerPermissionHandler:
    @staticmethod
    def create_apply(bk_app_code: str, mcp_server_ids: List[int], reason: str, applied_by: str):
        queryset = MCPServer.objects.filter(
            id__in=mcp_server_ids,
            status=MCPServerStatusEnum.ACTIVE.value,
            gateway__status=GatewayStatusEnum.ACTIVE.value,
            stage__status=StageStatusEnum.ACTIVE.value,
        )

        selected_mcp_server_ids = list(queryset.values_list("id", flat=True))
        existing_permissions = MCPServerAppPermissionApply.objects.filter(
            bk_app_code=bk_app_code,
            mcp_server_id__in=selected_mcp_server_ids,
            status__in=[
                MCPServerAppPermissionApplyStatusEnum.PENDING.value,
                MCPServerAppPermissionApplyStatusEnum.APPROVED.value,
            ],
        ).order_by("-applied_time")

        if existing_permissions:
            existing_names = ", ".join([obj.mcp_server.name for obj in existing_permissions])
            raise error_codes.INVALID_ARGUMENT.format(
                _(f"mcp server name：{existing_names} 已经存在待审批或已审批的记录")
            )

        add_app_permissions_apply_list = [
            MCPServerAppPermissionApply(
                bk_app_code=bk_app_code,
                mcp_server=obj,
                reason=reason,
                applied_by=applied_by,
                applied_time=now_datetime(),
                expire_days=MCPServerAppPermissionApplyExpireDaysEnum.FOREVER.value,
                status=MCPServerAppPermissionApplyStatusEnum.PENDING.value,
            )
            for obj in queryset
        ]

        return MCPServerAppPermissionApply.objects.bulk_create(add_app_permissions_apply_list)

    @staticmethod
    def filter_records(
        bk_app_code: str,
        applied_by: str,
        apply_status: str,
        query: str,
        applied_time_start: Optional[datetime.datetime] = None,
        applied_time_end: Optional[datetime.datetime] = None,
    ):
        queryset = MCPServerAppPermissionApply.objects.filter(bk_app_code=bk_app_code).order_by("-applied_time")

        if applied_by:
            queryset = queryset.filter(applied_by=applied_by)

        if applied_time_start and applied_time_end:
            queryset = queryset.filter(applied_time__range=(applied_time_start, applied_time_end))

        if apply_status:
            queryset = queryset.filter(status=apply_status)

        if query:
            queryset = queryset.filter(mcp_server__name__icontains=query)

        return queryset
