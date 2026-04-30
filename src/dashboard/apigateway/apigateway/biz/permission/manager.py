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
from abc import ABCMeta, abstractmethod
from typing import List, Optional, Tuple

from django.conf import settings
from django.utils.translation import gettext as _

from apigateway.apps.permission.constants import (
    RENEWABLE_EXPIRE_DAYS,
    ApplyStatusEnum,
    GrantDimensionEnum,
    GrantTypeEnum,
)
from apigateway.apps.permission.models import (
    AppGatewayPermission,
    AppPermissionApply,
    AppPermissionApplyStatus,
    AppPermissionRecord,
    AppResourcePermission,
)
from apigateway.common.error_codes import error_codes
from apigateway.core.models import Gateway, Resource
from apigateway.service.bk_itsm import ItsmPermissionApplyHelper
from apigateway.utils.time import now_datetime

logger = logging.getLogger(__name__)


class PermissionDimensionManager(metaclass=ABCMeta):
    @staticmethod
    def _build_itsm_ticket_apply_resources(
        grant_dimension: str,
        gateway: Gateway,
        resource_ids: List[int],
    ) -> Tuple[str, List[str]]:
        """构建 ITSM 提单所需的授权维度与资源名称列表"""
        itsm_grant_dimension = grant_dimension
        resource_names: List[str] = []

        if grant_dimension == GrantDimensionEnum.API.value:
            itsm_grant_dimension = "gateway"
            resource_names = [gateway.name]
        elif grant_dimension == GrantDimensionEnum.RESOURCE.value and resource_ids:
            resource_names = list(
                Resource.objects.filter(gateway=gateway, id__in=resource_ids).values_list("name", flat=True)
            )

        return itsm_grant_dimension, resource_names

    @classmethod
    def get_manager(cls, grant_dimension: str) -> "PermissionDimensionManager":
        if grant_dimension == GrantDimensionEnum.API.value:
            return GatewayPermissionDimensionManager()
        if grant_dimension == GrantDimensionEnum.RESOURCE.value:
            return ResourcePermissionDimensionManager()

        raise error_codes.INVALID_ARGUMENT.format(f"unsupported grant_dimension: {grant_dimension}")

    @classmethod
    def get_permission_model(cls, grant_dimension: str):
        if grant_dimension == GrantDimensionEnum.API.value:
            return AppGatewayPermission

        if grant_dimension == GrantDimensionEnum.RESOURCE.value:
            return AppResourcePermission

        raise ValueError(f"unsupported dimension: {grant_dimension}")

    @abstractmethod
    def handle_permission_apply(
        self,
        gateway: Gateway,
        apply: AppPermissionApply,
        status: str,
        comment: str,
        handled_by: str,
        part_resource_ids: Optional[List[int]],
    ) -> AppPermissionRecord:
        """处理权限申请"""

    @abstractmethod
    def save_permission_apply_status(
        self,
        bk_app_code: str,
        gateway: Gateway,
        apply: AppPermissionApply,
        status: str,
        resources: List[Resource],
    ):
        """保存权限申请状态"""

    @abstractmethod
    def get_resource_names_display(self, gateway_id: int, resource_ids: List[int]) -> List[str]:
        """资源权限申请时，获取展示的资源名称列表"""

    @abstractmethod
    def get_approved_resource_names_display(self, gateway_id: int, resource_ids: List[int], status: str) -> List[str]:
        """资源审批时，获取审批通过的资源名称列表"""

    @abstractmethod
    def get_rejected_resource_names_display(self, gateway_id: int, resource_ids: List[int], status: str) -> List[str]:
        """资源审批时，获取审批拒绝的资源名称列表"""

    @abstractmethod
    def allow_apply_permission(
        self, gateway_id: int, bk_app_code: str, resource_ids: Optional[List[int]] = None
    ) -> Tuple[bool, str]:
        """判断是否允许申请权限"""

    def create_apply_record(
        self,
        bk_app_code: str,
        gateway: Gateway,
        resource_ids: List[int],
        grant_dimension: str,
        reason: str,
        expire_days: int,
        username: str,
    ) -> AppPermissionApply:
        """创建申请权限的单据"""
        record = AppPermissionRecord.objects.create(
            bk_app_code=bk_app_code,
            applied_by=username,
            applied_time=now_datetime(),
            reason=reason,
            expire_days=expire_days,
            gateway=gateway,
            resource_ids=resource_ids,
            grant_dimension=grant_dimension,
            status=ApplyStatusEnum.PENDING.value,
        )

        instance = AppPermissionApply.objects.create(
            bk_app_code=bk_app_code,
            applied_by=username,
            gateway=gateway,
            resource_ids=resource_ids,
            grant_dimension=grant_dimension,
            status=ApplyStatusEnum.PENDING.value,
            reason=reason,
            expire_days=expire_days,
            apply_record_id=record.id,
        )

        self.save_permission_apply_status(
            bk_app_code=bk_app_code,
            gateway=gateway,
            apply=instance,
            status=ApplyStatusEnum.PENDING.value,
            resources=Resource.objects.filter(gateway=gateway, id__in=resource_ids),
        )

        # 如果启用了 ITSM 权限申请工单，创建 ITSM 工单
        if getattr(settings, "BK_ITSM4_PERMISSION_APPLY_ENABLED", False):
            self._create_itsm_ticket(
                record=record,
                gateway=gateway,
                bk_app_code=bk_app_code,
                grant_dimension=grant_dimension,
                resource_ids=resource_ids,
                reason=reason,
                expire_days=expire_days,
                username=username,
            )

        return record

    def _create_itsm_ticket(
        self,
        record: AppPermissionRecord,
        gateway: Gateway,
        bk_app_code: str,
        grant_dimension: str,
        resource_ids: List[int],
        reason: str,
        expire_days: int,
        username: str,
    ):
        """创建 ITSM 权限申请工单"""
        try:
            helper = ItsmPermissionApplyHelper()
            if not helper.is_ready():
                return

            itsm_grant_dimension, resource_names = self._build_itsm_ticket_apply_resources(
                grant_dimension=grant_dimension,
                gateway=gateway,
                resource_ids=resource_ids,
            )
            callback_token = helper.generate_callback_token()
            AppPermissionApply.objects.filter(apply_record_id=record.id).update(itsm_callback_token=callback_token)

            resp = helper.create_permission_apply_ticket(
                bk_app_code=bk_app_code,
                gateway_name=gateway.name,
                grant_dimension=itsm_grant_dimension,
                apply_resource_names=resource_names,
                reason=reason,
                expire_days=expire_days,
                applied_by=username,
                apply_record_id=record.id,
                approvers=gateway.maintainers,
                callback_token=callback_token,
            )

            # 保存 ITSM 工单 ID 到申请记录
            ticket_id = helper.extract_ticket_id(resp)
            if ticket_id:
                record.itsm_ticket_id = ticket_id
                record.save(update_fields=["itsm_ticket_id"])

                AppPermissionApply.objects.filter(apply_record_id=record.id).update(itsm_ticket_id=ticket_id)

                logger.info(
                    "ITSM ticket created: record_id=%s, ticket_id=%s",
                    record.id,
                    ticket_id,
                )
        except Exception:
            # ITSM 工单创建失败不应阻塞主流程
            logger.exception("Failed to create ITSM ticket for permission apply, record_id=%s", record.id)


