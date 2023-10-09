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
from collections import defaultdict
from typing import Any, Dict, List, Optional

from django.utils.translation import gettext as _

from apigateway.apps.label.models import APILabel
from apigateway.biz.gateway import GatewayHandler
from apigateway.biz.gateway_label import GatewayLabelHandler
from apigateway.biz.resource import ResourceHandler
from apigateway.biz.resource.models import ResourceAuthConfig, ResourceBackendConfig, ResourceData
from apigateway.biz.resource.savers import ResourcesSaver
from apigateway.core.constants import DEFAULT_BACKEND_NAME, HTTP_METHOD_ANY
from apigateway.core.models import Backend, Gateway, Resource

from .legacy_synchronizers import LegacyTransformHeadersToPluginSynchronizer, LegacyUpstreamToBackendSynchronizer

logger = logging.getLogger(__name__)


class ResourceDataConvertor:
    def __init__(self, gateway: Gateway, resources: List[Dict[str, Any]]):
        """
        将资源数据转换为 ResourceData

        :param resources: 资源数据，可由 swagger yaml 解析而来或者自主构造。样例：
            {
                "id": 1,  # 可为 None
                "method": "GET",
                "path": "/v1/test",
                "match_subpath": False,
                "name": "test",
                "description": "test",
                "is_public": True,
                "allow_apply_permission": True,
                "labels": ["label1", "label2"],
                "auth_config": {
                    "app_verified_required": True,
                    "auth_verified_required": True,
                    "resource_perm_required": True,
                },
                "backend_name": "default",
                "backend_config": {
                    "method": "GET",
                    "path": "/v1/test",
                    "match_subpath": False,
                    "timeout": 0
                },
            }
        """
        self.gateway = gateway
        self.resources = resources

    def convert(self) -> List[ResourceData]:
        resource_objs = list(Resource.objects.filter(gateway=self.gateway))
        resource_id_to_resource_obj = {resource.id: resource for resource in resource_objs}
        resource_key_to_resource_obj = {f"{resource.method}:{resource.path}": resource for resource in resource_objs}
        backends = {backend.name: backend for backend in Backend.objects.filter(gateway=self.gateway)}

        resource_data_list = []
        for resource in self.resources:
            resource_obj = self._get_resource_obj(resource, resource_id_to_resource_obj, resource_key_to_resource_obj)

            metadata = resource.get("metadata", {})
            # 是否为新增资源
            metadata["is_created"] = not resource_obj
            # 标签名
            metadata["labels"] = resource.get("labels", [])

            backend_name = resource.get("backend_name", DEFAULT_BACKEND_NAME)
            backend = backends.get(backend_name)
            if not backend:
                raise ValueError(_("后端服务 (name={name}) 不存在。").format(name=backend_name))

            resource_data_list.append(
                ResourceData(
                    resource=resource_obj,
                    name=resource["name"],
                    description=resource.get("description", ""),
                    description_en=resource.get("description_en", None),
                    method=resource["method"],
                    path=resource["path"],
                    match_subpath=resource.get("match_subpath", False),
                    is_public=resource.get("is_public", True),
                    allow_apply_permission=resource.get("allow_apply_permission", True),
                    auth_config=ResourceAuthConfig.parse_obj(resource.get("auth_config", {})),
                    backend=backend,
                    backend_config=ResourceBackendConfig.parse_obj(resource["backend_config"]),
                    # 在导入时，根据 metadata 中的 labels 创建 GatewayLabel，并补全 label_ids 数据
                    label_ids=[],
                    metadata=metadata,
                )
            )

        return resource_data_list

    def _get_resource_obj(
        self,
        resource: Dict[str, Any],
        resource_id_to_resource_obj: Dict[int, Resource],
        resource_key_to_resource_obj: Dict[str, Resource],
    ) -> Optional[Resource]:
        if resource.get("id") is not None:
            if resource["id"] not in resource_id_to_resource_obj:
                raise ValueError("资源 (id={id}) 不存在。".format(id=resource["id"]))

            return resource_id_to_resource_obj[resource["id"]]

        key = f"{resource['method']}:{resource['path']}"
        return resource_key_to_resource_obj.get(key)


