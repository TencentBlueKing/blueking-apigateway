#  -*- coding: utf-8 -*-
#  #
#  TencentBlueKing is pleased to support the open source community by making
#  蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
#  Copyright (C) 2017 THL A29 Limited, a Tencent company. All rights reserved.
#  Licensed under the MIT License (the "License"); you may not use this file except
#  in compliance with the License. You may obtain a copy of the License at
#  #
#      http://opensource.org/licenses/MIT
#  #
#  Unless required by applicable law or agreed to in writing, software distributed under
#  the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND,
#  either express or implied. See the License for the specific language governing permissions and
#  limitations under the License.
#  #
#  We undertake not to change the open source license (MIT license) applicable
#  to the current version of the project delivered to anyone in the future.
#  #
from collections import defaultdict
from typing import Any, Dict, List

from blue_krill.cubing_case import shortcuts
from django.conf import settings
from django.utils.translation import gettext as _

from apigateway.apps.label.models import APILabel
from apigateway.apps.plugin.models import PluginType
from apigateway.biz.gateway import GatewayHandler
from apigateway.biz.resource.importer.schema import SchemaValidateErr
from apigateway.biz.resource.models import ResourceData
from apigateway.common.plugin.validator import PluginConfigYamlValidator
from apigateway.core.constants import HTTP_METHOD_ANY
from apigateway.core.models import Backend, Gateway, Resource
from apigateway.utils.list import get_duplicate_items


