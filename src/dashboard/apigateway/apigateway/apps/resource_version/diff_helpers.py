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

        for key in getattr(self, "__fields__", {}).keys():
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
    def clean_transform_headers(cls, v):
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


class ResourceDiffer(BaseModel, DiffMixin):
    id: int
    name: Text
    description: Text = ""
    method: Text
    path: Text
    match_subpath: bool = False
    is_public: bool = True
    proxy: Union[ResourceHTTPProxy, ResourceMockProxy]
    contexts: ResourceContexts
    disabled_stages: List[Text] = Field(default_factory=list)
    doc_updated_time: Dict[str, str]

    def diff_proxy(self, target: BaseModel) -> Tuple[Optional[dict], Optional[dict]]:
        if not isinstance(self.proxy, type(target.proxy)):
            return self.proxy.dict(), target.proxy.dict()

        return self.proxy.diff(target.proxy)

    def diff_contexts(self, target: BaseModel) -> Tuple[Optional[dict], Optional[dict]]:
        return self.contexts.diff(target.contexts)
