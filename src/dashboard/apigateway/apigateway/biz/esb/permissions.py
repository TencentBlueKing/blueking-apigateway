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
import copy
import json
import math
from abc import ABCMeta
from typing import Any, Dict, List, Optional, Union

from django.conf import settings
from django.db import transaction
from django.utils.functional import cached_property
from pydantic import BaseModel, parse_obj_as

from apigateway.apps.esb.bkcore.models import (
    AppComponentPermission,
    AppPermissionApplyRecord,
    AppPermissionApplyStatus,
    ComponentResourceBinding,
    ComponentSystem,
)
from apigateway.apps.esb.helpers import get_component_doc_link
from apigateway.apps.esb.utils import get_esb_gateway
from apigateway.apps.permission.constants import (
    ApplyStatusEnum,
    GrantDimensionEnum,
    GrantTypeEnum,
    PermissionLevelEnum,
    PermissionStatusEnum,
)
from apigateway.apps.permission.models import AppPermissionApplyStatus as GatewayAppPermissionApplyStatus
from apigateway.apps.permission.models import AppResourcePermission
from apigateway.biz.permission import PermissionDimensionManager


class ComponentPermissionManager(metaclass=ABCMeta):
    """
    组件权限管理
    - 未使用网关 bk-esb 管理组件权限时，直接使用组件的权限数据，权限单据
    - 使用网关 bk-esb 管理组件权限时（开源版），通过 ComponentResourceBinding 将组件和网关 bk-esb 的资源关联起来，然后使用网关的权限数据，单据审批结果
    """

    @classmethod
    def get_manager(cls) -> "ComponentPermissionManager":
        if settings.USE_GATEWAY_BK_ESB_MANAGE_COMPONENT_PERMISSIONS and ComponentResourceBinding:
            return ComponentPermissionByGatewayManager()

        return ComponentPermissionByEsbManager()

    @transaction.atomic
    def create_apply_record(
        self,
        bk_app_code: str,
        system: ComponentSystem,
        component_ids: List[int],
        reason: str,
        expire_days: int,
        username: str,
    ) -> AppPermissionApplyRecord:
        """创建权限申请单"""
        instance = AppPermissionApplyRecord.objects.create_record(
            board=system.board,
            bk_app_code=bk_app_code,
            applied_by=username,
            system=system,
            component_ids=component_ids,
            status=ApplyStatusEnum.PENDING.value,
            reason=reason,
            expire_days=expire_days,
        )

        if AppPermissionApplyStatus is not None:
            # 删除应用-组件申请状态的历史记录，方便下面批量插入
            AppPermissionApplyStatus.objects.filter(
                bk_app_code=bk_app_code,
                system=system,
                component_id__in=component_ids,
            ).delete()
            AppPermissionApplyStatus.objects.batch_create(
                record=instance,
                bk_app_code=bk_app_code,
                system=system,
                component_ids=component_ids,
                status=ApplyStatusEnum.PENDING.value,
            )

        return instance

    def renew_permission(self, bk_app_code: str, component_ids: List[int], expire_days: int):
        """权限续期"""
        AppComponentPermission.objects.renew_permissions(
            bk_app_code,
            component_ids,
            expire_days,
        )

    def list_permissions(self, bk_app_code: str, components: List[Dict[str, Any]]):
        """权限列表"""
        component_ids = [component["id"] for component in components]
        component_permission_map = {
            perm.component_id: AppComponentPermissionData(
                expires_in=perm.expires_in,
            )
            for perm in AppComponentPermission.objects.filter(bk_app_code=bk_app_code, component_id__in=component_ids)
        }
        component_permission_apply_status_map = dict(
            AppPermissionApplyStatus.objects.filter(
                bk_app_code=bk_app_code,
                component_id__in=component_ids,
            ).values_list("component_id", "status")
        )

        components = copy.copy(components)
        for component in components:
            component["component_permission"] = component_permission_map.get(component["id"])
            component["component_permission_apply_status"] = component_permission_apply_status_map.get(
                component["id"], None
            )

        component_permissions = parse_obj_as(List[ComponentPermission], components)

        return [perm.as_dict() for perm in component_permissions]

    def patch_permission_apply_records(self, records: List[AppPermissionApplyRecord]):
        pass

    def _get_component_id_to_resource_id(self, component_ids: Optional[List[int]] = None) -> Dict[int, int]:
        queryset = ComponentResourceBinding.objects.all()

        if component_ids is not None:
            queryset = queryset.filter(component_id__in=component_ids)

        return dict(queryset.values_list("component_id", "resource_id"))


