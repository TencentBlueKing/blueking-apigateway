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
from collections import defaultdict
from typing import Dict, List, Optional, Union

from django.utils.functional import cached_property
from pydantic import BaseModel, parse_obj_as

from apigateway.apps.permission.constants import (
    GrantDimensionEnum,
    PermissionLevelEnum,
    PermissionStatusEnum,
)
from apigateway.apps.permission.models import AppGatewayPermission, AppPermissionApplyStatus, AppResourcePermission
from apigateway.biz.released_resource import ReleasedResourceHandler
from apigateway.biz.resource_version import ResourceVersionHandler
from apigateway.core.models import Gateway, ReleasedResource, Resource


class ResourcePermission(BaseModel):
    class Config:
        arbitrary_types_allowed = True
        keep_untouched = (cached_property,)

    id: int
    name: str
    api_name: str
    gateway_id: Optional[int] = None
    description: str
    description_en: Optional[str] = None
    resource_perm_required: bool
    doc_link: str
    api_permission: Optional[AppGatewayPermission] = None
    resource_permission: Optional[AppResourcePermission] = None
    api_permission_apply_status: Optional[str] = ""
    resource_permission_apply_status: Optional[str] = ""

    def as_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "api_name": self.api_name,
            "gateway_id": self.gateway_id,
            "description": self.description,
            "description_en": self.description_en,
            "doc_link": self.doc_link,
            "permission_status": self.permission_status,
            "permission_level": self.permission_level,
            "expires_in": self.expires_in,
        }

    @property
    def permission_level(self):
        if self.resource_perm_required:
            return PermissionLevelEnum.NORMAL.value

        return PermissionLevelEnum.UNLIMITED.value

    @property
    def permission_status(self):
        # 如果资源不需要权限校验，则权限类型为：无限制，即默认拥有权限
        if not self.resource_perm_required:
            return PermissionStatusEnum.UNLIMITED.value

        # 如果权限记录中，有效期为永久有效；权限不需要再申请，优先展示
        if self.expires_in == math.inf:
            return PermissionStatusEnum.OWNED.value

        # 如果权限已有申请状态，如已拒绝、申请中；优先展示
        if self.api_permission_apply_status or self.resource_permission_apply_status:
            return self.api_permission_apply_status or self.resource_permission_apply_status

        # 有权限且未过期
        if self.expires_in > 0:
            return PermissionStatusEnum.OWNED.value

        # 有权限，但是已过期
        if self.expires_in > -math.inf:
            return PermissionStatusEnum.EXPIRED.value

        # 无权限，待申请
        return PermissionStatusEnum.NEED_APPLY.value

    @cached_property
    def expires_in(self) -> Union[int, float]:
        if not self.resource_perm_required:
            return math.inf

        return max(self._get_api_permission_expires_in(), self._get_resource_permission_expires_in())

    def _get_api_permission_expires_in(self) -> Union[int, float]:
        if not self.api_permission:
            return -math.inf

        return self._normalize_expires_in(self.api_permission.expires_in)

    def _get_resource_permission_expires_in(self) -> Union[int, float]:
        if not self.resource_permission:
            return -math.inf

        return self._normalize_expires_in(self.resource_permission.expires_in)

    def _normalize_expires_in(self, expires_in) -> Union[int, float]:
        # 指定的过期时间为None，表示不过期，过期时间设置为 math.inf
        if expires_in is None:
            return math.inf

        return expires_in


