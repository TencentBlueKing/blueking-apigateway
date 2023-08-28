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
import itertools
import json
import logging
import operator
import re
from typing import Any, Dict, List, Optional

from django.conf import settings
from django.utils.translation import gettext as _
from pydantic import BaseModel, Field, ValidationError

from apigateway.apps.esb.bkcore.models import ComponentResourceBinding
from apigateway.apps.permission.constants import PermissionLevelEnum
from apigateway.common.error_codes import error_codes
from apigateway.components.esb_components import get_client_by_username
from apigateway.core.constants import DEFAULT_BACKEND_NAME, HTTP_METHOD_ANY

logger = logging.getLogger(__name__)


class Component(BaseModel):
    id: Optional[int]
    method: str
    path: str
    name: str
    full_path: str
    is_public: bool
    description: str
    permission_level: str
    verified_user_required: bool
    system_name: str
    binding_resource_id: Optional[int] = None
    binding_resource_name: str = Field(default="")

    def to_resource(self) -> Dict[str, Any]:
        return {
            "id": self.binding_resource_id,
            "method": self.resource_method,
            "path": self.path,
            "match_subpath": False,
            "name": self.binding_resource_name,
            "description": self.description,
            "is_public": self.is_public,
            "backend_name": DEFAULT_BACKEND_NAME,
            "backend_config": {
                "method": self.resource_method,
                "path": self.full_path,
                "match_subpath": False,
                "timeout": 0,
            },
            "auth_config": {
                # 不需要权限校验的组件，在网关层也不需要认证应用，而是将应用认证结果传递给 ESB，由 ESB 处理
                "app_verified_required": self.permission_level != PermissionLevelEnum.UNLIMITED.value,
                "resource_perm_required": self.permission_level != PermissionLevelEnum.UNLIMITED.value,
                "auth_verified_required": self.verified_user_required,
            },
            "allow_apply_permission": self.is_public,
            "labels": [self.system_name],
            "metadata": {
                "system_name": self.system_name,
                "component_id": self.id,
                "component_name": self.name,
                "component_method": self.method,
                "component_path": self.path,
                "component_permission_level": self.permission_level,
            },
        }

    @property
    def resource_method(self) -> str:
        if not self.method:
            return HTTP_METHOD_ANY
        return self.method

    @property
    def component_key(self) -> str:
        if self.id:
            return str(self.id)
        elif self.path:
            return f"{self.method}:{self.path}"

        raise ValueError("component id or method+path cannot be empty at the same time")


class ComponentConvertor:
    def to_resources(self) -> List[Dict[str, Any]]:
        components = self._get_synchronized_components()
        self._validate_components(components)
        parsed_components = self._parse_components(components)
        self._enrich_resource_id(parsed_components)
        self._enrich_resource_name(parsed_components)
        return [parsed_component.to_resource() for parsed_component in parsed_components]

    def _get_synchronized_components(self) -> List[Dict[str, Any]]:
        """从 bk-esb 获取组件列表"""
        # 拉取待同步组件列表的接口，不能走网关，因注册时，该组件可能还没有注册到网关
        client = get_client_by_username("admin", endpoint=settings.BK_COMPONENT_API_INNER_URL)
        result = client.esb.get_synchronized_components()
        if not result["result"]:
            logger.error("failed to fetch components from esb, message=%s", result["message"])
            raise error_codes.INTERNAL.format(message=_("拉取待同步组件列表失败，请稍后重试。"), replace=True)
        return result["data"]

    def _parse_components(self, components: List[Dict[str, Any]]) -> List[Component]:
        parsed_components = []
        for component in components:
            # 为精确定位到出错的组件配置，未使用 parse_obj_as
            try:
                parsed_components.append(Component.parse_obj(component))
            except ValidationError:
                logger.exception(f"component configuration error, please check: {json.dumps(component)}")
                raise error_codes.INTERNAL.format(message=_("组件配置错误，请进行检查。"))
        return parsed_components

    def _validate_components(self, components: List[Dict[str, Any]]):
        components = sorted(components, key=operator.itemgetter("path"))
        for __, group in itertools.groupby(components, key=operator.itemgetter("path")):
            method_to_component = {component["method"]: component for component in group}
            if len(method_to_component) == 1:
                continue

            # method = "" 为 GET/POST 方法
            if "" in method_to_component:
                raise error_codes.INVALID_ARGUMENT.format(
                    _("同一组件路径下，请求方法包含 'GET/POST' 及其它请求方法，请将请求方法为 'GET/POST' 的组件，拆分为请求方法分别为 GET、POST 的两个组件。"),
                )

    def _enrich_resource_id(self, components: List[Component]) -> List[Component]:
        component_key_to_resource_id = ComponentResourceBinding.objects.get_component_key_to_resource_id()

        for component in components:
            component.binding_resource_id = component_key_to_resource_id.get(component.component_key)

        return components

    def _enrich_resource_name(self, components: List[Component]) -> List[Component]:
        unique_resource_name_set = set()

        for component in components:
            resource_name = f"{component.system_name}_{component.name}".replace("-", "_").lower()
            if resource_name in unique_resource_name_set:
                resource_name = "{method}_{name}".format(
                    method=component.resource_method.lower(),
                    name="_".join(re.findall(r"[a-z0-9]+", component.path.lower())),
                )

            component.binding_resource_name = resource_name
            unique_resource_name_set.add(resource_name)

        return components
