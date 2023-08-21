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
from typing import Any, Dict, List

from attrs import define
from django.db import transaction

from apigateway.apps.esb.bkcore.models import ComponentResourceBinding
from apigateway.apps.esb.component.convertor import ComponentConvertor
from apigateway.biz.resource.importer.importer import ResourcesImporter
from apigateway.core.models import Gateway


@define(slots=False)
class ComponentSynchronizer:
    def get_importing_resources(self) -> List[Dict[str, Any]]:
        # 获取组件对应的资源配置
        component_convertor = ComponentConvertor()
        return component_convertor.to_resources()

    @transaction.atomic
    def sync_to_resources(self, gateway: Gateway, username: str) -> List[Dict[str, Any]]:
        """同步到资源，为组件创建对应的资源"""
        # 获取组件对应的资源配置
        importing_resources = self.get_importing_resources()

        # 导入资源
        resources_importer = ResourcesImporter(
            gateway=gateway,
            allow_overwrite=True,
            need_delete_unspecified_resources=True,
            username=username,
        )
        resources_importer.set_importing_resources(importing_resources)
        unspecified_resources = resources_importer.get_unspecified_resources()
        resources_importer.import_resources()

        # 同步组件 - 资源绑定关系
        ComponentResourceBinding.objects.sync(resources_importer.imported_resources)

        return unspecified_resources + importing_resources
