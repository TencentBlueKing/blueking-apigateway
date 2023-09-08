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
将 ESB 组件对应网关的类型设置为 SUPER_OFFICIAL_API，以便于网关向 ESB 传递所有请求参数
"""
import logging
from enum import Enum

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from apigateway.apps.esb.exceptions import EsbGatewayNotFound
from apigateway.apps.esb.utils import get_esb_gateway
from apigateway.biz.gateway import GatewayHandler
from apigateway.core.constants import GatewayTypeEnum

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    更新 esb 网关的认证配置

    - 更新网关类型：SUPER_OFFICIAL_API
    - 更新配置：不允许修改网关资源的认证配置
    """

    def handle(self, *args, **options):
        print(f"gateway(name={settings.BK_ESB_GATEWAY_NAME}) update auth config start")

        try:
            esb_gateway = get_esb_gateway()
        except EsbGatewayNotFound as err:
            raise CommandError(str(err))

        esb_gateway_auth_config = {
            "api_type": GatewayTypeEnum.SUPER_OFFICIAL_API,
            "allow_update_api_auth": False,
        }

        current_auth_config = GatewayHandler().get_current_gateway_auth_config(esb_gateway.id)
        if not self._should_update_auth_config(current_auth_config, esb_gateway_auth_config):
            print(f"gateway(name={settings.BK_ESB_GATEWAY_NAME}) auth config not changed, skip")
            return

        GatewayHandler().save_auth_config(esb_gateway.id, **esb_gateway_auth_config)

        print(f"gateway(name={settings.BK_ESB_GATEWAY_NAME}) auth config updated")

    def _should_update_auth_config(self, current_config, new_config) -> bool:
        """检查配置是否有差异，若有差异，则需要更新"""
        for key, value in new_config.items():
            if isinstance(value, Enum):
                value = value.value  # ruff: noqa: PLW2901

            if value != current_config.get(key):
                return True

        return False
