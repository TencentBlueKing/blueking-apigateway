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
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from apigateway.biz.plugin.plugin_synchronizers import PluginConfigData
from apigateway.core.models import Backend, Resource


class ResourceAuthConfig(BaseModel):
    auth_verified_required: bool = Field(default=True)
    app_verified_required: bool = Field(default=True)
    resource_perm_required: bool = Field(default=True)


class ResourceBackendConfig(BaseModel):
    method: str
    path: str
    match_subpath: bool = Field(default=False)
    timeout: int = Field(default=0)
    # 1.13 版本: 兼容旧版 (api_version=0.1) 资源 yaml 通过 openapi 导入
    legacy_upstreams: Optional[dict] = Field(default=None, exclude=True)
    legacy_transform_headers: Optional[dict] = Field(default=None, exclude=True)


class ResourceData(BaseModel):
    resource: Optional[Resource] = Field(default=None)
    # basic
    name: str = Field(...)
    description: Optional[str] = Field(default="")
    description_en: Optional[str] = Field(default=None)
    method: str = Field(...)
    path: str = Field(...)
    match_subpath: bool = Field(default=False)
    is_public: bool = Field(default=True)
    allow_apply_permission: bool = Field(default=True)
    # auth config
    auth_config: ResourceAuthConfig = Field(...)
    # backend
    backend: Optional[Backend] = Field(default=None)
    backend_config: ResourceBackendConfig = Field(...)
    # label
    label_ids: List[int] = Field(default_factory=list)
    # plugin configs
    plugin_configs: Optional[List[PluginConfigData]] = Field(default=None)
    # 扩展数据
    metadata: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        arbitrary_types_allowed = True

    @property
    def basic_data(self) -> Dict[str, Any]:
        return self.dict(include=set(self.basic_field_names()))

    @staticmethod
    def basic_field_names() -> List[str]:
        return [
            "name",
            "description",
            "description_en",
            "method",
            "path",
            "match_subpath",
            "is_public",
            "allow_apply_permission",
        ]

    def snapshot(self) -> Dict[str, Any]:
        assert self.resource
        assert self.backend

        return {
            "id": self.resource.id,
            "name": self.name,
            "description": self.description,
            "method": self.method,
            "path": self.path,
            "match_subpath": self.match_subpath,
            "is_public": self.is_public,
            "allow_apply_permission": self.allow_apply_permission,
            "auth_config": self.auth_config.dict(),
            "backend_id": self.backend.id,
            "backend_config": self.backend_config.dict(),
            "metadata": self.metadata,
        }
