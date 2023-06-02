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
import logging
from collections import defaultdict
from typing import Any, Dict, List, Optional

from django.utils.translation import gettext as _

from apigateway.apps.label.models import APILabel
from apigateway.apps.resource import serializers
from apigateway.apps.resource.mixins import CreateResourceMixin, UpdateResourceMixin
from apigateway.apps.resource.swagger.swagger import ResourceSwaggerImporter
from apigateway.apps.support.models import ResourceDoc
from apigateway.biz.resource import ResourceHandler
from apigateway.common.error_codes import error_codes
from apigateway.common.exceptions import SchemaValidationError
from apigateway.core.models import Gateway, Resource, Stage

logger = logging.getLogger(__name__)


class ResourceImportValidator:
    """
    - 1. 识别导入的资源，补全资源 ID
    - 2. 校验资源是否合法
    """

    def __init__(
        self,
        gateway: Gateway,
        importing_resources: List[Dict[str, Any]],
        resource_doc_language: str = "",
        need_delete_unspecified_resources: bool = False,
    ):
        self.gateway = gateway
        self._importing_resources = importing_resources
        self._resource_doc_language = resource_doc_language
        self._need_delete_unspecified_resources = need_delete_unspecified_resources
        self._existed_resource_id_to_fields = Resource.objects.filter_id_to_fields(
            gateway_id=self.gateway.pk,
            fields=["id", "name", "method", "path"],
        )

    def validate(self) -> List[Dict[str, Any]]:
        self._enrich_resource_id()

        if self._need_delete_unspecified_resources:
            self._remove_unspecified_resources(self._existed_resource_id_to_fields)

        self._validate_resource_id()
        self._validate_method_path()
        self._validate_resource_name()
        self._validate_resource_count()

        return self._check_importing_resources()

    def _enrich_resource_id(self):
        """补全资源 ID"""
        resource_path_method_to_id = self._get_resource_path_method_to_id()
        for resource in self._importing_resources:
            if resource.get("id"):
                continue
            resource["id"] = resource_path_method_to_id.get(resource["path"], {}).get(resource["method"])

    def _remove_unspecified_resources(self, existed_resource_id_to_fields):
        # 如果要删除未指定资源，清理配置 existed_resource_id_to_fields，以防止校验时数据冲突
        specified_resource_ids = [
            resource["id"] for resource in self._importing_resources if resource["id"] is not None
        ]
        unspecified_resource_ids = set(existed_resource_id_to_fields.keys()) - set(specified_resource_ids)
        for resource_id in unspecified_resource_ids:
            existed_resource_id_to_fields.pop(resource_id)

    def _validate_resource_id(self):
        """
        - 检查资源ID是否存在
        - 检查资源ID是否重复
        """
        resource_id_set = set()
        for resource in self._importing_resources:
            resource_id = resource.get("id")
            if not resource_id:
                continue

            # 资源ID不存在
            if resource_id not in self._existed_resource_id_to_fields:
                raise error_codes.VALIDATE_ERROR.format(
                    message=_("资源ID【id={resource_id}】不存在。").format(resource_id=resource_id)
                )

            # 资源ID有重复
            if resource_id in resource_id_set:
                raise error_codes.VALIDATE_ERROR.format(
                    message=_("资源ID【id={resource_id}】重复，资源信息【method={method}, path={path}】。").format(
                        resource_id=resource_id,
                        method=resource["method"],
                        path=resource["path"],
                    )
                )

            resource_id_set.add(resource_id)

    def _validate_method_path(self):
        """
        - 校验 method+path 不能重复
        """
        key_to_id: Dict[str, Optional[int]] = {
            f"{resource['method']}:{resource['path']}": resource_id
            for resource_id, resource in self._existed_resource_id_to_fields.items()
        }
        for resource in self._importing_resources:
            resource_id = resource.get("id")
            if resource_id:
                existed_resource_fields = self._existed_resource_id_to_fields[resource_id]
                existed_key = f"{existed_resource_fields['method']}:{existed_resource_fields['path']}"
                key_to_id.pop(existed_key)

            key = f"{resource['method']}:{resource['path']}"
            if key in key_to_id:
                raise error_codes.VALIDATE_ERROR.format(
                    message=_("资源【method={method}, path={path}】重复。").format(
                        method=resource["method"], path=resource["path"]
                    )
                )

            key_to_id[key] = resource_id

    def _validate_resource_name(self):
        """校验资源名称是否合法，不符合标准的几种情况：

        - 资源名称已存在，并且指定的 ID 不等于已存在的值
        - 资源名称已存在，但路径或方法名变了（无法自动匹配到资源 ID，ID 值为空）
        - 同一个资源名称被重复使用

        :raise APIError: When validation fails.
        """
        existed_name_res_map = {obj["name"]: obj for obj in self._existed_resource_id_to_fields.values()}
        seen_names = set()
        for resource in self._importing_resources:
            name = resource["name"]
            # Check if there are any existing resources using the same name.
            existed_res = existed_name_res_map.get(name)
            if existed_res and existed_res["id"] != resource.get("id"):
                raise error_codes.VALIDATE_ERROR.format(
                    _(
                        "资源（{input_method} {input_path}）的名称【name={name}】重复，该名字已被现有资源"
                        "（{method} {path}）占用，需调整资源名或维持相同的请求方法和路径。"
                    ).format(  # noqa: E501
                        input_method=resource.get("method", ""),
                        input_path=resource.get("path", ""),
                        name=name,
                        method=existed_res["method"],
                        path=existed_res["path"],
                    ),
                )

            # Check if the name is duplicated
            if name in seen_names:
                raise error_codes.VALIDATE_ERROR.format(
                    _("资源名称【name={name}】重复，该名字在当前配置数据中被多次使用。").format(name=name),
                )
            else:
                seen_names.add(name)

    def _validate_resource_count(self):
        new_resources = [resource for resource in self._importing_resources if not resource.get("id")]
        count = len(self._existed_resource_id_to_fields) + len(new_resources)
        if count > self.gateway.max_resource_count:
            raise error_codes.VALIDATE_ERROR.format(
                message=_("每个网关最多创建 {count} 个资源。").format(count=self.gateway.max_resource_count)
            )

    def _check_importing_resources(self) -> List[Dict[str, Any]]:
        slz = serializers.CheckImportResourceSLZ(
            data=self._importing_resources,  # type: ignore
            many=True,
            context={
                "api": self.gateway,
                "stage_name_set": set(Stage.objects.get_names(self.gateway.pk)),
                "resource_path_method_to_id": self._get_resource_path_method_to_id(),
                "resource_doc_language": self._resource_doc_language,
                "resource_doc_key_to_id": ResourceDoc.objects.get_doc_key_to_id(self.gateway.pk),
            },
        )
        slz.is_valid(raise_exception=True)
        return slz.validated_data  # type: ignore

    def _get_resource_path_method_to_id(self) -> Dict[str, Dict[str, int]]:
        resource_path_method_to_id: Dict[str, Dict[str, int]] = defaultdict(dict)
        for resource_id, resource in self._existed_resource_id_to_fields.items():
            resource_path_method_to_id[resource["path"]][resource["method"]] = resource_id
        return resource_path_method_to_id


