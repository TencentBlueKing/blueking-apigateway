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
同步 ESB 免用户认证应用白名单到网关
- 网关 bk-esb 的插件：免用户认证应用白名单
"""
import logging
import re
from typing import List, Optional

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apigateway.apps.esb.bkcore.models import FunctionController
from apigateway.apps.esb.constants import FunctionControllerCodeEnum
from apigateway.apps.esb.exceptions import EsbGatewayNotFound
from apigateway.apps.esb.utils import get_esb_gateway
from apigateway.apps.plugin.constants import PluginBindingScopeEnum
from apigateway.apps.plugin.models import PluginBinding, PluginConfig, PluginType
from apigateway.core.models import Gateway, Stage
from apigateway.utils.django import get_object_or_None
from apigateway.utils.yaml import yaml_dumps

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    default_plugin_name = "verified user exempted apps"

    @transaction.atomic
    def handle(self, *args, **options):
        verified_user_exempted_apps = self._get_verified_user_exempted_apps()
        if not verified_user_exempted_apps:
            return

        try:
            esb_gateway = get_esb_gateway()
        except EsbGatewayNotFound as err:
            raise CommandError(str(err))

        plugin_type = PluginType.objects.get(code="bk-verified-user-exempted-apps")
        plugins = self._filter_or_create_plugins(esb_gateway, plugin_type)
        self._sync_to_plugins(plugin_type, plugins, verified_user_exempted_apps)

    def _get_verified_user_exempted_apps(self) -> Optional[List[str]]:
        obj = get_object_or_None(FunctionController, func_code=FunctionControllerCodeEnum.SKIP_USER_AUTH.value)
        if not obj:
            return None

        return re.findall(r"[^,;]+", obj.wlist)

    def _filter_or_create_plugins(self, esb_gateway: Gateway, plugin_type: PluginType) -> List[PluginConfig]:
        queryset = PluginConfig.objects.filter(api=esb_gateway, type=plugin_type)
        if queryset.exists():
            return list(queryset)

        plugin_config = PluginConfig.objects.create(
            api=esb_gateway,
            name=self.default_plugin_name,
            type=plugin_type,
            yaml="exempted_apps: []",
        )
        PluginBinding.objects.create_or_update_bindings(
            gateway=esb_gateway,
            config=plugin_config,
            scope_type=PluginBindingScopeEnum.STAGE.value,
            scope_ids=Stage.objects.get_ids(esb_gateway.id),
            username="admin",
        )

        return [plugin_config]

    def _sync_to_plugins(
        self, plugin_type: PluginType, plugins: List[PluginConfig], verified_user_exempted_apps: List[str]
    ):
        # ESB 中的白名单应用列表，转换为插件中的“全量资源”类型白名单
        for plugin in plugins:
            config = plugin.config
            app_code_to_config = {item["bk_app_code"]: item for item in config.get("exempted_apps", [])}
            for bk_app_code in verified_user_exempted_apps:
                app_code_to_config[bk_app_code] = {"bk_app_code": bk_app_code, "dimension": "api", "resource_ids": []}

            plugin.config = yaml_dumps(
                {"exempted_apps": sorted(app_code_to_config.values(), key=lambda x: x["bk_app_code"])}
            )
            plugin.save()
