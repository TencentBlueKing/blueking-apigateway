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

from typing import TYPE_CHECKING

from django.db import transaction
from django.db.models import Q
from django.utils.translation import gettext as _

from apigateway.apps.audit.constants import OpTypeEnum
from apigateway.apps.mcp_server.constants import MCPServerAppPermissionApplyStatusEnum
from apigateway.apps.mcp_server.models import MCPServerAppPermissionApply
from apigateway.apps.permission.constants import ApplyStatusEnum
from apigateway.apps.permission.models import AppPermissionApply, AppPermissionApplyStatus, AppPermissionRecord
from apigateway.biz.audit import Auditor
from apigateway.biz.bk_itsm import ITSM_PERMISSION_APPROVAL_HANDLER
from apigateway.biz.gateway import GatewayHandler
from apigateway.common.error_codes import error_codes
from apigateway.common.tenant.query import (
    gateway_related_filter_by_maintainer_tenant_id,
    gateway_related_filter_by_user_tenant_id,
    mcp_server_related_filter_by_maintainer_tenant_id,
    mcp_server_related_filter_by_user_tenant_id,
)
from apigateway.service.bk_itsm import ItsmPermissionApplyHelper
from apigateway.utils.django import get_model_dict
from apigateway.utils.time import now_datetime

if TYPE_CHECKING:
    from django.db.models.query import QuerySet