class GatewayPermissionDimensionManager(PermissionDimensionManager):
    def handle_permission_apply(
        self,
        gateway: Gateway,
        apply: AppPermissionApply,
        status: str,
        comment: str,
        handled_by: str,
        part_resource_ids=None,
    ) -> AppPermissionRecord:
        if status == ApplyStatusEnum.APPROVED.value:
            AppGatewayPermission.objects.save_permissions(
                gateway=gateway,
                bk_app_code=apply.bk_app_code,
                grant_type=GrantTypeEnum.APPLY.value,
                expire_days=apply.expire_days,
            )

        self._handle_apply_status(apply, status)

        # 添加到已审批单据记录
        return AppPermissionRecord.objects.save_record(
            record_id=apply.apply_record_id,
            gateway=gateway,
            bk_app_code=apply.bk_app_code,
            applied_by=apply.applied_by,
            applied_time=apply.created_time,
            handled_by=handled_by,
            resource_ids=apply.resource_ids,
            handled_resource_ids={},
            status=status,
            comment=comment,
            reason=apply.reason,
            expire_days=apply.expire_days,
            grant_dimension=apply.grant_dimension,
        )

    def save_permission_apply_status(
        self,
        bk_app_code: str,
        gateway: Gateway,
        apply: AppPermissionApply,
        status: str,
        resources=None,
    ):
        AppPermissionApplyStatus.objects.update_or_create(
            bk_app_code=bk_app_code,
            gateway=gateway,
            resource=None,
            grant_dimension=GrantDimensionEnum.API.value,
            defaults={
                "apply": apply,
                "status": status,
            },
        )

    def get_resource_names_display(self, gateway_id: int, resource_ids: List[int]) -> List[str]:
        return ["该网关所有资源，包括新建资源"]

    def get_approved_resource_names_display(self, gateway_id: int, resource_ids: List[int], status: str) -> List[str]:
        if status == ApplyStatusEnum.APPROVED.value:
            return self.get_resource_names_display(gateway_id, resource_ids)
        return []

    def get_rejected_resource_names_display(self, gateway_id: int, resource_ids: List[int], status: str) -> List[str]:
        if status == ApplyStatusEnum.APPROVED.value:
            return []

        return self.get_resource_names_display(gateway_id, resource_ids)

    def _handle_apply_status(self, apply, status: str):
        # 按网关申请被拒绝后，如果不删除申请状态记录，应用看到网关下所有资源申请状态均为“拒绝”，体验不友好，
        # 因此，按网关申请时，同意、拒绝，均删除申请状态记录
        AppPermissionApplyStatus.objects.filter(apply=apply).delete()

    def allow_apply_permission(
        self, gateway_id: int, bk_app_code: str, resource_ids: Optional[List[int]] = None
    ) -> Tuple[bool, str]:
        is_pending = AppPermissionApplyStatus.objects.is_permission_pending_by_gateway(gateway_id, bk_app_code)
        if is_pending:
            return False, _("权限申请中，请联系网关负责人审批。")

        api_perm = AppGatewayPermission.objects.filter(
            gateway_id=gateway_id,
            bk_app_code=bk_app_code,
        ).first()

        if api_perm and not api_perm.allow_apply_permission:
            return False, _("权限有效期小于 {days} 天时，才可申请。").format(days=RENEWABLE_EXPIRE_DAYS)

        return True, ""


