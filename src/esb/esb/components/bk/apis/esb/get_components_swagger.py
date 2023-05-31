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
import operator
from collections import defaultdict

from django import forms
from django.conf import settings
from django.http import HttpResponse

from common.base_utils import yaml_dumps
from common.constants import API_TYPE_Q
from common.forms import BaseComponentForm
from components.component import Component
from esb.bkcore.constants import DataTypeEnum
from esb.bkcore.models import ESBChannel

from .toolkit import configs


class GetComponentsSwagger(Component):
    """以 swagger 形式获取组件列表，用于生成组件 SDK"""

    sys_name = configs.SYSTEM_NAME
    api_type = API_TYPE_Q

    ignore_systems = [
        "BK_DOCS_CENTER",
        "BSCP",
        "GSEKIT",
        "IAM",
        "LOG_SEARCH",
        # 推荐用 JOBV3
        "JOB",
    ]

    class Form(BaseComponentForm):
        token = forms.CharField(label="token", required=True)
        version = forms.CharField(label="sdk version", required=False)

        def clean(self):
            if self.cleaned_data["token"] != getattr(settings, "ESB_COMPONENTS_SWAGGER_TOKEN", ""):
                raise forms.ValidationError("parameter token error")

            self.cleaned_data["version"] = self.cleaned_data.get("version") or "1.0.0"

            return self.cleaned_data

    def handle(self):
        # TODO: 待支持 board 后，切换为当前 board 变量
        components = self._get_available_components(board="default")
        components = self._deduplicate_and_enrich_components(components)
        yaml_swagger = self._generate_swagger(components, self.form_data["version"])

        response = HttpResponse(yaml_swagger)
        response["Content-Type"] = "application/octet-stream"
        response["Content-Disposition"] = 'attachment;filename="bk_esb_components.yaml"'

        # support CORS
        response["Access-Control-Allow-Origin"] = "*"
        response["Access-Control-Allow-Headers"] = "Content-Type,Content-Disposition"
        response["Access-Control-Allow-Methods"] = "GET,POST,OPTIONS"
        response["Access-Control-Expose-Headers"] = "Content-Type,Content-Disposition"

        self.response.payload = response

    def _get_available_components(self, board):
        """获取公开、可用的组件"""
        queryset = ESBChannel.objects.filter(
            board=board,
            is_public=True,
            is_active=True,
            data_type=DataTypeEnum.OFFICIAL_PUBLIC.value,
        )

        components = []
        for component in queryset:
            method = component.config.get("suggest_method") or component.method
            if not method or component.config.get("no_sdk"):
                continue

            if component.system.name in self.ignore_systems:
                continue

            components.append(
                {
                    "name": component.name,
                    "description": component.description,
                    "method": method,
                    "path": component.path,
                    "system_name": component.system.name,
                }
            )

        return sorted(components, key=operator.itemgetter("system_name", "name"))

    def _deduplicate_and_enrich_components(self, components):
        path_mapping = {}
        for component in components:
            # /v2/ 开头为新版组件，其配置优先级更高
            if component["path"].startswith("/v2/"):
                component["path"] = component["path"][3:]
                # 去除 /v2，统一调整为 {bk_api_ver}
                path_mapping[component["path"]] = component
            elif component["path"] not in path_mapping:
                path_mapping[component["path"]] = component

        deduplicated_components = path_mapping.values()
        for component in deduplicated_components:
            # 将 path 更新为 sdk 中需要的完整路径
            component["path"] = "/api/c/compapi{bk_api_ver}" + component["path"]

        return deduplicated_components

    def _generate_swagger(self, components, api_version):
        content = {
            "swagger": "2.0",
            "basePath": "/",
            "info": {
                "version": api_version,
                "title": "ESB Components",
            },
            "schemes": ["http"],
            "paths": dict(self._generate_swagger_paths(components)),
        }
        return yaml_dumps(content)

    def _generate_swagger_paths(self, components):
        paths = defaultdict(dict)
        for component in components:
            method = component["method"].lower()
            path = component["path"]
            paths[path][method] = {
                "operationId": f'{component["system_name"].lower()}_{component["name"]}',
                "description": component["description"],
                "tags": [component["system_name"].lower()],
                "x-component-name": component["name"],
            }

        return paths