class ResourceImportValidator:
    """校验导入的资源是否合法(逻辑上进行校验)"""

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
        self.schema_validate_result: List[SchemaValidateErr] = []

    def validate(self):
        self._validate_method_path()
        self._validate_method()
        self._validate_name()
        self._validate_match_subpath()
        self._validate_resource_count()
        self._validate_label_count()
        self._validate_plugin_type()
        self._validate_plugin_config()
        self._validate_backend()
        return self.schema_validate_result

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

    def _validate_method_path(self):
        """校验 method + path 不能重复"""
        unchanged_resource_keys = {
            f"{resource['method']}:{resource['path']}" for resource in self._unchanged_resources
        }
        resource_keys = set()
        for resource_data in self.resource_data_list:
            key = f"{resource_data.method}:{resource_data.path}"
            if key in unchanged_resource_keys:
                validate_err = SchemaValidateErr(
                    _("资源请求方法+请求路径重复，method={method}, path={path} 已被现有资源占用，请检查。").format(
                        method=resource_data.method, path=resource_data.path
                    ),
                    f"$.paths.{resource_data.path}",
                    absolute_path=[],
                )
                self.schema_validate_result.append(validate_err)
            if key in resource_keys:
                validate_err = SchemaValidateErr(
                    _(
                        "资源请求方法+请求路径重复，method={method}, path={path} 在当前配置数据中被多次使用，请检查。"
                    ).format(method=resource_data.method, path=resource_data.path),
                    f"$.paths.{resource_data.path}",
                    absolute_path=[],
                )
                self.schema_validate_result.append(validate_err)

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
                validate_err = SchemaValidateErr(
                    _(
                        "当前配置数据及已有资源数据中，请求路径 {path} 下，同时存在 {method_any} 及其它请求方法。"
                    ).format(path=path, method_any=HTTP_METHOD_ANY),
                    f"$.paths.{path}",
                    absolute_path=[],
                )
                self.schema_validate_result.append(validate_err)

    def _validate_name(self):
        """校验资源名称不能重复"""
        unchanged_resource_names = {item["name"] for item in self._unchanged_resources}
        lower_resource_names = {
            shortcuts.to_lower_dash_case(obj.name): obj.id for obj in Resource.objects.filter(gateway=self.gateway)
        }
        resource_names = set()

        for resource_data in self.resource_data_list:
            if resource_data.name in unchanged_resource_names:
                validate_err = SchemaValidateErr(
                    _("资源名称重复，operationId={name} 已被现有资源占用，请检查。").format(name=resource_data.name),
                    f"$.paths.{resource_data.path}.{resource_data.method.lower()}.operationId",
                    absolute_path=[],
                )
                self.schema_validate_result.append(validate_err)

            if resource_data.name in resource_names:
                validate_err = SchemaValidateErr(
                    _("资源名称重复，operationId={name} 在当前配置数据中被多次使用，请检查。").format(
                        name=resource_data.name
                    ),
                    f"$.paths.{resource_data.path}.{resource_data.method.lower()}.operationId",
                    absolute_path=[],
                )
                self.schema_validate_result.append(validate_err)

            lower_name = shortcuts.to_lower_dash_case(resource_data.name)
            resource_id = lower_resource_names.get(lower_name)
            if resource_id and (not resource_data.resource or resource_data.resource.id != resource_id):
                validate_err = SchemaValidateErr(
                    _(
                        "网关下资源名称 {name} 或其同名驼峰名称已被占用（如 get_foo 会与 getFoo 冲突），请使用其他命名，建议使用统一的命名格式。"
                    ).format(name=resource_data.name),
                    f"$.paths.{resource_data.path}.{resource_data.method.lower()}.operationId",
                    absolute_path=[],
                )
                self.schema_validate_result.append(validate_err)

            resource_names.add(resource_data.name)

    def _validate_match_subpath(self):
        for resource_data in self.resource_data_list:
            if resource_data.match_subpath != resource_data.backend_config.match_subpath:
                validate_err = SchemaValidateErr(
                    _(
                        "当前配置数据中，资源 method={method}, path={path}，前端配置中的 match_subpath 与后端配置中的 match_subpath 值必需相同。"
                    ).format(method=resource_data.method, path=resource_data.path),
                    f"$.paths.{resource_data.path}.{resource_data.method.lower()}.match_subpath",
                    absolute_path=[],
                )
                self.schema_validate_result.append(validate_err)

    def _validate_resource_count(self):
        count = len(self.resource_data_list) + len(self._unchanged_resources)
        max_resource_count = GatewayHandler.get_max_resource_count(self.gateway.name)
        if count > max_resource_count:
            validate_err = SchemaValidateErr(
                _("每个网关最多创建 {count} 个资源。").format(count=max_resource_count), "$.paths", absolute_path=[]
            )
            self.schema_validate_result.append(validate_err)

    def _validate_label_count(self):
        label_names = set()
        for resource_data in self.resource_data_list:
            label_names.update(resource_data.metadata.get("labels", []))

        if not label_names:
            return

        exist_label_names = set(APILabel.objects.filter(gateway=self.gateway).values_list("name", flat=True))
        if len(label_names | exist_label_names) > settings.MAX_LABEL_COUNT_PER_GATEWAY:
            validate_err = SchemaValidateErr(
                _("每个网关最多创建 {max_count} 个标签。").format(max_count=settings.MAX_LABEL_COUNT_PER_GATEWAY),
                "$.paths.*.tages",
                absolute_path=[],
            )
            self.schema_validate_result.append(validate_err)

    def _validate_plugin_type(self):
        """
        校验插件类型
        - 1. 资源绑定的插件，插件类型不能重复
        - 2. 插件类型必须已存在
        """
        exist_plugin_types = set(PluginType.objects.all().values_list("code", flat=True))
        for resource_data in self.resource_data_list:
            if resource_data.plugin_configs is None:
                continue

            resource_plugin_types = [config.type for config in resource_data.plugin_configs]
            duplicate_types = get_duplicate_items(resource_plugin_types)
            if duplicate_types:
                validate_err = SchemaValidateErr(
                    _("资源绑定的插件类型重复，资源名称：{resource_name}，重复的插件类型：{duplicate_types}").format(
                        resource_name=resource_data.name,
                        duplicate_types=", ".join(duplicate_types),
                    ),
                    f"$.paths.{resource_data.path}.{resource_data.method.lower()}.x-bk-apigateway-resource",
                    absolute_path=[],
                )
                self.schema_validate_result.append(validate_err)
            # 校验插件类型
            types = set(resource_plugin_types)
            not_exist_types = types - exist_plugin_types
            if not_exist_types:
                validate_err = SchemaValidateErr(
                    _("插件类型 {not_exist_types} 不存在。").format(not_exist_types=", ".join(not_exist_types)),
                    f"$.paths.{resource_data.path}.{resource_data.method.lower()}.x-bk-apigateway-resource",
                    absolute_path=[],
                )
                self.schema_validate_result.append(validate_err)

    def _validate_plugin_config(self):
        """
        校验插件配置
        - 1. 插件配置，必须符合插件类型的 schema 约束
        """
        plugin_types = {plugin_type.code: plugin_type for plugin_type in PluginType.objects.all()}
        yaml_validator = PluginConfigYamlValidator()

        for resource_data in self.resource_data_list:
            if resource_data.plugin_configs is None:
                continue

            for plugin_config_data in resource_data.plugin_configs:
                plugin_type = plugin_types[plugin_config_data.type]
                try:
                    yaml_validator.validate(
                        plugin_type.code,
                        plugin_config_data.yaml.encode().decode("unicode_escape"),
                        plugin_type.schema and plugin_type.schema.schema,
                    )
                except Exception as err:
                    validate_err = SchemaValidateErr(
                        _(
                            "资源的插件配置校验失败，资源名称：{resource_name}，插件类型：{plugin_type_code}，错误信息：{err}。"
                        ).format(
                            resource_name=resource_data.name,
                            plugin_type_code=plugin_type.code,
                            err=err,
                        ),
                        f"$.paths.{resource_data.path}.{resource_data.method.lower()}.x-bk-apigateway-resource",
                        absolute_path=[],
                    )
                    self.schema_validate_result.append(validate_err)

    def _validate_backend(self):
        """
        校验resource 绑定的backend
        - backend_name必须存在
        """
        backends = {backend.name: backend for backend in Backend.objects.filter(gateway=self.gateway)}

        for resource_data in self.resource_data_list:
            if resource_data.backend is None:
                continue
            backend = backends.get(resource_data.backend.name)
            if not backend:
                validate_err = SchemaValidateErr(
                    _("资源的后端服务校验失败，资源名称：{resource_name}，后端服务：{backend_name} 不存在").format(
                        resource_name=resource_data.name,
                        plugin_type_code=resource_data.backend.name,
                    ),
                    f"$.paths.{resource_data.path}.{resource_data.method.lower()}.x-bk-apigateway-resource.backend",
                    absolute_path=[],
                )
                self.schema_validate_result.append(validate_err)
