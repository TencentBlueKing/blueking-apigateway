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

from apigateway.core.models import Backend, Resource


class ResourceAuthConfig(BaseModel):
    auth_verified_required: bool = Field(default=True)
    app_verified_required: bool = Field(default=True)
    resource_perm_required: bool = Field(default=True)


class BackendConfig(BaseModel):
    method: str
    path: str
    match_subpath: bool = Field(default=False)
    timeout: int = Field(default=0)


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
    backend_config: BackendConfig = Field(...)
    # label
    label_ids: List[int] = Field(default_factory=list)
    # 扩展数据
    metadata: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        arbitrary_types_allowed = True

    @property
    def basic_data(self):
        return self.dict(include=self.basic_field_names)

    @staticmethod
    def basic_field_names():
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

    def snapshot(self):
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
            "backend_config": self.backend.dict(),
            "metadata": self.metadata,
        }