class WorkbenchPermissionHandler:
    @staticmethod
    def _get_gateway_apply_for_update(apply_id: int, username: str, tenant_id: str) -> AppPermissionApply:
        apply = AppPermissionApply.objects.select_for_update().filter(id=apply_id, applied_by=username).first()
        if not apply:
            raise error_codes.NOT_FOUND
        # 租户校验使用普通查询，避免 FOR UPDATE 锁定关联的网关记录。
        queryset = gateway_related_filter_by_user_tenant_id(AppPermissionApply.objects.filter(id=apply.id), tenant_id)
        if not queryset.exists():
            raise error_codes.NOT_FOUND
        return apply

    @staticmethod
    def _get_gateway_apply_by_record_for_update(
        record_id: int, bk_app_code: str, tenant_id: str
    ) -> AppPermissionApply:
        apply = (
            AppPermissionApply.objects.select_for_update()
            .filter(
                apply_record_id=record_id,
                bk_app_code=bk_app_code,
            )
            .first()
        )
        if not apply:
            raise error_codes.NOT_FOUND
        if tenant_id:
            queryset = gateway_related_filter_by_user_tenant_id(
                AppPermissionApply.objects.filter(id=apply.id),
                tenant_id,
            )
            if not queryset.exists():
                raise error_codes.NOT_FOUND
        return apply

    @staticmethod
    def _get_mcp_apply_for_update(apply_id: int, username: str, tenant_id: str) -> MCPServerAppPermissionApply:
        apply = (
            MCPServerAppPermissionApply.objects.select_for_update()
            .filter(
                id=apply_id,
                applied_by=username,
                is_deleted=False,
            )
            .first()
        )
        if not apply:
            raise error_codes.NOT_FOUND
        # 租户校验使用普通查询，避免 FOR UPDATE 锁定关联的 MCP Server 和网关记录。
        queryset = mcp_server_related_filter_by_user_tenant_id(
            MCPServerAppPermissionApply.objects.filter(
                id=apply.id,
                is_deleted=False,
            ),
            tenant_id,
        )
        if not queryset.exists():
            raise error_codes.NOT_FOUND
        return apply

    @staticmethod
    def _get_mcp_apply_by_record_for_update(
        record_id: int, bk_app_code: str, tenant_id: str
    ) -> MCPServerAppPermissionApply:
        apply = (
            MCPServerAppPermissionApply.objects.select_for_update()
            .filter(
                id=record_id,
                bk_app_code=bk_app_code,
                is_deleted=False,
            )
            .first()
        )
        if not apply:
            raise error_codes.NOT_FOUND
        if tenant_id:
            queryset = mcp_server_related_filter_by_user_tenant_id(
                MCPServerAppPermissionApply.objects.filter(
                    id=apply.id,
                    is_deleted=False,
                ),
                tenant_id,
            )
            if not queryset.exists():
                raise error_codes.NOT_FOUND
        return apply

    @staticmethod
    def _record_gateway_apply_audit(
        op_type: OpTypeEnum,
        username: str,
        gateway_id: int,
        instance_id: int,
        instance_name: str,
        data_before: dict,
        data_after: dict,
        comment: str,
    ) -> None:
        Auditor.record_permission_op_success(
            op_type=op_type,
            username=username,
            gateway_id=gateway_id,
            instance_id=instance_id,
            instance_name=instance_name,
            data_before=data_before,
            data_after=data_after,
            comment=comment,
        )

    @staticmethod
    def _record_mcp_apply_audit(
        op_type: OpTypeEnum,
        username: str,
        gateway_id: int,
        instance_id: int,
        instance_name: str,
        data_before: dict,
        data_after: dict,
        comment: str,
    ) -> None:
        Auditor.record_mcp_server_permission_op_success(
            op_type=op_type,
            username=username,
            gateway_id=gateway_id,
            instance_id=instance_id,
            instance_name=instance_name,
            data_before=data_before,
            data_after=data_after,
            comment=comment,
        )

    @classmethod
    @transaction.atomic
    def cancel_gateway_permission_apply(
        cls,
        apply_id: int,
        username: str,
        tenant_id: str,
    ) -> None:
        """取消待审批 API 网关权限申请"""
        apply = cls._get_gateway_apply_for_update(apply_id, username, tenant_id)
        cls._cancel_gateway_permission_apply(apply, username)

    @classmethod
    @transaction.atomic
    def cancel_gateway_permission_apply_by_app(
        cls,
        record_id: int,
        bk_app_code: str,
        operated_by: str,
        tenant_id: str,
    ) -> None:
        """按应用取消待审批 API 网关权限申请"""
        apply = cls._get_gateway_apply_by_record_for_update(record_id, bk_app_code, tenant_id)
        cls._cancel_gateway_permission_apply(apply, operated_by)

    @classmethod
    def _cancel_gateway_permission_apply(cls, apply: AppPermissionApply, operated_by: str) -> None:
        if apply.status != ApplyStatusEnum.PENDING.value:
            raise error_codes.FAILED_PRECONDITION.format(_("仅待审批的申请可以取消。"), replace=True)

        data_before = get_model_dict(apply)
        if apply.itsm_ticket_id:
            ItsmPermissionApplyHelper().cancel_permission_apply_ticket(apply.itsm_ticket_id)

        AppPermissionApplyStatus.objects.filter(apply=apply).delete()
        AppPermissionRecord.objects.filter(id=apply.apply_record_id).update(
            status=ApplyStatusEnum.CANCELED.value,
            handled_by=operated_by,
            handled_time=now_datetime(),
        )
        apply.status = ApplyStatusEnum.CANCELED.value
        apply.save(update_fields=["status"])
        cls._record_gateway_apply_audit(
            op_type=OpTypeEnum.MODIFY,
            username=operated_by,
            gateway_id=apply.gateway_id,
            instance_id=apply.id,
            instance_name=apply.bk_app_code,
            data_before=data_before,
            data_after=get_model_dict(apply),
            comment="取消权限申请",
        )

    @classmethod
    @transaction.atomic
    def delete_gateway_permission_apply(
        cls,
        apply_id: int,
        username: str,
        tenant_id: str,
    ) -> None:
        """删除已取消 API 网关权限申请"""
        apply = cls._get_gateway_apply_for_update(apply_id, username, tenant_id)
        cls._delete_gateway_permission_apply(apply, username)

    @classmethod
    @transaction.atomic
    def delete_gateway_permission_apply_by_app(
        cls,
        record_id: int,
        bk_app_code: str,
        operated_by: str,
        tenant_id: str,
    ) -> None:
        """按应用删除已取消 API 网关权限申请"""
        apply = cls._get_gateway_apply_by_record_for_update(record_id, bk_app_code, tenant_id)
        cls._delete_gateway_permission_apply(apply, operated_by)

    @classmethod
    def _delete_gateway_permission_apply(cls, apply: AppPermissionApply, operated_by: str) -> None:
        if apply.status != ApplyStatusEnum.CANCELED.value:
            raise error_codes.FAILED_PRECONDITION.format(_("仅已取消的申请可以删除。"), replace=True)

        data_before = get_model_dict(apply)
        instance_id = apply.id
        gateway_id = apply.gateway_id
        instance_name = apply.bk_app_code
        AppPermissionRecord.objects.filter(id=apply.apply_record_id).delete()
        apply.delete()
        cls._record_gateway_apply_audit(
            op_type=OpTypeEnum.DELETE,
            username=operated_by,
            gateway_id=gateway_id,
            instance_id=instance_id,
            instance_name=instance_name,
            data_before=data_before,
            data_after={},
            comment="删除已取消的权限申请",
        )

    @classmethod
    @transaction.atomic
    def cancel_mcp_permission_apply(
        cls,
        apply_id: int,
        username: str,
        tenant_id: str,
    ) -> None:
        """取消待审批 MCP Server 权限申请"""
        apply = cls._get_mcp_apply_for_update(apply_id, username, tenant_id)
        cls._cancel_mcp_permission_apply(apply, username)

    @classmethod
    @transaction.atomic
    def cancel_mcp_permission_apply_by_app(
        cls,
        record_id: int,
        bk_app_code: str,
        operated_by: str,
        tenant_id: str,
    ) -> None:
        """按应用取消待审批 MCP Server 权限申请"""
        apply = cls._get_mcp_apply_by_record_for_update(record_id, bk_app_code, tenant_id)
        cls._cancel_mcp_permission_apply(apply, operated_by)

    @classmethod
    def _cancel_mcp_permission_apply(cls, apply: MCPServerAppPermissionApply, operated_by: str) -> None:
        if apply.status != MCPServerAppPermissionApplyStatusEnum.PENDING.value:
            raise error_codes.FAILED_PRECONDITION.format(_("仅待审批的申请可以取消。"), replace=True)

        data_before = get_model_dict(apply)
        if apply.itsm_ticket_id:
            ItsmPermissionApplyHelper().cancel_permission_apply_ticket(apply.itsm_ticket_id)
        apply.status = MCPServerAppPermissionApplyStatusEnum.CANCELED.value
        apply.handled_by = operated_by
        apply.handled_time = now_datetime()
        apply.save(update_fields=["status", "handled_by", "handled_time"])
        cls._record_mcp_apply_audit(
            op_type=OpTypeEnum.MODIFY,
            username=operated_by,
            gateway_id=apply.mcp_server.gateway_id,
            instance_id=apply.id,
            instance_name=apply.bk_app_code,
            data_before=data_before,
            data_after=get_model_dict(apply),
            comment="取消 MCP Server 权限申请",
        )

    @classmethod
    @transaction.atomic
    def delete_mcp_permission_apply(
        cls,
        apply_id: int,
        username: str,
        tenant_id: str,
    ) -> None:
        """删除已取消 MCP Server 权限申请"""
        apply = cls._get_mcp_apply_for_update(apply_id, username, tenant_id)
        cls._delete_mcp_permission_apply(apply, username)

    @classmethod
    @transaction.atomic
    def delete_mcp_permission_apply_by_app(
        cls,
        record_id: int,
        bk_app_code: str,
        operated_by: str,
        tenant_id: str,
    ) -> None:
        """按应用删除已取消 MCP Server 权限申请"""
        apply = cls._get_mcp_apply_by_record_for_update(record_id, bk_app_code, tenant_id)
        cls._delete_mcp_permission_apply(apply, operated_by)

    @classmethod
    def _delete_mcp_permission_apply(cls, apply: MCPServerAppPermissionApply, operated_by: str) -> None:
        if apply.status != MCPServerAppPermissionApplyStatusEnum.CANCELED.value:
            raise error_codes.FAILED_PRECONDITION.format(_("仅已取消的申请可以删除。"), replace=True)

        data_before = get_model_dict(apply)
        instance_id = apply.id
        gateway_id = apply.mcp_server.gateway_id
        instance_name = apply.bk_app_code
        apply.delete()
        cls._record_mcp_apply_audit(
            op_type=OpTypeEnum.DELETE,
            username=operated_by,
            gateway_id=gateway_id,
            instance_id=instance_id,
            instance_name=instance_name,
            data_before=data_before,
            data_after={},
            comment="删除已取消的 MCP Server 权限申请",
        )

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
        ).exclude(status__in=[ApplyStatusEnum.PENDING.value, ApplyStatusEnum.CANCELED.value])
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
        ).exclude(
            status__in=[
                MCPServerAppPermissionApplyStatusEnum.PENDING.value,
                MCPServerAppPermissionApplyStatusEnum.CANCELED.value,
            ]
        )
        return mcp_server_related_filter_by_maintainer_tenant_id(queryset, tenant_id)