class ResourcesImporter(CreateResourceMixin, UpdateResourceMixin):
    """导入资源

    - 支持解析输入的 yaml/json 资源配置
    - 支持校验资源配置
    """

    def __init__(
        self,
        gateway: Gateway,
        allow_overwrite: bool,
        need_delete_unspecified_resources: bool = False,
        username: str = "",
    ):
        self.gateway = gateway
        self.allow_overwrite = allow_overwrite
        self.need_delete_unspecified_resources = need_delete_unspecified_resources
        self.username = username

        self._resource_doc_language = ""
        self.imported_resources: List[Dict[str, Any]] = []
        # selected_resources 为 None 表示不过滤资源
        self._selected_resources: Optional[List[Dict[str, Any]]] = None
        self._deleted_resources: List[Dict[str, Any]] = []

    def import_resources(self) -> List[Dict[str, Any]]:
        # 0. 如果删除未指定，则先删除
        if self.need_delete_unspecified_resources:
            self._deleted_resources = self._delete_unspecified_resources()

        # 1. 过滤待导入的资源
        self._filter_imported_resources()

        # 2. 分析并创建网关标签
        self._create_not_exist_labels()

        # 3. 补充导入资源配置中的 label_ids、disabled_stage_ids 等信息
        self._enrich_imported_resources()

        # 4. 创建或更新资源
        self._create_or_update_resources()

        return self.imported_resources

    def load_importing_resources_by_swagger(self, content: str, resource_doc_language: str = ""):
        try:
            importer = ResourceSwaggerImporter(content)
        except Exception as err:
            raise error_codes.VALIDATE_ERROR.format(_("导入内容为无效的 json/yaml 数据，{err}。").format(err=err))

        try:
            importer.validate()
        except SchemaValidationError as err:
            raise error_codes.VALIDATE_ERROR.format(_("导入内容不符合 swagger 2.0 协议，{err}。").format(err=err))

        self._resource_doc_language = resource_doc_language
        self.set_importing_resources(importer.get_resources())

    def set_importing_resources(self, importing_resources: List[Dict[str, Any]]):
        validator = ResourceImportValidator(
            gateway=self.gateway,
            importing_resources=importing_resources,
            resource_doc_language=self._resource_doc_language,
            need_delete_unspecified_resources=self.need_delete_unspecified_resources,
        )
        self.imported_resources = validator.validate()

    def set_selected_resources(self, selected_resources: Optional[List[Dict[str, Any]]]):
        self._selected_resources = selected_resources

    def get_deleted_resources(self):
        return self._deleted_resources

    def _delete_unspecified_resources(self) -> List[Dict[str, Any]]:
        """删除未指定的资源，即当前网关未在 imported_resources 中存在的资源"""
        unspecified_resources = self.get_unspecified_resources()
        if not unspecified_resources:
            return []

        unspecified_resource_ids = [resource["id"] for resource in unspecified_resources]
        ResourceHandler().delete_resources(unspecified_resource_ids, self.gateway)
        return unspecified_resources

    def get_unspecified_resources(self) -> List[Dict[str, Any]]:
        """获取网关中，当前 imported_resources 未指定的资源"""
        specified_resource_ids = [resource["id"] for resource in self.imported_resources if resource["id"] is not None]
        return Resource.objects.get_unspecified_resource_fields(self.gateway.id, specified_resource_ids)

    def _filter_imported_resources(self):
        """过滤导入的资源

        - 如果未设置选中的资源，则导入全部资源
        - 如果设置选中的资源，则仅导入选中的资源
        """
        if self._selected_resources is None:
            return

        selected_resource_names = {item["name"] for item in self._selected_resources}
        self.imported_resources = [
            resource for resource in self.imported_resources if resource["name"] in selected_resource_names
        ]

    def _create_not_exist_labels(self):
        """创建不存在的标签"""
        labels = set()
        for resource in self.imported_resources:
            labels.update(resource["labels"])

        APILabel.objects.save_labels(self.gateway, labels, self.username)

    def _enrich_imported_resources(self):
        """
        补充资源中 label_ids、disabled_stage_ids 等信息
        """
        label_name_to_id = APILabel.objects.get_name_id_map(self.gateway)
        stage_name_to_id = Stage.objects.get_name_id_map(self.gateway)

        for resource in self.imported_resources:
            resource["label_ids"] = [label_name_to_id[name] for name in resource["labels"]]
            resource["disabled_stage_ids"] = [stage_name_to_id[name] for name in resource["disabled_stages"]]

    def _create_or_update_resources(self):
        for resource in self.imported_resources:
            if resource["id"] is None:
                instance = self._create_resource(
                    gateway=self.gateway,
                    data=resource,
                    username=self.username,
                )
                resource["id"] = instance.id
                resource["_is_created"] = True

            elif self.allow_overwrite:
                instance = Resource.objects.get(id=resource["id"])
                self._update_resource(
                    gateway=self.gateway,
                    instance=instance,
                    data=resource,
                    username=self.username,
                )
                resource["_is_updated"] = True
