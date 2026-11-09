#
# TencentBlueKing is pleased to support the open source community by making
# 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
# Copyright (C) Tencent. All rights reserved.
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
"""渲染和校验用到的资源定义，以及按 (gateway, stage, resource) 查询资源定义的接口。

类型写法：`string`、`integer`、`array<string>`；多种类型用 `|` 连接，如 `array|integer|string`。
响应字段用相对响应体的字段路径表示，数组层级写成 `[]`，如 `data.items[].id`。
"""

from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Optional, Protocol, Tuple

from .refs import norm_path


@dataclass
class ResourceParam:
    name: str
    location: str  # path / query / header / body
    type: str = ""
    required: bool = False
    description: str = ""

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ResourceParam":
        return cls(
            name=data["name"],
            location=data["in"],
            type=data.get("type") or "",
            required=bool(data.get("required", False)),
            description=data.get("description") or "",
        )


@dataclass
class ResponseField:
    field: str
    type: str = ""
    description: str = ""

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ResponseField":
        return cls(field=data["field"], type=data.get("type") or "", description=data.get("description") or "")


@dataclass
class ResourceDefinition:
    gateway: str
    stage: str
    resource: str
    method: str
    path: str
    description: str = ""
    app_verified_required: bool = False
    user_verified_required: bool = False
    resource_perm_required: bool = False
    params: List[ResourceParam] = field(default_factory=list)
    responses: List[ResponseField] = field(default_factory=list)
    # 读取资源定义时发现的问题（如无 schema、快照可删除），由校验原样输出
    warnings: List[str] = field(default_factory=list)

    @property
    def key(self) -> Tuple[str, str, str]:
        return self.gateway, self.stage, self.resource

    def get_param(self, name: str) -> Optional[ResourceParam]:
        return next((param for param in self.params if param.name == name), None)

    def get_param_location(self, name: str) -> str:
        """参数定义里没有时（校验已报 warning）按方法推断位置"""
        param = self.get_param(name)
        if param:
            return param.location
        return "query" if self.method in ("GET", "DELETE") else "body"

    def has_response_field(self, path: str) -> bool:
        """path 是响应中的字段，或某些字段的对象 / 数组前缀"""
        normed = norm_path(path)
        return any(
            item.field == normed or item.field.startswith(normed + ".") or item.field.startswith(normed + "[")
            for item in self.responses
        )

    def get_response_field(self, path: str) -> Optional[ResponseField]:
        normed = norm_path(path)
        return next((item for item in self.responses if item.field == normed), None)

    def has_response_array(self, path: str) -> bool:
        normed = norm_path(path)
        return any(item.field.startswith(normed + "[") for item in self.responses)


class ResourceProvider(Protocol):
    def get_resource(self, gateway: str, stage: str, resource: str) -> Optional[ResourceDefinition]:
        """资源不存在时返回 None"""


class StaticResourceProvider:
    """内存中的资源定义，用于测试和离线渲染"""

    def __init__(self, resources: Iterable[ResourceDefinition]):
        self._resources = {resource.key: resource for resource in resources}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "StaticResourceProvider":
        """`{"resources": [...]}`，每项含 gateway、stage、resource、method、path、description、auth、params、response"""
        return cls(_definition_from_dict(item) for item in data["resources"])

    def get_resource(self, gateway: str, stage: str, resource: str) -> Optional[ResourceDefinition]:
        return self._resources.get((gateway, stage, resource))


def _definition_from_dict(data: Dict[str, Any]) -> ResourceDefinition:
    auth = data.get("auth") or {}
    return ResourceDefinition(
        gateway=data["gateway"],
        stage=data["stage"],
        resource=data["resource"],
        method=data["method"],
        path=data["path"],
        description=data.get("description") or "",
        app_verified_required=bool(auth.get("app_verified_required", False)),
        user_verified_required=bool(auth.get("user_verified_required", False)),
        resource_perm_required=bool(auth.get("resource_perm_required", False)),
        params=[ResourceParam.from_dict(item) for item in data.get("params", [])],
        responses=[ResponseField.from_dict(item) for item in data.get("response", [])],
    )
