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

from blue_krill.async_utils.django_utils import apply_async_on_commit
from django.conf import settings
from django.db import transaction
from django.utils.decorators import method_decorator
from drf_yasg.utils import swagger_auto_schema
from rest_framework import generics, status

from apigateway.apis.v2.permissions import OpenAPIV2Permission
from apigateway.apps.mcp_server.constants import (
    MCPServerAppPermissionApplyStatusEnum,
    MCPServerAppPermissionGrantTypeEnum,
)
from apigateway.apps.mcp_server.models import MCPServerAppPermission, MCPServerAppPermissionApply
from apigateway.apps.permission.constants import ApplyStatusEnum
from apigateway.apps.permission.models import AppPermissionApply
from apigateway.apps.permission.tasks import send_mail_for_perm_handle
from apigateway.biz.mcp_server import MCPServerHandler
from apigateway.biz.permission import PermissionDimensionManager
from apigateway.common.error_codes import error_codes
from apigateway.utils.responses import OKJsonResponse
from apigateway.utils.time import now_datetime

from . import serializers

logger = logging.getLogger(__name__)


@method_decorator(
    name="post",
    decorator=swagger_auto_schema(
        operation_description="ITSM 工单审批结果回调",
        request_body=serializers.ItsmCallbackInputSLZ,
        responses={status.HTTP_200_OK: ""},
        tags=["OpenAPI.V2.Open"],
    ),
)
class ItsmCallbackApi(generics.CreateAPIView):
    """
    ITSM 工单审批结果回调接口

    ITSM 单据结束后会向 callback_url 发送 POST 请求，
    请求体中包含 ticket 信息，包括 approve_result 等字段。
    """

    permission_classes = [OpenAPIV2Permission]

    def create(self, request, *args, **kwargs):
        slz = serializers.ItsmCallbackInputSLZ(data=request.data)
        slz.is_valid(raise_exception=True)

        data = slz.validated_data
        self._validate_callback_request_context(request)
        callback_token = self._get_callback_token(request, data)
        ticket = data.get("ticket", {})
        approve_result = self._parse_approve_result(ticket.get("approve_result", False))
        form_data = ticket.get("form_data", {})

        apply_record_id = form_data.get("apply_record_id")
        if apply_record_id in (None, ""):
            logger.warning("ITSM callback missing apply_record_id, ticket_id=%s", ticket.get("id"))
            raise error_codes.INVALID_ARGUMENT.format("apply_record_id is required in form_data")

        try:
            apply_record_id = int(apply_record_id)
        except (TypeError, ValueError):
            raise error_codes.INVALID_ARGUMENT.format("apply_record_id must be integer")

        ticket_id = str(ticket.get("id", ""))
        if not ticket_id:
            logger.warning("ITSM callback missing ticket.id, apply_record_id=%s", apply_record_id)
            raise error_codes.INVALID_ARGUMENT.format("ticket.id is required")

        self._handle_approval_result(
            apply_record_id=apply_record_id,
            approve_result=approve_result,
            ticket=ticket,
            callback_token=callback_token,
            ticket_id=ticket_id,
        )

        return OKJsonResponse(data={"result": True, "message": "success"})

    @staticmethod
    def _validate_callback_request_context(request):
        allowed_app_codes = getattr(settings, "BK_ITSM4_CALLBACK_ALLOWED_APP_CODES", ["bk-itsm4", "cw_aitsm"])
        app_code = getattr(getattr(request, "app", None), "app_code", "")
        if app_code not in allowed_app_codes:
            logger.warning("ITSM callback app_code not allowed, app_code=%s", app_code)
            raise error_codes.INVALID_ARGUMENT.format("invalid callback source app")

        if settings.ENABLE_MULTI_TENANT_MODE:
            tenant_id = request.headers.get("X-Bk-Tenant-Id")
            if not tenant_id:
                logger.warning("ITSM callback missing X-Bk-Tenant-Id in multi-tenant mode, app_code=%s", app_code)
                raise error_codes.INVALID_ARGUMENT.format("X-Bk-Tenant-Id is required")

    @staticmethod
    def _get_callback_token(request, data: Dict[str, Any]) -> str:
        callback_token = data.get("callback_token", "")
        if callback_token:
            return callback_token

        # 兼容 ITSM 回调只回传 query 参数 verify_token 的场景
        callback_token = request.query_params.get("verify_token", "")
        if callback_token:
            return callback_token

        raise error_codes.INVALID_ARGUMENT.format("callback_token or verify_token is required")

    @staticmethod
    def _parse_approve_result(value: Any) -> bool:
        if isinstance(value, bool):
            return value

        if isinstance(value, str):
            return value.strip().lower() in {"1", "true", "yes", "approved", "pass"}

        return bool(value)

    def _handle_approval_result(
        self,
        apply_record_id: int,
        approve_result: bool,
        ticket: Dict[str, Any],
        callback_token: str,
        ticket_id: str,
    ):
        """处理 ITSM 审批结果"""
        form_data = ticket.get("form_data", {})
        grant_dimension = form_data.get("grant_dimension", "gateway")

        if grant_dimension == "mcp_server":
            self._handle_mcp_server_approval(apply_record_id, approve_result, ticket_id, callback_token)
            return

        self._handle_gateway_approval(apply_record_id, approve_result, ticket_id, callback_token)

    @staticmethod
    def _validate_callback_token_and_ticket_id(
        *,
        local_callback_token: str,
        callback_token: str,
        local_ticket_id: str,
        callback_ticket_id: str,
        log_prefix: str,
        log_id_field: str,
        log_id_value: int,
    ):
        if not local_callback_token or local_callback_token != callback_token:
            logger.warning(
                "%s callback token mismatch, %s=%s, local_callback_token=%s",
                log_prefix,
                log_id_field,
                log_id_value,
                ItsmCallbackApi._mask_token(local_callback_token),
            )
            raise error_codes.INVALID_ARGUMENT.format("invalid callback_token")

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
        """处理网关/资源维度的 ITSM 审批结果"""
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
            record = manager.handle_permission_apply(
                gateway=apply.gateway,
                apply=apply,
                status=status_value,
                comment="",
                handled_by="itsm",
                part_resource_ids=None,
            )

            try:
                apply_async_on_commit(send_mail_for_perm_handle, args=[record.id])
            except Exception:  # pylint: disable=broad-except
                logger.exception("send mail to applicant fail. record_id=%s", record.id)

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
        """处理 MCP Server 维度的 ITSM 审批结果"""
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
            apply.handled_by = "itsm"
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