class ResourcePermissionDimensionManager(PermissionDimensionManager):
    def handle_permission_apply(
        self,
        gateway: Gateway,
        apply: AppPermissionApply,
        status: str,
        comment: str,
        handled_by: str,
        part_resource_ids: Optional[List[int]],
    ):
        approved_resource_ids, rejected_resource_ids = self._split_resource_ids(
            status,
            apply.resource_ids,
            part_resource_ids,
        )

        # 如果审批同意，则更新权限信息
        # 如果审批驳回，则不做任何处理
        if approved_resource_ids:
            AppResourcePermission.objects.save_permissions(
                gateway=gateway,
                resource_ids=approved_resource_ids,
                bk_app_code=apply.bk_app_code,
                grant_type=GrantTypeEnum.APPLY.value,
                expire_days=apply.expire_days,
            )

        # 更新应用访问资源权限申请状态
        # 若拒绝，则更新状态为拒绝
        # 若同意，则删除单据对应记录
        self._handle_apply_status(apply, rejected_resource_ids)

        # 添加到已审批单据记录
        return AppPermissionRecord.objects.save_record(
            record_id=apply.apply_record_id,
            gateway=gateway,
            bk_app_code=apply.bk_app_code,
            applied_by=apply.applied_by,
            applied_time=apply.created_time,
            handled_by=handled_by,
            resource_ids=apply.resource_ids,
            handled_resource_ids={
                ApplyStatusEnum.APPROVED.value: approved_resource_ids,
                ApplyStatusEnum.REJECTED.value: rejected_resource_ids,
            },
            status=status,
            comment=comment,
            reason=apply.reason,
            expire_days=apply.expire_days,
            grant_dimension=apply.grant_dimension,
        )

    def save_permission_apply_status(
        self,
        bk_app_code: str,
        gateway: Gateway,
        apply: AppPermissionApply,
        status: str,
        resources=None,
    ):
        for resource in resources:
            AppPermissionApplyStatus.objects.update_or_create(
                bk_app_code=bk_app_code,
                gateway=gateway,
                resource=resource,
                grant_dimension=GrantDimensionEnum.RESOURCE.value,
                defaults={
                    "apply": apply,
                    "status": status,
                },
            )

    def get_resource_names_display(self, gateway_id: int, resource_ids: List[int]) -> List[str]:
        if not resource_ids:
            return []

        return list(Resource.objects.filter(gateway_id=gateway_id, id__in=resource_ids).values_list("name", flat=True))

    def get_approved_resource_names_display(self, gateway_id: int, resource_ids: List[int], status: str) -> List[str]:
        return self.get_resource_names_display(gateway_id, resource_ids)

    def get_rejected_resource_names_display(self, gateway_id: int, resource_ids: List[int], status: str) -> List[str]:
        return self.get_resource_names_display(gateway_id, resource_ids)

    def _handle_apply_status(self, apply: AppPermissionApply, rejected_resource_ids: List[int]):
        if rejected_resource_ids:
            AppPermissionApplyStatus.objects.filter(apply=apply, resource_id__in=rejected_resource_ids).update(
                apply=None,
                status=ApplyStatusEnum.REJECTED.value,
            )

        AppPermissionApplyStatus.objects.filter(apply=apply).delete()

    def _split_resource_ids(self, status, resource_ids, part_resource_ids=None):
        """
        拆分资源 ID 为通过、驳回两组
        :param status: 审批状态
        :param resource_ids: 申请单据中的资源 ID
        :param part_resource_ids: 部分审批时，部分审批的资源 ID
        """
        if status == ApplyStatusEnum.APPROVED.value:
            return resource_ids, []

        if status == ApplyStatusEnum.REJECTED.value:
            return [], resource_ids

        if status == ApplyStatusEnum.PARTIAL_APPROVED.value:
            resource_id_set = set(resource_ids)
            part_resource_id_set = set(part_resource_ids or [])
            return list(resource_id_set & part_resource_id_set), list(resource_id_set - part_resource_id_set)

        raise ValueError("unsupported apply status: {status}")

    def allow_apply_permission(
        self, gateway_id: int, bk_app_code: str, resource_ids: Optional[List[int]] = None
    ) -> Tuple[bool, str]:
        # 按资源申请时，resource_ids 必须传入
        if not resource_ids:
            return True, ""

        # 检查待审批
        qs = AppPermissionApplyStatus.objects.filter(
            bk_app_code=bk_app_code,
            gateway_id=gateway_id,
            grant_dimension=GrantDimensionEnum.RESOURCE.value,
            status=ApplyStatusEnum.PENDING.value,
            resource_id__in=resource_ids,
        )

        pending_resource_names = list(qs.values_list("resource__name", flat=True))
        if pending_resource_names:
            return False, _("[{names}] 资源权限申请中，请联系网关负责人审批。").format(
                names=", ".join(pending_resource_names)
            )

        # 检查已拥有且未过期的权限
        existing_perms = AppResourcePermission.objects.filter(
            gateway_id=gateway_id,
            bk_app_code=bk_app_code,
            resource_id__in=resource_ids,
        )
        unexpired_resource_ids = [perm.resource_id for perm in existing_perms if not perm.allow_apply_permission]
        if unexpired_resource_ids:
            unexpired_resource_names = list(
                Resource.objects.filter(gateway_id=gateway_id, id__in=unexpired_resource_ids).values_list(
                    "name", flat=True
                )
            )
            if unexpired_resource_names:
                return False, _("[{names}] 资源权限已存在且未过期，无需重复申请。").format(
                    names=", ".join(unexpired_resource_names)
                )

        return True, ""
