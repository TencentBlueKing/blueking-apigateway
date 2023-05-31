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
from typing import Optional

from cachetools import TTLCache, cached
from django.conf import settings

from common.base_validators import BaseValidator
from common.errors import error_codes
from esb.bkcore.constants import PermissionLevelEnum
from esb.bkcore.models import AppComponentPermission


class ComponentPermValidator(BaseValidator):
    def validate(self, request):
        if getattr(request, "__esb_skip_comp_perm__", False):
            return

        if request.apigw.enabled:
            # 权限管理，托管到网关侧，如果是来自网关的请求，跳过校验
            return

        app_code = request.g.app_code
        channel_conf = request.g.channel_conf

        if not self._is_component_permission_required(channel_conf.get("id"), channel_conf.get("permission_level")):
            return

        if not self._has_permission(app_code, channel_conf["id"]):
            raise error_codes.APP_PERMISSION_DENIED.format_prompt(
                f"APP has no permission to access the component ({request.g.component_alias_name}) of "
                f"the system ({request.g.system_name}). "
                "The APP manager can go to the Developer Center and apply for permission to access the component"
            )

    def _is_component_permission_required(self, component_id: Optional[int], permission_level: Optional[str]) -> bool:
        if not component_id:
            return False

        if not permission_level or permission_level == PermissionLevelEnum.UNLIMITED.value:
            return False

        return True

    @cached(
        cache=TTLCache(
            maxsize=getattr(settings, "ESB_COMPONENT_PERMISSION_CACHE_MAXSIZE", 2000),
            ttl=getattr(settings, "ESB_COMPONENT_PERMISSION_CACHE_TTL_SECONDS", 300),
        )
    )
    def _has_permission(self, app_code: str, component_id: int) -> bool:
        return AppComponentPermission.objects.has_permission(app_code, component_id)
