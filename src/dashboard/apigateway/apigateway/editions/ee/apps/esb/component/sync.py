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

from django.db import transaction

from apigateway.apps.esb.component.convertor import ComponentConvertor

# FIXME: 将 sync 中内容挪到 biz 模块，apps 模块不能引用 biz 模块内容
from apigateway.biz.esb.component_resource_binding import ComponentResourceBindingHandler
from apigateway.biz.resource.importer import ResourceDataConvertor, ResourcesImporter
from apigateway.core.models import Gateway


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

        # 导入资源】

        resource_data_list = ResourceDataConvertor(gateway, importing_resources).convert()

        resources_importer = ResourcesImporter.from_resources(
            gateway=gateway,
            resources=resource_data_list,
            selected_resources=None,
            need_delete_unspecified_resources=True,
            username=username,
        )
        resources_importer.import_resources()

        deleted_resources = resources_importer.get_deleted_resources()
        resource_data_list = resources_importer.get_selected_resource_data_list()

        # 同步组件 - 资源绑定关系
        ComponentResourceBindingHandler.sync(resource_data_list)

        return deleted_resources + [resource_data.snapshot() for resource_data in resource_data_list]
