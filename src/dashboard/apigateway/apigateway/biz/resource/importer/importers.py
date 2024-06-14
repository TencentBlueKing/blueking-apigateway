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
from typing import Any, Dict, List, Optional

from apigateway.apps.label.models import APILabel
from apigateway.apps.plugin.constants import PluginBindingScopeEnum
from apigateway.biz.gateway_label import GatewayLabelHandler
from apigateway.biz.plugin.plugin_synchronizers import PluginConfigData, PluginSynchronizer
from apigateway.biz.resource import ResourceHandler
from apigateway.biz.resource.models import ResourceData
from apigateway.biz.resource.savers import ResourcesSaver
from apigateway.core.models import Gateway, Resource

from .legacy_synchronizers import LegacyTransformHeadersToPluginSynchronizer, LegacyUpstreamToBackendSynchronizer

logger = logging.getLogger(__name__)


class ResourcesImporter:
    def __init__(
        self,
        gateway: Gateway,
        resource_data_list: List[ResourceData],
        selected_resources: Optional[List[Dict[str, Any]]] = None,
        need_delete_unspecified_resources: bool = False,
        username: str = "",
    ):
        """
        资源导入

        :param resource_data_list: 资源数据列表
        :param selected_resources: 已选择的资源，为 None 表示不过滤；仅导入 resource_data_list 中，符合 selected_resources 过滤规则的资源
        :param need_delete_unspecified_resources: 是否删除未指定的资源；未指定的资源，指已创建的资源中，未被选中的资源
        """
        selected_resource_data_list = self._filter_selected_resource_data_list(selected_resources, resource_data_list)

        self.gateway = gateway
        self.resource_data_list = selected_resource_data_list
        self.need_delete_unspecified_resources = need_delete_unspecified_resources
        self.username = username

        self._deleted_resources: List[Dict[str, Any]] = []

    @classmethod
    def from_resources(
        cls,
        gateway: Gateway,
        resources: List[ResourceData],
        selected_resources: Optional[List[Dict[str, Any]]] = None,
        need_delete_unspecified_resources: bool = False,
        username: str = "",
    ):
        """
        :param resources: 资源数据，可由 swagger yaml 解析而来或自主构造；此方法中，将其转换为 ResourceData
        """
        return cls(
            gateway=gateway,
            resource_data_list=resources,
            selected_resources=selected_resources,
            need_delete_unspecified_resources=need_delete_unspecified_resources,
            username=username,
        )

    def import_resources(self):
        # 1. 删除未指定资源，即已创建的资源中，未被选中的资源
        if self.need_delete_unspecified_resources:
            self._deleted_resources = self._delete_unspecified_resources()

        # 2. 创建不存在的网关标签
        self._create_not_exist_labels()

        # 3. 补全标签 ID 数据
        self._complete_label_ids()

        # 4. [legacy upstreams] 创建或更新 backend，并替换资源对应的 backend
        self._sync_legacy_upstreams_to_backend_and_replace_resource_backend()

        # 5. 创建或更新资源
        self._create_or_update_resources()

        # 6. [legacy transform-headers] 将 transform-headers 转换为 bk-header-rewrite 插件，并绑定到资源
        self._sync_legacy_transform_headers_to_plugins()

        # 7. 导入插件
        self._sync_plugins()

    def get_selected_resource_data_list(self) -> List[ResourceData]:
        return self.resource_data_list

    def get_deleted_resources(self) -> List[Dict[str, Any]]:
        return self._deleted_resources

    def _filter_selected_resource_data_list(
        self, selected_resources: Optional[List[Dict[str, Any]]], resource_data_list: List[ResourceData]
    ) -> List[ResourceData]:
        # selected_resources 为 None 表示不过滤资源
        if selected_resources is None:
            return resource_data_list

        selected_resource_names = {item["name"] for item in selected_resources}
        return [resource_data for resource_data in resource_data_list if resource_data.name in selected_resource_names]

    def _delete_unspecified_resources(self) -> List[Dict[str, Any]]:
        """删除未指定的资源"""
        resource_ids = [
            resource_data.resource.id for resource_data in self.resource_data_list if resource_data.resource
        ]
        unspecified_resources = list(
            Resource.objects.filter(gateway=self.gateway)
            .exclude(id__in=resource_ids)
            .values("id", "name", "method", "path")
        )
        if not unspecified_resources:
            return []

        unspecified_resource_ids = [resource["id"] for resource in unspecified_resources]
        ResourceHandler.delete_resources(unspecified_resource_ids)

        return unspecified_resources

    def _create_not_exist_labels(self):
        """创建不存在的标签"""
        label_names = set()
        for resource_data in self.resource_data_list:
            label_names.update(resource_data.metadata.get("labels", []))

        GatewayLabelHandler.save_labels(self.gateway, list(label_names), self.username)

    def _complete_label_ids(self):
        """补全资源中的 label_ids 信息"""
        labels = dict(APILabel.objects.filter(gateway=self.gateway).values_list("name", "id"))
        for resource_data in self.resource_data_list:
            resource_data.label_ids = [labels[name] for name in resource_data.metadata.get("labels", [])]

    def _create_or_update_resources(self) -> List[Resource]:
        saver = ResourcesSaver(
            gateway=self.gateway,
            resource_data_list=self.resource_data_list,
            username=self.username,
        )
        return saver.save()

    def _sync_plugins(self):
        scope_id_to_plugin_configs: Dict[int, List[PluginConfigData]] = {}
        for resource_data in self.resource_data_list:
            if resource_data.plugin_configs is None:
                # 没有配置，既也要移除对应的插件配置
                scope_id_to_plugin_configs[resource_data.resource.id] = []
                continue

            scope_id_to_plugin_configs[resource_data.resource.id] = resource_data.plugin_configs

        synchronizer = PluginSynchronizer()
        synchronizer.sync(
            gateway_id=self.gateway.id,
            scope_type=PluginBindingScopeEnum.RESOURCE,
            scope_id_to_plugin_configs=scope_id_to_plugin_configs,
        )

    def _sync_legacy_upstreams_to_backend_and_replace_resource_backend(self):
        """根据 backend_config 中的 legacy_upstreams 创建 backend，并替换 resource_data_list 中资源关联的 backend"""
        synchronizer = LegacyUpstreamToBackendSynchronizer(self.gateway, self.resource_data_list, self.username)
        synchronizer.sync_backends_and_replace_resource_backend()

    def _sync_legacy_transform_headers_to_plugins(self):
        """根据 backend_config 中的 legacy_transform_headers 创建 bk-header-rewrite 插件，并绑定到资源"""
        synchronizer = LegacyTransformHeadersToPluginSynchronizer(self.gateway, self.resource_data_list, self.username)
        synchronizer.sync_plugins()
