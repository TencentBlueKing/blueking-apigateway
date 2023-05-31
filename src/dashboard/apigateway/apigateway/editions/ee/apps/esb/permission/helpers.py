# -*- coding: utf-8 -*-
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
from typing import List, Optional, Tuple

from apigateway.apps.esb.bkcore.models import (
    AppComponentPermission,
    AppPermissionApplyRecord,
    AppPermissionApplyStatus,
)
from apigateway.apps.permission.constants import ApplyStatusEnum, GrantTypeEnum
from apigateway.utils.time import now_datetime


class PermissionManager:
    def handle_permission_apply(
        self,
        record: AppPermissionApplyRecord,
        status: str,
        comment: str,
        handled_by: str,
        part_component_ids: Optional[List[int]],
    ):
        approved_component_ids, rejected_component_ids = self._split_component_ids(
            status,
            record.component_ids,
            part_component_ids,
        )

        # 如果审批同意，则更新权限信息
        # 如果审批驳回，则不做任何处理
        if approved_component_ids:
            AppComponentPermission.objects.save_permissions(
                board=record.board,
                component_ids=approved_component_ids,
                bk_app_code=record.bk_app_code,
                grant_type=GrantTypeEnum.APPLY.value,
                expire_days=record.expire_days,
            )

        # 更新应用访问组件权限申请状态
        # 若拒绝，则更新状态为拒绝
        # 若同意，则删除单据对应记录
        self._handle_apply_status(record, rejected_component_ids)

        # 更新单据
        record.handled_by = handled_by
        record.handled_time = now_datetime()
        record.status = status
        record.comment = comment
        record.handled_component_ids = {
            ApplyStatusEnum.APPROVED.value: approved_component_ids,
            ApplyStatusEnum.REJECTED.value: rejected_component_ids,
        }

        record.save()

    def _handle_apply_status(self, record: AppPermissionApplyRecord, rejected_component_ids: List[int]):
        if rejected_component_ids:
            AppPermissionApplyStatus.objects.filter(record=record, component_id__in=rejected_component_ids).update(
                record=None,
                status=ApplyStatusEnum.REJECTED.value,
            )

        AppPermissionApplyStatus.objects.filter(record=record).delete()

    def _split_component_ids(
        self,
        status: str,
        component_ids: List[int],
        part_component_ids: Optional[List[int]] = None,
    ) -> Tuple[List[int], List[int]]:
        """
        拆分组件ID 为通过、驳回两组
        :param status: 审批状态
        :param component_ids: 申请单据中的组件ID
        :param part_component_ids: 部分审批时，部分审批的组件ID
        """
        if status == ApplyStatusEnum.APPROVED.value:
            return component_ids, []

        elif status == ApplyStatusEnum.REJECTED.value:
            return [], component_ids

        elif status == ApplyStatusEnum.PARTIAL_APPROVED.value:
            component_id_set = set(component_ids)
            part_component_id_set = set(part_component_ids or [])
            return list(component_id_set & part_component_id_set), list(component_id_set - part_component_id_set)

        raise ValueError(f"unsupported status: {status}")
