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
import logging
from dataclasses import dataclass
from typing import Optional

from django.utils.translation import gettext_lazy
from rest_framework import permissions

from apigateway.controller.micro_gateway_config import MicroGatewayJWTAuth
from apigateway.core.models import MicroGateway

logger = logging.getLogger(__name__)


@dataclass
class MicroGatewayInstancePermission(permissions.BasePermission):
    """
    获取微网关实例并认证权限
    """

    message = gettext_lazy("当前微网关实例无权限调用")

    def has_permission(self, request, view):
        micro_gateway = self._get_micro_gateway(view)
        if not micro_gateway:
            return False

        instance_id = request.headers.get("X-Bk-Micro-Gateway-Instance-Id")
        instance_secret = request.headers.get("X-Bk-Micro-Gateway-Instance-Secret")
        if not (instance_id and instance_secret):
            return False

        if micro_gateway.id != instance_id:
            return False

        auth = MicroGatewayJWTAuth.from_micro_gateway_config(micro_gateway.config)
        if instance_secret != auth.secret_key:
            return False

        return True

    def _get_micro_gateway(self, view) -> Optional[MicroGateway]:
        """
        根据路径参数 instance_id 获取微网关对象
        如果 instance_id 不在路径参数中，则返回 None，忽略此权限验证
        """
        instance_id = view.kwargs.get("instance_id")
        if not instance_id:
            return None

        return MicroGateway.objects.filter(pk=instance_id).first()
