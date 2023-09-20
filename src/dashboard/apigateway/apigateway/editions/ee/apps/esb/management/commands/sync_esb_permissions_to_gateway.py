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
"""
同步组件权限到网关
"""
import logging
from typing import Any, Dict, List

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apigateway.apps.esb.bkcore.models import AppComponentPermission, ComponentResourceBinding, ESBChannel
from apigateway.apps.esb.exceptions import EsbGatewayNotFound
from apigateway.apps.esb.utils import get_esb_gateway
from apigateway.apps.permission.constants import GrantTypeEnum
from apigateway.apps.permission.models import AppResourcePermission
from apigateway.apps.permission.utils import calculate_expires
from apigateway.core.models import Gateway

logger = logging.getLogger(__name__)


rewrite_components = {
    "/v2/cmsi/send_voice_msg/": "/cmsi/send_voice_msg/",
    "/v2/cmsi/send_mail/": "/cmsi/send_mail/",
    "/v2/cmsi/send_sms/": "/cmsi/send_sms/",
    "/v2/cmsi/send_weixin/": "/cmsi/send_weixin/",
    "/v2/cmsi/get_msg_type/": "/cmsi/get_msg_type/",
    "/v2/cmsi/send_msg/": "/cmsi/send_msg/",
}


class Command(BaseCommand):
    @transaction.atomic
    def handle(self, *args, **options):
        try:
            esb_gateway = get_esb_gateway()
        except EsbGatewayNotFound as err:
            raise CommandError(str(err))

        component_permissions = self._get_component_permissions()
        resource_permissions = self._convert_to_resource_permissions(component_permissions)
        resource_permissions.extend(self._get_resource_permissions_for_rewrite_components())
        self._add_permissions_to_gateway(esb_gateway, resource_permissions)

    def _get_component_permissions(self) -> List[Dict[str, Any]]:
        return list(AppComponentPermission.objects.values("bk_app_code", "component_id"))

    def _convert_to_resource_permissions(self, component_permissions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        component_id_to_resource_id = self._get_component_id_to_resource_id()
        resource_permissions = []
        for permission in component_permissions:
            component_id = permission["component_id"]
            resource_id = component_id_to_resource_id.get(component_id)
            if not resource_id:
                continue

            resource_permissions.append(
                {
                    "bk_app_code": permission["bk_app_code"],
                    "resource_id": resource_id,
                }
            )

        return resource_permissions

    def _get_resource_permissions_for_rewrite_components(self):
        # 获取 path 对应的组件 ID，资源 ID
        source_path = list(rewrite_components.keys())
        target_path = list(rewrite_components.values())

        path_to_binding_fields = {
            item["component_path"]: item
            for item in ComponentResourceBinding.objects.filter(component_path__in=source_path + target_path).values(
                "component_path", "component_id", "resource_id"
            )
        }

        target_component_id_to_path = {
            item["id"]: item["path"] for item in ESBChannel.objects.filter(path__in=target_path).values("id", "path")
        }

        target_path_to_source_path = {
            target_path: source_path for source_path, target_path in rewrite_components.items()
        }

        target_component_permissions = AppComponentPermission.objects.filter(
            component_id__in=target_component_id_to_path.keys()
        ).values("bk_app_code", "component_id")
        resource_permissions = []
        for permission in target_component_permissions:
            # target component id => target path => source path => source resource id
            target_component_id = permission["component_id"]
            target_path = target_component_id_to_path[target_component_id]
            source_path = target_path_to_source_path[target_path]
            binding_fields = path_to_binding_fields[source_path]
            resource_permissions.append(
                {
                    "resource_id": binding_fields["resource_id"],
                    "bk_app_code": permission["bk_app_code"],
                }
            )

        return resource_permissions

    def _add_permissions_to_gateway(self, esb_gateway: Gateway, resource_permissions: List[Dict[str, Any]]):
        """只添加不存在的资源权限，不更新已存在的权限"""
        existed_resource_permissions = self._get_current_resource_permissions(esb_gateway)
        new_resource_permissions = []
        for permission in resource_permissions:
            key = f"{permission['bk_app_code']}:{permission['resource_id']}"
            if key not in existed_resource_permissions:
                new_resource_permissions.append(
                    AppResourcePermission(
                        bk_app_code=permission["bk_app_code"],
                        gateway=esb_gateway,
                        resource_id=permission["resource_id"],
                        # 永久有效，目前组件权限中的有效期，实际并未使用
                        expires=calculate_expires(None),
                        grant_type=GrantTypeEnum.RENEW.value,
                    )
                )

        AppResourcePermission.objects.bulk_create(new_resource_permissions, batch_size=50)

    def _get_component_id_to_resource_id(self):
        return dict(ComponentResourceBinding.objects.values_list("component_id", "resource_id"))

    def _get_current_resource_permissions(self, esb_gateway: Gateway) -> Dict[str, bool]:
        permissions = AppResourcePermission.objects.filter(gateway=esb_gateway).values("bk_app_code", "resource_id")
        return {f"{permission['bk_app_code']}:{permission['resource_id']}": True for permission in permissions}
