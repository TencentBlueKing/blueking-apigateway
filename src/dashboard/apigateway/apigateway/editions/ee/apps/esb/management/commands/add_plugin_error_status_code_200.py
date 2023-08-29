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
添加插件：网关错误使用HTTP状态码200(不推荐)
"""
import logging

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apigateway.apps.esb.exceptions import EsbGatewayNotFound
from apigateway.apps.esb.utils import get_esb_gateway
from apigateway.apps.plugin.constants import PluginBindingScopeEnum
from apigateway.apps.plugin.models import PluginBinding, PluginConfig, PluginType
from apigateway.core.models import Gateway, Stage
from apigateway.utils.yaml import yaml_dumps

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    plugin_type_code = "bk-status-rewrite"
    default_plugin_name = "Gateway error using HTTP status code 200"

    @transaction.atomic
    def handle(self, *args, **options):
        try:
            esb_gateway = get_esb_gateway()
        except EsbGatewayNotFound as err:
            raise CommandError(str(err))

        self._create_plugin_when_not_exist(esb_gateway)

    def _create_plugin_when_not_exist(self, esb_gateway: Gateway):
        plugin_type = self._get_plugin_type()
        plugin_config = PluginConfig.objects.filter(
            gateway=esb_gateway,
            type=plugin_type,
        )
        if plugin_config.exists():
            return

        plugin_config = PluginConfig.objects.create(
            gateway=esb_gateway,
            name=self.default_plugin_name,
            type=plugin_type,
            description="网关错误使用HTTP状态码200(不推荐)。比如，网关中的访问频率超限、蓝鲸应用认证失败、网关请求后端接口异常等出错情况，网关返回的响应将使用状态码 200。",
            description_en=(
                "Gateway error using HTTP status code 200 (not recommended). "
                "For example, if the access frequency in the gateway exceeds the limit, "
                "the authentication of the bk app fails, "
                "the gateway requests the backend interface to be abnormal, etc., "
                "the response returned by the gateway will use the status code 200."
            ),
            yaml=yaml_dumps({}),
        )
        for stage_id in Stage.objects.get_ids(esb_gateway.id):
            PluginBinding.objects.get_or_create(
                gateway=esb_gateway,
                scope_type=PluginBindingScopeEnum.STAGE.value,
                scope_id=stage_id,
                config__type=plugin_type,
                defaults={
                    "config": plugin_config,
                    "created_by": "admin",
                    "updated_by": "admin",
                },
            )

    def _get_plugin_type(self) -> PluginType:
        try:
            return PluginType.objects.get(code=self.plugin_type_code)
        except PluginType.DoesNotExist:
            raise CommandError(f"plugin type [{self.plugin_type_code}] not found, please load it first.")