class ResourceImportValidator:
    """校验导入的资源是否合法"""

    def __init__(
        self,
        gateway: Gateway,
        resource_data_list: List[ResourceData],
        need_delete_unspecified_resources: bool = False,
    ):
        """
        :param resource_data_list: 资源数据列表
        :param need_delete_unspecified_resources: 是否删除未指定资源；已创建，但未在 resource_data_list 中指定的资源，即为未指定资源
        """
        self.gateway = gateway
        self.resource_data_list = resource_data_list
        self.need_delete_unspecified_resources = need_delete_unspecified_resources
        self._unchanged_resources = self._get_unchanged_resources()

    def validate(self):
        self._validate_resources()
        self._validate_method_path()
        self._validate_method()
        self._validate_name()
        self._validate_match_subpath()
        self._validate_resource_count()

    def _get_unchanged_resources(self) -> List[Dict[str, Any]]:
        """
        获取不会发生变化的资源，便于校验数据；不会发生变化的资源 + resource_data_list 中资源，即为最终的全量资源
        - 如果需要删除未指定的资源，则所有资源均会变化，返回空列表
        - 如果不删除未指定的资源，则未指定的资源，即为不会变化的资源
        """
        if self.need_delete_unspecified_resources:
            return []

        return self.get_unspecified_resources()

    def get_unspecified_resources(self) -> List[Dict[str, Any]]:
        """获取未指定的资源。未指定的资源，指已创建的资源中，未被选中的资源"""
        specified_resource_ids = [
            resource_data.resource.id for resource_data in self.resource_data_list if resource_data.resource
        ]
        return list(
            Resource.objects.filter(gateway=self.gateway)
            .exclude(id__in=specified_resource_ids)
            .values("id", "name", "method", "path")
        )

    def _validate_resources(self):
        """校验资源数据列表中，是否存在重复的资源"""
        resource_ids = set()
        for resource_data in self.resource_data_list:
            if not resource_data.resource:
                continue

            resource_id = resource_data.resource.id
            if resource_id in resource_ids:
                raise ValueError(
                    _("资源重复，id={resource_id}, method={method}, path={path} 在当前配置数据中被多次使用，请检查。").format(
                        resource_id=resource_id,
                        method=resource_data.method,
                        path=resource_data.path,
                    )
                )

            resource_ids.add(resource_id)

    def _validate_method_path(self):
        """校验 method + path 不能重复"""
        unchanged_resource_keys = {
            f"{resource['method']}:{resource['path']}" for resource in self._unchanged_resources
        }
        resource_keys = set()

        for resource_data in self.resource_data_list:
            key = f"{resource_data.method}:{resource_data.path}"
            if key in unchanged_resource_keys:
                raise ValueError(
                    _("资源请求方法+请求路径重复，method={method}, path={path} 已被现有资源占用，请检查。").format(
                        method=resource_data.method, path=resource_data.path
                    )
                )

            if key in resource_keys:
                raise ValueError(
                    _("资源请求方法+请求路径重复，method={method}, path={path} 在当前配置数据中被多次使用，请检查。").format(
                        method=resource_data.method, path=resource_data.path
                    )
                )

            resource_keys.add(key)

    def _validate_method(self):
        """
        校验请求方法
        - 同一路径下，如果存在 ANY 请求方法，则不能存在其它请求方法
        """
        path_to_methods = defaultdict(list)
        for resource in self._unchanged_resources:
            path_to_methods[resource["path"]].append(resource["method"])
        for resource_data in self.resource_data_list:
            path_to_methods[resource_data.path].append(resource_data.method)

        for path, methods in path_to_methods.items():
            if HTTP_METHOD_ANY in methods and len(methods) > 1:
                raise ValueError(
                    _("当前配置数据及已有资源数据中，请求路径 {path} 下，同时存在 {method_any} 及其它请求方法。").format(
                        path=path, method_any=HTTP_METHOD_ANY
                    )
                )

    def _validate_name(self):
        """校验资源名称不能重复"""
        unchanged_resource_names = {item["name"] for item in self._unchanged_resources}
        resource_names = set()

        for resource_data in self.resource_data_list:
            if resource_data.name in unchanged_resource_names:
                raise ValueError(_("资源名称重复，name={name} 已被现有资源占用，请检查。").format(name=resource_data.name))

            if resource_data.name in resource_names:
                raise ValueError(_("资源名称重复，name={name} 在当前配置数据中被多次使用，请检查。").format(name=resource_data.name))

            resource_names.add(resource_data.name)

    def _validate_match_subpath(self):
        for resource_data in self.resource_data_list:
            if resource_data.match_subpath != resource_data.backend_config.match_subpath:
                raise ValueError(
                    _(
                        "当前配置数据中，资源 method={method}, path={path}，前端配置中的 match_subpath 与后端配置中的 match_subpath 值必需相同。"
                    ).format(method=resource_data.method, path=resource_data.path)
                )

    def _validate_resource_count(self):
        count = len(self.resource_data_list) + len(self._unchanged_resources)
        max_resource_count = GatewayHandler.get_max_resource_count(self.gateway.name)
        if count > max_resource_count:
            raise ValueError(_("每个网关最多创建 {count} 个资源。").format(count=max_resource_count))


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
        validator = ResourceImportValidator(
            gateway=gateway,
            resource_data_list=selected_resource_data_list,
            need_delete_unspecified_resources=need_delete_unspecified_resources,
        )
        validator.validate()

        self.gateway = gateway
        self.resource_data_list = selected_resource_data_list
        self.need_delete_unspecified_resources = need_delete_unspecified_resources
        self.username = username

        self._deleted_resources: List[Dict[str, Any]] = []

    @classmethod
    def from_resources(
        cls,
        gateway: Gateway,
        resources: List[Dict[str, Any]],
        selected_resources: Optional[List[Dict[str, Any]]] = None,
        need_delete_unspecified_resources: bool = False,
        username: str = "",
    ):
        """
        :param resources: 资源数据，可由 swagger yaml 解析而来或自主构造；此方法中，将其转换为 ResourceData
        """
        resource_data_list = ResourceDataConvertor(gateway, resources).convert()
        return cls(
            gateway=gateway,
            resource_data_list=resource_data_list,
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
        self._create_or_update_backends()

        # 5. 创建或更新资源
        self._create_or_update_resources()

        # 6. [legacy transform-headers] 将 transform-headers 转换为 plugin，并绑定到资源
        self._create_or_update_header_rewrite_plugins()

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

    def _create_or_update_backends(self):
        """根据 backend_config 中的 legacy_upstreams 创建 backend，并替换 resource_data_list 中资源关联的 backend"""
        synchronizer = LegacyUpstreamToBackendSynchronizer(self.gateway, self.resource_data_list, self.username)
        synchronizer.sync_backends_and_replace_resource_backend()

    def _create_or_update_header_rewrite_plugins(self):
        """根据 backend_config 中的 legacy_transform_headers 创建 bk-header-rewrite 插件，并绑定到资源"""
        synchronizer = LegacyTransformHeadersToPluginSynchronizer(self.gateway, self.resource_data_list, self.username)
        synchronizer.sync_plugins()
