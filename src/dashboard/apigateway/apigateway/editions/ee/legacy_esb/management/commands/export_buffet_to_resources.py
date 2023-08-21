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
"""将 PaaS2/ESB 中自定义组件配置，导出为网关 Swagger 资源配置文件"""
import os
from collections import defaultdict
from typing import Dict, List

from django.conf import settings
from django.core.management.base import BaseCommand

from apigateway.biz.resource_import.swagger.swagger import ResourceSwaggerExporter
from apigateway.core.constants import SwaggerFormatEnum
from apigateway.legacy_esb import models as legacy_models
from apigateway.utils.file import write_to_file


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument(
            "--file-path",
            type=str,
            dest="file_path",
            required=False,
            default=os.path.join(settings.BASE_DIR, "data/apigw-definitions/bk-esb-buffet-resources.yaml"),
        )

    def handle(self, file_path: str, *args, **options):
        content = self._convert_buffet_to_swagger()
        write_to_file(content, file_path)

    def _convert_buffet_to_swagger(self) -> str:
        """将旧版 ESB 自助接入组件，转换为网关资源 Swagger 配置"""
        buffet_components = legacy_models.ESBBuffetComponent.objects.all().order_by("id")
        buffet_resources = [component.to_resource() for component in buffet_components]
        buffet_resources = self._rename_duplicate_names(buffet_resources)
        exporter = ResourceSwaggerExporter()
        return exporter.to_swagger(buffet_resources, file_type=SwaggerFormatEnum.YAML.value)

    def _rename_duplicate_names(self, buffet_resources: List[dict]) -> List[dict]:
        """同一网关下资源名不能重复，如果 buffet 迁移资源的名称存在重复的情况，添加数字后缀"""
        resource_name_to_count: Dict[str, int] = defaultdict(int)
        for resource in buffet_resources:
            resource_name = resource["name"]
            resource_name_to_count[resource_name] += 1
            if resource_name_to_count[resource_name] > 1:
                resource["name"] = f"{resource_name}_{resource_name_to_count[resource_name]}"

        return buffet_resources
