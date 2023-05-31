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
import copy
import math
from dataclasses import dataclass
from typing import List, Optional, Union

from django.utils.functional import cached_property
from pydantic import BaseModel, parse_obj_as

from apigateway.apps.esb.bkcore.models import AppComponentPermission, AppPermissionApplyRecord
from apigateway.apps.esb.helpers import get_component_doc_link
from apigateway.apps.permission.constants import ApplyStatusEnum, PermissionLevelEnum, PermissionStatusEnum


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
    component_permission: Optional[AppComponentPermission]
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


@dataclass
class ComponentPermissionBuilder:
    system_id: Optional[int]
    target_app_code: str

    def build(self, components: list) -> list:
        component_ids = [component["id"] for component in components]
        component_permission_map = self._get_component_permission_map(component_ids)
        component_permission_apply_status_map = AppPermissionApplyRecord.objects.get_component_permisson_status(
            self.target_app_code,
            self.system_id,
            [ApplyStatusEnum.PENDING.value],
        )

        components = copy.copy(components)
        for component in components:
            component["component_permission"] = component_permission_map.get(component["id"])
            component["component_permission_apply_status"] = component_permission_apply_status_map.get(
                component["id"], None
            )

        component_permissions = parse_obj_as(List[ComponentPermission], components)

        return [perm.as_dict() for perm in component_permissions]

    def _get_component_permission_map(self, component_ids: List[int]):
        return {
            perm.component_id: perm
            for perm in AppComponentPermission.objects.filter(
                bk_app_code=self.target_app_code,
                component_id__in=component_ids,
            )
        }
