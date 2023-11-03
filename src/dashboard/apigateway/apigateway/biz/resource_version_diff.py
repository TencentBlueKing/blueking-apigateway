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
from typing import Any, Dict, List, Optional, Text, Tuple, Union

from pydantic import BaseModel, Field, Json, validator
from typing_extensions import Literal


class DiffMixin:
    def diff(self, target: BaseModel) -> Tuple[Optional[dict], Optional[dict]]:
        source_diff_data = {}
        target_diff_data = {}

        for key in getattr(self, "__fields__", {}):
            diff_method = getattr(self, f"diff_{key}", None)
            if diff_method is not None:
                source_diff_value, target_diff_value = diff_method(target)
            else:
                source_diff_value, target_diff_value = self._diff_with_field_value(target, key)

            if source_diff_value or target_diff_value:
                source_diff_data[key] = source_diff_value
                target_diff_data[key] = target_diff_value

        return source_diff_data, target_diff_data

    def _diff_with_field_value(self, target: BaseModel, field: str) -> Tuple[Any, Any]:
        source_field_value = getattr(self, field, None)
        target_field_value = getattr(target, field, None)

        if isinstance(source_field_value, BaseModel):
            source_field_value = source_field_value.dict()

        if isinstance(target_field_value, BaseModel):
            target_field_value = target_field_value.dict()

        if source_field_value != target_field_value:
            return source_field_value, target_field_value

        return None, None


class TransformHeaders(BaseModel, DiffMixin):
    set: Optional[Dict[Text, Any]] = None
    delete: Optional[List[Text]] = None


class ResourceProxyHTTPConfig(BaseModel, DiffMixin):
    method: Text
    path: Text
    match_subpath: bool = False
    timeout: int
    upstreams: Dict[Text, Any] = Field(default_factory=dict)
    transform_headers: Dict[Text, Any] = Field(default_factory=dict)

    @validator("transform_headers")
    def clean_transform_headers(cls, v):  # noqa: N805
        return TransformHeaders.parse_obj(v).dict(exclude_unset=True)


class ResourceProxyMockConfig(BaseModel, DiffMixin):
    code: int
    body: Text
    headers: Dict[Text, Text] = Field(default_factory=dict)


class ResourceHTTPProxy(BaseModel, DiffMixin):
    type: Literal["http"]
    config: Json[ResourceProxyHTTPConfig]

    def diff_config(self, target: BaseModel) -> Tuple[Optional[dict], Optional[dict]]:
        return self.config.diff(target.config)


class ResourceMockProxy(BaseModel, DiffMixin):
    type: Literal["mock"]
    config: Json[ResourceProxyMockConfig]

    def diff_config(self, target: BaseModel) -> Tuple[Optional[dict], Optional[dict]]:
        return self.config.diff(target.config)


class ResourceAuthConfig(BaseModel, DiffMixin):
    auth_verified_required: bool
    app_verified_required: bool
    resource_perm_required: bool


class ResourceAuth(BaseModel, DiffMixin):
    config: Json[ResourceAuthConfig]

    def diff_config(self, target: BaseModel) -> Tuple[Optional[dict], Optional[dict]]:
        return self.config.diff(target.config)


class ResourceContexts(BaseModel, DiffMixin):
    resource_auth: ResourceAuth

    def diff_resource_auth(self, target: BaseModel) -> Tuple[Optional[dict], Optional[dict]]:
        return self.resource_auth.diff(target.resource_auth)


class ResourcePluginConfig(BaseModel, DiffMixin):
    id: int
    name: str
    type: str
    config: Dict[Text, Any] = Field(default_factory=dict)


class ResourceDifferHandler(BaseModel, DiffMixin):
    id: int
    name: Text
    description: Text = ""
    method: Text
    path: Text
    match_subpath: bool = False
    is_public: bool = True
    allow_apply_permission: bool = True
    proxy: Union[ResourceHTTPProxy, ResourceMockProxy]
    contexts: ResourceContexts
    disabled_stages: List[Text] = Field(default_factory=list)
    plugins: List[ResourcePluginConfig] = Field(default_factory=list)
    doc_updated_time: Dict[str, str]

    def diff_proxy(self, target: BaseModel) -> Tuple[Optional[dict], Optional[dict]]:
        if not isinstance(self.proxy, type(target.proxy)):
            return self.proxy.dict(), target.proxy.dict()

        return self.proxy.diff(target.proxy)

    def diff_contexts(self, target: BaseModel) -> Tuple[Optional[dict], Optional[dict]]:
        return self.contexts.diff(target.contexts)

    def diff_plugins(self, target: BaseModel) -> Tuple[Optional[dict], Optional[dict]]:
        source_plugins = {plugin.type: plugin.dict() for plugin in self.plugins}
        target_plugins = {plugin.type: plugin.dict() for plugin in target.plugins}
        return source_plugins, target_plugins

    @staticmethod
    def diff_resource_version_data(
        source_data: list,
        target_data: list,
        source_resource_doc_updated_time: dict,
        target_resource_doc_updated_time: dict,
    ) -> dict:
        source_key_to_value_map = {}
        target_data_map = {}
        for item in source_data:
            resource_id = item["id"]
            # 添加文档更新时间
            item["doc_updated_time"] = source_resource_doc_updated_time.get(resource_id, {})
            source_key_to_value_map[resource_id] = item
        for item in target_data:
            resource_id = item["id"]
            # 添加文档更新时间
            item["doc_updated_time"] = target_resource_doc_updated_time.get(resource_id, {})
            target_data_map[resource_id] = item

        resource_add = []
        resource_delete = []
        resource_update = []

        for resource_id, source_resource_data_raw in source_key_to_value_map.items():
            source_resource_differ = ResourceDifferHandler.parse_obj(source_resource_data_raw)
            target_resource_data = target_data_map.pop(resource_id, None)

            # 目标版本中资源不存在，资源被删除
            if not target_resource_data:
                resource_delete.append(source_resource_differ.dict())
                continue

            target_resource_differ = ResourceDifferHandler.parse_obj(target_resource_data)
            source_diff_value, target_diff_value = source_resource_differ.diff(target_resource_differ)

            # 资源无变化，忽略此资源
            if not source_diff_value and not target_diff_value:
                continue

            # 资源有变化，记录资源差异
            source_resource_data = source_resource_differ.dict()
            target_resource_data = target_resource_differ.dict()
            source_resource_data["diff"] = source_diff_value
            target_resource_data["diff"] = target_diff_value
            resource_update.append(
                {
                    "source": source_resource_data,
                    "target": target_resource_data,
                }
            )

        # 目标版本中，新增的资源
        if target_data_map:
            for target_resource_data in target_data_map.values():
                target_resource_differ = ResourceDifferHandler.parse_obj(target_resource_data)
                resource_add.append(target_resource_differ.dict())

        return {
            "add": sorted(resource_add, key=lambda x: x["path"]),
            "delete": sorted(resource_delete, key=lambda x: x["path"]),
            "update": sorted(resource_update, key=lambda x: x["target"]["path"]),
        }