class ComponentPermissionByEsbManager(ComponentPermissionManager):
    """根据 ESB 数据，处理组件权限数据"""

    pass


class ComponentPermissionByGatewayManager(ComponentPermissionManager):
    """根据网关 bk-esb 权限数据，处理组件权限数据"""

    GATEWAY_APPLY_RECORD_ID_KEY = "gateway_apply_record_id"

    @transaction.atomic
    def create_apply_record(
        self,
        bk_app_code: str,
        system: ComponentSystem,
        component_ids: List[int],
        reason: str,
        expire_days: int,
        username: str,
    ):
        # 根据组件 ID 获取对应的资源 ID
        component_id_to_resource_id = self._get_component_id_to_resource_id(component_ids)
        if len(component_id_to_resource_id) != len(component_ids):
            missing_component_ids = set(component_ids) - set(component_id_to_resource_id.keys())
            raise ValueError(
                f"The gateway resources corresponding to the component were not found, missing components ids: {','.join(map(str, missing_component_ids))}."
                "Please contact the administrator."
            )

        # 创建组件权限申请单
        instance = super().create_apply_record(bk_app_code, system, component_ids, reason, expire_days, username)

        # 创建网关 bk-esb 的权限申请单
        manager = PermissionDimensionManager.get_manager(GrantDimensionEnum.RESOURCE.value)
        gateway_record = manager.create_apply_record(
            bk_app_code,
            get_esb_gateway(),
            list(component_id_to_resource_id.values()),
            GrantDimensionEnum.RESOURCE.value,
            reason,
            expire_days,
            username,
        )

        # 将网关权限单ID，记录到组件权限申请单，方便查询组件权限单据时，根据网关权限单获取单据实际的审批结果；
        # 因组件权限单不会审批，comment 不会用到，因此使用此字段保存
        instance.comment = json.dumps({self.GATEWAY_APPLY_RECORD_ID_KEY: gateway_record.id})
        instance.save()

        return instance

    def renew_permission(self, bk_app_code: str, component_ids: List[int], expire_days: int):
        """权限续期"""
        # 根据组件 ID 获取对应的资源 ID
        component_id_to_resource_id = self._get_component_id_to_resource_id(component_ids)
        if len(component_id_to_resource_id) != len(component_ids):
            missing_component_ids = set(component_ids) - set(component_id_to_resource_id.keys())
            raise ValueError(
                f"The gateway resources corresponding to the component were not found, missing component ids: {','.join(map(str, missing_component_ids))}."
                "Please contact the administrator."
            )

        # 续期组件权限
        super().renew_permission(bk_app_code, component_ids, expire_days)

        # 根据组件 ID 获取对应的资源 ID
        component_id_to_resource_id = self._get_component_id_to_resource_id(component_ids)

        # 续期网关资源权限
        AppResourcePermission.objects.renew_by_resource_ids(
            gateway=get_esb_gateway(),
            bk_app_code=bk_app_code,
            resource_ids=list(component_id_to_resource_id.values()),
            grant_type=GrantTypeEnum.RENEW.value,
            expire_days=expire_days,
        )

    def list_permissions(self, bk_app_code: str, components: List[Dict[str, Any]]):
        """权限列表"""
        component_ids = [component["id"] for component in components]
        component_id_to_resource_id = self._get_component_id_to_resource_id(component_ids)
        gateway = get_esb_gateway()

        resource_id_to_permission = {
            perm.resource_id: AppComponentPermissionData(
                expires_in=perm.expires_in,
            )
            for perm in AppResourcePermission.objects.filter(
                api=gateway,
                bk_app_code=bk_app_code,
                resource_id__in=component_id_to_resource_id.values(),
            )
        }

        resource_id_to_apply_status = dict(
            GatewayAppPermissionApplyStatus.objects.filter(
                bk_app_code=bk_app_code,
                api_id=gateway.id,
                grant_dimension=GrantDimensionEnum.RESOURCE.value,
            ).values_list("resource_id", "status")
        )

        components = copy.copy(components)
        for component in components:
            resource_id = component_id_to_resource_id.get(component["id"])
            component["component_permission"] = resource_id_to_permission.get(resource_id)
            component["component_permission_apply_status"] = resource_id_to_apply_status.get(resource_id, None)

        component_permissions = parse_obj_as(List[ComponentPermission], components)

        return [perm.as_dict() for perm in component_permissions]

    def patch_permission_apply_records(self, records: List[AppPermissionApplyRecord]):
        gateway_apply_record_ids = []
        for record in records:
            try:
                record.gateway_apply_record_id = json.loads(record.comment)[self.GATEWAY_APPLY_RECORD_ID_KEY]
            except Exception:
                continue
            gateway_apply_record_ids.append(record.gateway_apply_record_id)

        component_id_to_resource_id = self._get_component_id_to_resource_id()
        resource_id_to_component_id = {value: key for key, value in component_id_to_resource_id.items()}

        gateway_apply_records = {
            record.id: record for record in AppPermissionApplyRecord.objects.filter(id__in=gateway_apply_record_ids)
        }
        for record in records:
            gateway_apply_record_id = getattr(record, "gateway_apply_record_id", None)
            if not gateway_apply_record_id:
                continue

            gateway_record = gateway_apply_records.get(gateway_apply_record_id)
            if not gateway_record:
                continue

            record.status = gateway_record.status
            record.comment = gateway_record.comment
            record.handled_by = gateway_record.handled_by
            record.handled_time = gateway_record.handled_time
            record.handled_component_ids = {
                status: [
                    resource_id_to_component_id.get(resource_id)
                    for resource_id in resource_ids
                    if resource_id_to_component_id.get(resource_id)
                ]
                for status, resource_ids in gateway_record.handled_resource_ids()
            }


