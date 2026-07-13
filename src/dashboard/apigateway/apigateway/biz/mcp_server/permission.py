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
import logging
from typing import TYPE_CHECKING, List, Optional

from django.db.models import Q
from django.utils.translation import gettext_lazy as _

from apigateway.apps.mcp_server.constants import (
    MCPServerAppPermissionApplyExpireDaysEnum,
    MCPServerAppPermissionApplyStatusEnum,
    MCPServerStatusEnum,
)
from apigateway.apps.mcp_server.models import MCPServer, MCPServerAppPermissionApply
from apigateway.apps.permission.constants import FormattedGrantDimensionEnum
from apigateway.common.error_codes import error_codes
from apigateway.common.tenant.query import gateway_filter_by_maintainer_tenant_id
from apigateway.core.constants import GatewayStatusEnum, StageStatusEnum
from apigateway.core.models import Gateway
from apigateway.service.bk_itsm import ItsmPermissionApplyHelper
from apigateway.utils.time import now_datetime

if TYPE_CHECKING:
    import datetime

logger = logging.getLogger(__name__)


class MCPServerPermissionHandler:
    @staticmethod
    def get_pending_apply_queryset_for_gateway_maintainer(username: str, tenant_id: str):
        """获取指定用户作为网关管理员待审批的 MCP Server 权限申请列表"""
        queryset = Gateway.objects.filter(_maintainers__contains=username)
        if tenant_id:
            queryset = gateway_filter_by_maintainer_tenant_id(queryset, tenant_id)

        gateway_ids = [gateway.id for gateway in queryset if gateway.has_permission(username)]
        return MCPServerAppPermissionApply.objects.filter(
            mcp_server__gateway_id__in=gateway_ids,
            status=MCPServerAppPermissionApplyStatusEnum.PENDING.value,
            is_deleted=False,
        )

    @staticmethod
    def create_apply(bk_app_code: str, mcp_server_ids: List[int], reason: str, applied_by: str):
        queryset = MCPServer.objects.filter(
            id__in=mcp_server_ids,
            status=MCPServerStatusEnum.ACTIVE.value,
            gateway__status=GatewayStatusEnum.ACTIVE.value,
            stage__status=StageStatusEnum.ACTIVE.value,
        )

        selected_mcp_server_ids = list(queryset.values_list("id", flat=True))
        if set(selected_mcp_server_ids) != set(mcp_server_ids):
            raise error_codes.NOT_FOUND.format(_("请检查对应 mcp server /环境/网关是否都已启用。"), replace=True)

        existing_permissions = MCPServerAppPermissionApply.objects.filter(
            bk_app_code=bk_app_code,
            mcp_server_id__in=selected_mcp_server_ids,
            is_deleted=False,
            status__in=[
                MCPServerAppPermissionApplyStatusEnum.PENDING.value,
                MCPServerAppPermissionApplyStatusEnum.APPROVED.value,
            ],
        ).order_by("-applied_time")

        if existing_permissions:
            existing_names = ", ".join([obj.mcp_server.name for obj in existing_permissions])
            raise error_codes.ALREADY_EXISTS.format(
                _(f"mcp server name：{existing_names} 已经存在待审批或已审批的记录")
            )

        current_time = now_datetime()
        created_apply_ids = []
        for obj in queryset:
            apply = MCPServerAppPermissionApply.objects.create(
                bk_app_code=bk_app_code,
                mcp_server=obj,
                reason=reason,
                applied_by=applied_by,
                applied_time=current_time,
                expire_days=MCPServerAppPermissionApplyExpireDaysEnum.FOREVER.value,
                status=MCPServerAppPermissionApplyStatusEnum.PENDING.value,
            )
            created_apply_ids.append(apply.id)

        new_applies = MCPServerAppPermissionApply.objects.filter(id__in=created_apply_ids)

        # 创建 ITSM 工单（不阻塞主流程）
        MCPServerPermissionHandler._create_itsm_tickets_for_applies(new_applies)

        return new_applies.select_related("mcp_server")

    @staticmethod
    def _create_itsm_tickets_for_applies(applies):
        """为 MCP Server 权限申请创建 ITSM 工单"""
        try:
            helper = ItsmPermissionApplyHelper()
            if not helper.is_ready():
                logger.info(
                    "Skip creating ITSM tickets for mcp server applies because ITSM helper is not ready, apply_count=%s",
                    applies.count(),
                )
                return

            for apply in applies.select_related("mcp_server__gateway"):
                try:
                    gateway = apply.mcp_server.gateway
                    callback_token = helper.generate_callback_token()
                    apply.itsm_callback_token = callback_token
                    apply.save(update_fields=["itsm_callback_token"])

                    resp = helper.create_permission_apply_ticket(
                        bk_app_code=apply.bk_app_code,
                        gateway_name=gateway.name,
                        grant_dimension=FormattedGrantDimensionEnum.MCP_SERVER.value,
                        apply_resource_names=[apply.mcp_server.name],
                        applied_by=apply.applied_by,
                        apply_record_id=apply.id,
                        approvers=gateway.maintainers,
                        callback_token=callback_token,
                    )

                    ticket_id = str(resp["id"])
                    apply.itsm_ticket_id = ticket_id
                    apply.save(update_fields=["itsm_ticket_id"])
                    logger.info(
                        "ITSM ticket created for mcp server apply: apply_id=%s, ticket_id=%s",
                        apply.id,
                        ticket_id,
                    )
                except Exception:
                    logger.exception("Failed to create ITSM ticket for mcp server apply, apply_id=%s", apply.id)
        except Exception:
            logger.exception("Failed to create ITSM tickets for mcp server applies")

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
            queryset = queryset.filter(Q(mcp_server__name__icontains=query) | Q(mcp_server__title__icontains=query))

        return queryset
