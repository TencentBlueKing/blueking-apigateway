# -*- coding: utf-8 -*-
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
import logging
from typing import Any, Dict

from django.db import transaction

from apigateway.apps.mcp_server.constants import (
    MCPServerAppPermissionApplyStatusEnum,
    MCPServerAppPermissionGrantTypeEnum,
)
from apigateway.apps.mcp_server.models import MCPServerAppPermission, MCPServerAppPermissionApply
from apigateway.apps.permission.constants import ApplyStatusEnum, FormattedGrantDimensionEnum
from apigateway.apps.permission.models import AppPermissionApply
from apigateway.biz.mcp_server import MCPServerHandler
from apigateway.biz.permission import PermissionDimensionManager
from apigateway.common.error_codes import error_codes
from apigateway.utils.time import now_datetime

logger = logging.getLogger(__name__)

ITSM_PERMISSION_APPROVAL_HANDLER = "itsm"


class ItsmCallbackResultHandler:
    """处理 ITSM 回调审批结果"""

    def handle(self, ticket: Dict[str, Any], callback_token: str):
        form_data = ticket["form_data"]
        apply_record_id = form_data["apply_record_id"]
        grant_dimension = form_data["grant_dimension"]
        ticket_id = ticket["id"]
        approve_result = ticket["approve_result"]

        if grant_dimension == FormattedGrantDimensionEnum.MCP_SERVER.value:
            self._handle_mcp_server_approval(
                apply_record_id=apply_record_id,
                approve_result=approve_result,
                ticket_id=ticket_id,
                callback_token=callback_token,
            )
            return

        self._handle_gateway_approval(
            apply_record_id=apply_record_id,
            approve_result=approve_result,
            ticket_id=ticket_id,
            callback_token=callback_token,
        )

    @staticmethod
    def _mask_token(token: str) -> str:
        if not token:
            return ""
        if len(token) <= 8:
            return "****"
        return f"{token[:4]}****{token[-4:]}"

    @staticmethod
    def _validate_callback_token_and_ticket_id(
        local_callback_token: str,
        callback_token: str,
        local_ticket_id: str,
        callback_ticket_id: str,
        log_prefix: str,
        log_id_field: str,
        log_id_value: int,
    ):
        # 校验回调token: 为空或不一致，则抛出异常
        if not local_callback_token or local_callback_token != callback_token:
            logger.warning(
                "%s callback token mismatch, %s=%s, local_callback_token=%s",
                log_prefix,
                log_id_field,
                log_id_value,
                ItsmCallbackResultHandler._mask_token(local_callback_token),
            )
            raise error_codes.INVALID_ARGUMENT.format("invalid callback_token")

        # 校验回调ticket_id: 为空或不一致，则抛出异常
        if not local_ticket_id or local_ticket_id != callback_ticket_id:
            logger.warning(
                "%s callback ticket mismatch, %s=%s, local_ticket_id=%s, callback_ticket_id=%s",
                log_prefix,
                log_id_field,
                log_id_value,
                local_ticket_id,
                callback_ticket_id,
            )
            raise error_codes.INVALID_ARGUMENT.format("ticket id mismatch")

    def _handle_gateway_approval(
        self, apply_record_id: int, approve_result: bool, ticket_id: str, callback_token: str
    ):
        with transaction.atomic():
            apply = (
                AppPermissionApply.objects.select_for_update()
                .select_related("gateway")
                .filter(apply_record_id=apply_record_id)
                .first()
            )
            if not apply:
                logger.info("Gateway apply already consumed or not found, record_id=%s", apply_record_id)
                return

            if not apply.itsm_ticket_id:
                apply.itsm_ticket_id = ticket_id
                apply.save(update_fields=["itsm_ticket_id"])

            self._validate_callback_token_and_ticket_id(
                local_callback_token=apply.itsm_callback_token,
                callback_token=callback_token,
                local_ticket_id=apply.itsm_ticket_id,
                callback_ticket_id=ticket_id,
                log_prefix="ITSM gateway",
                log_id_field="record_id",
                log_id_value=apply_record_id,
            )

            if apply.status != ApplyStatusEnum.PENDING.value:
                logger.info(
                    "Ignore repeated gateway callback, record_id=%s, current_status=%s",
                    apply_record_id,
                    apply.status,
                )
                return

            status_value = ApplyStatusEnum.APPROVED.value if approve_result else ApplyStatusEnum.REJECTED.value
            manager = PermissionDimensionManager.get_manager(apply.grant_dimension)
            manager.handle_permission_apply(
                gateway=apply.gateway,
                apply=apply,
                status=status_value,
                comment="",
                handled_by=ITSM_PERMISSION_APPROVAL_HANDLER,
                part_resource_ids=None,
            )

            apply.delete()

        logger.info(
            "ITSM gateway approval result handled: record_id=%s, approve_result=%s, ticket_id=%s",
            apply_record_id,
            approve_result,
            ticket_id,
        )

    def _handle_mcp_server_approval(
        self, apply_record_id: int, approve_result: bool, ticket_id: str, callback_token: str
    ):
        with transaction.atomic():
            apply = (
                MCPServerAppPermissionApply.objects.select_for_update()
                .filter(id=apply_record_id)
                .select_related("mcp_server")
                .first()
            )
            if not apply:
                logger.info("MCP apply already consumed or not found, apply_id=%s", apply_record_id)
                return

            self._validate_callback_token_and_ticket_id(
                local_callback_token=apply.itsm_callback_token,
                callback_token=callback_token,
                local_ticket_id=apply.itsm_ticket_id,
                callback_ticket_id=ticket_id,
                log_prefix="ITSM mcp",
                log_id_field="apply_id",
                log_id_value=apply_record_id,
            )

            if apply.status != MCPServerAppPermissionApplyStatusEnum.PENDING.value:
                logger.info(
                    "Ignore repeated mcp callback, apply_id=%s, current_status=%s",
                    apply_record_id,
                    apply.status,
                )
                return

            status_value = (
                MCPServerAppPermissionApplyStatusEnum.APPROVED.value
                if approve_result
                else MCPServerAppPermissionApplyStatusEnum.REJECTED.value
            )
            apply.status = status_value
            apply.handled_by = ITSM_PERMISSION_APPROVAL_HANDLER
            apply.handled_time = now_datetime()
            apply.save(update_fields=["status", "handled_by", "handled_time"])

            if approve_result:
                MCPServerAppPermission.objects.save_permission(
                    mcp_server_id=apply.mcp_server_id,
                    bk_app_code=apply.bk_app_code,
                    grant_type=MCPServerAppPermissionGrantTypeEnum.APPLY.value,
                    expire_days=None,
                )
                MCPServerHandler.sync_permissions(apply.mcp_server_id)

        logger.info(
            "ITSM mcp server approval result handled: apply_id=%s, approve_result=%s, ticket_id=%s",
            apply_record_id,
            approve_result,
            ticket_id,
        )