class AppComponentPermissionData(BaseModel):
    expires_in: int


class ComponentPermission(BaseModel):
    class Config:
        arbitrary_types_allowed = True
        keep_untouched = (cached_property,)

    id: int
    board: str
    name: str
    description: str
    description_en: Optional[str] = None
    system_name: str
    permission_level: str
    component_permission: Optional[AppComponentPermissionData]
    component_permission_apply_status: Optional[str]

    def as_dict(self):
        return {
            "board": self.board,
            "id": self.id,
            "name": self.name,
            "system_name": self.system_name,
            "description": self.description,
            "description_en": self.description_en,
            "permission_level": self.permission_level,
            "permission_status": self.permission_status,
            "expires_in": self.expires_in,
            "doc_link": self.doc_link,
        }

    @property
    def component_perm_required(self) -> bool:
        return self.permission_level != PermissionLevelEnum.UNLIMITED.value

    @property
    def doc_link(self):
        return get_component_doc_link(
            board=self.board,
            system_name=self.system_name,
            component_name=self.name,
        )

    @property
    def permission_status(self) -> str:
        if not self.component_perm_required or self.expires_in == math.inf:
            return PermissionStatusEnum.OWNED.value

        if self.component_permission_apply_status:
            return self.component_permission_apply_status

        if self.expires_in > 0:
            return PermissionStatusEnum.OWNED.value

        if self.expires_in > -math.inf:
            return PermissionStatusEnum.EXPIRED.value

        return PermissionStatusEnum.NEED_APPLY.value

    @cached_property
    def expires_in(self) -> Union[int, float]:
        if not self.component_perm_required:
            return math.inf

        return self._get_component_permission_expires_in()

    def _get_component_permission_expires_in(self) -> Union[int, float]:
        if not self.component_permission:
            return -math.inf

        return self._normalize_expires_in(self.component_permission.expires_in)

    def _normalize_expires_in(self, expires_in) -> Union[int, float]:
        # 指定的过期时间为None，表示不过期，过期时间设置为 math.inf
        if expires_in is None:
            return math.inf

        return expires_in