class ResourcePermissionBuilder:
    def __init__(self, gateway: Gateway, target_app_code: str):
        self.gateway = gateway
        self.target_app_code = target_app_code

        self.api_permission = self._get_api_permission()
        self.resource_permission_map = self._get_resource_permission_map()
        self.api_permission_apply_status = self._get_api_permission_apply_status()
        self.resource_permission_apply_status_map = self._get_resource_permission_apply_status_map()

    def build(self, resources: list) -> list:
        resources = copy.copy(resources)
        resource_ids = [resource["id"] for resource in resources]
        doc_links = ReleasedResourceHandler.get_latest_doc_link(resource_ids)

        for resource in resources:
            resource["api_name"] = self.gateway.name
            resource["gateway_id"] = self.gateway.id
            resource["doc_link"] = doc_links.get(resource["id"], "")
            resource["api_permission"] = self.api_permission
            resource["resource_permission"] = self.resource_permission_map.get(resource["id"])
            resource["api_permission_apply_status"] = self.api_permission_apply_status
            resource["resource_permission_apply_status"] = self.resource_permission_apply_status_map.get(
                resource["id"], ""
            )

        resource_permissions = parse_obj_as(List[ResourcePermission], resources)

        return [perm.as_dict() for perm in resource_permissions]

    def _get_api_permission(self):
        return AppGatewayPermission.objects.filter(
            gateway=self.gateway,
            bk_app_code=self.target_app_code,
        ).first()

    def _get_resource_permission_map(self):
        return {
            perm.resource_id: perm
            for perm in AppResourcePermission.objects.filter(
                gateway=self.gateway,
                bk_app_code=self.target_app_code,
            )
        }

    def _get_api_permission_apply_status(self):
        apply_status = AppPermissionApplyStatus.objects.filter(
            bk_app_code=self.target_app_code,
            gateway_id=self.gateway.id,
            grant_dimension=GrantDimensionEnum.API.value,
        ).first()

        if not apply_status:
            return ""

        return apply_status.status

    def _get_resource_permission_apply_status_map(self):
        return {
            apply_status.resource_id: apply_status.status
            for apply_status in AppPermissionApplyStatus.objects.filter(
                bk_app_code=self.target_app_code,
                gateway_id=self.gateway.id,
                grant_dimension=GrantDimensionEnum.RESOURCE.value,
            )
        }


class AppPermissionBuilder:
    """获取应用的网关资源权限"""

    def __init__(self, target_app_code: str):
        self.target_app_code = target_app_code

    def build(self) -> list:
        api_permission_map = self._get_api_permission_map()
        resource_permission_map = self._get_resource_permission_map()
        gateway_id_to_permission_apply_status = self._get_gateway_id_to_permission_apply_status()
        resource_id_to_permission_apply_status = self._get_resource_id_to_permission_apply_status()

        resource_map: defaultdict = defaultdict(dict)
        for gateway_id in api_permission_map:
            for resource in ResourceVersionHandler.get_released_public_resources(gateway_id):
                resource.update({"api_permission": api_permission_map.get(gateway_id)})
                resource_map[resource["id"]] = resource

        for resource in ReleasedResource.objects.filter_latest_released_resources(
            list(resource_permission_map.keys())
        ):
            resource.update({"resource_permission": resource_permission_map.get(resource["id"])})
            resource_map[resource["id"]].update(resource)

        resource_id_to_fields = {
            item["id"]: item
            for item in Resource.objects.filter(id__in=list(resource_map.keys())).values(
                "id", "gateway_id", "gateway__name"
            )
        }

        doc_links = ReleasedResourceHandler.get_latest_doc_link(list(resource_map.keys()))
        for resource_id, resource in resource_map.items():
            resource_fields = resource_id_to_fields.get(resource_id, {})
            resource["api_name"] = resource_fields.get("gateway__name", "")
            resource["gateway_id"] = resource_fields.get("gateway_id")
            resource["doc_link"] = doc_links.get(resource_id, "")

            api_permission_apply_status = gateway_id_to_permission_apply_status.get(
                resource_fields.get("gateway_id"), ""
            )
            resource["api_permission_apply_status"] = api_permission_apply_status
            if api_permission_map.get(resource["gateway_id"]):
                resource["resource_permission_apply_status"] = ""
            else:
                resource["resource_permission_apply_status"] = resource_id_to_permission_apply_status.get(
                    resource_id, ""
                )

        resource_permissions = parse_obj_as(List[ResourcePermission], list(resource_map.values()))
        return [perm.as_dict() for perm in resource_permissions]

    def _get_api_permission_map(self) -> Dict[int, AppGatewayPermission]:
        return {
            perm.gateway_id: perm
            for perm in AppGatewayPermission.objects.filter_public_permission_by_app(bk_app_code=self.target_app_code)
        }

    def _get_resource_permission_map(self) -> Dict[int, AppResourcePermission]:
        return {
            perm.resource_id: perm
            for perm in AppResourcePermission.objects.filter_public_permission_by_app(bk_app_code=self.target_app_code)
        }

    def _get_gateway_id_to_permission_apply_status(self):
        return dict(
            AppPermissionApplyStatus.objects.filter(
                bk_app_code=self.target_app_code,
                grant_dimension=GrantDimensionEnum.API.value,
            ).values_list("gateway_id", "status")
        )

    def _get_resource_id_to_permission_apply_status(self):
        return dict(
            AppPermissionApplyStatus.objects.filter(
                bk_app_code=self.target_app_code,
                grant_dimension=GrantDimensionEnum.RESOURCE.value,
            ).values_list("resource_id", "status")
        )
