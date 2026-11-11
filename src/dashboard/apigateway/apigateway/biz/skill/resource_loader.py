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
"""从目标环境当前发布的版本读取资源，组装 Skill 校验和渲染用的 SkillResource。

方法、路径、说明、认证直接用发布资源 ReleasedResourceData，参数和响应只取该版本的 OpenAPI schema。
网关或环境未启用、环境未发布、资源不存在或不可用、OpenAPI schema 没有同时定义请求参数和响应参数，
都视为资源不存在。
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from apigateway.biz.released_resource import ReleasedResourceData
from apigateway.core.constants import GatewayStatusEnum, ResourceKindEnum, StageStatusEnum
from apigateway.core.models import Gateway, Release, ReleasedResource, Stage
from apigateway.service.resource_version import get_resource_id_to_schema_by_resource_version, has_openapi_schema

from .refs import norm_path
from .schema_converter import (
    ResourceParam,
    ResponseField,
    convert_schema_params,
    convert_schema_responses,
    has_non_json_request_body,
)


@dataclass
class SkillResource:
    """一个可编排资源：发布数据原样保留，参数和响应由 OpenAPI schema 转换得到。"""

    gateway: str
    stage: str
    data: ReleasedResourceData
    params: List[ResourceParam] = field(default_factory=list)
    responses: List[ResponseField] = field(default_factory=list)
    # 读取资源时发现的非阻断问题（如资源未公开），由校验原样输出
    warnings: List[str] = field(default_factory=list)
    # 资源不能用来生成 Skill 的原因（如请求体不是 JSON）；
    # 由校验作为 error 输出，有值时字段级对照没有依据，跳过
    errors: List[str] = field(default_factory=list)

    @property
    def key(self) -> Tuple[str, str, str]:
        return self.gateway, self.stage, self.data.name

    def get_param(self, name: str) -> Optional[ResourceParam]:
        return next((param for param in self.params if param.name == name), None)

    def has_response_field(self, path: str) -> bool:
        """path 是响应中的字段，或某些字段的对象 / 数组前缀"""
        normed = norm_path(path)
        return any(
            item.field == normed or item.field.startswith(normed + ".") or item.field.startswith(normed + "[")
            for item in self.responses
        )


class ResourceProvider(ABC):
    @abstractmethod
    def get_resource(self, gateway: str, stage: str, resource: str) -> Optional[SkillResource]:
        """资源不存在时返回 None"""
        raise NotImplementedError()


def build_skill_resource(
    gateway: str, stage: str, data: ReleasedResourceData, schema: Dict[str, Any]
) -> Optional[SkillResource]:
    """当前环境禁用该资源，或 schema 没有同时定义请求参数和响应字段时，返回 None。"""
    if stage in data.disabled_stages:
        return None

    resource = SkillResource(gateway=gateway, stage=stage, data=data)
    if not data.is_public:
        resource.warnings.append(f"{gateway}.{data.name}：资源未公开，调用方无法申请权限")

    responses = convert_schema_responses(schema)
    # 显式声明「无请求参数」（none_schema）也算定义了请求参数
    if not (has_openapi_schema(schema) and responses):
        return None

    resource.responses = responses
    if has_non_json_request_body(schema):
        resource.errors.append(f"{gateway}.{data.name}：请求体不是 application/json，SKILL.md 只能描述 JSON 请求体")
    else:
        resource.params = convert_schema_params(schema)
    return resource


@dataclass
class _StageResources:
    resources: Dict[str, ReleasedResourceData]
    schemas: Dict[int, Dict[str, Any]]


class ReleasedResourceProvider(ResourceProvider):
    """同一网关、环境只查一次数据库，结果缓存在实例内，实例的生命周期是一次注入或一次上传"""

    def __init__(self):
        self._stages: Dict[Tuple[str, str], Optional[_StageResources]] = {}

    def get_resource(self, gateway: str, stage: str, resource: str) -> Optional[SkillResource]:
        stage_resources = self._get_stage_resources(gateway, stage)
        if stage_resources is None:
            return None
        data = stage_resources.resources.get(resource)
        if data is None:
            return None
        return build_skill_resource(gateway, stage, data, stage_resources.schemas.get(data.id) or {})

    def _get_stage_resources(self, gateway_name: str, stage_name: str) -> Optional[_StageResources]:
        key = (gateway_name, stage_name)
        if key not in self._stages:
            self._stages[key] = self._load_stage_resources(gateway_name, stage_name)
        return self._stages[key]

    def _load_stage_resources(self, gateway_name: str, stage_name: str) -> Optional[_StageResources]:
        gateway = Gateway.objects.filter(name=gateway_name, status=GatewayStatusEnum.ACTIVE.value).first()
        if not gateway:
            return None
        stage = Stage.objects.filter(gateway=gateway, name=stage_name, status=StageStatusEnum.ACTIVE.value).first()
        if not stage:
            return None
        resource_version_id = Release.objects.get_released_resource_version_id(gateway.id, stage_name)
        if not resource_version_id:
            return None

        released_resources = ReleasedResource.objects.filter(gateway=gateway, resource_version_id=resource_version_id)
        resources = {}
        for item in released_resources:
            data = ReleasedResourceData.from_data(item.data)
            if data.kind != ResourceKindEnum.STANDARD.value:
                continue
            resources[item.resource_name] = data
        return _StageResources(
            resources=resources,
            schemas=get_resource_id_to_schema_by_resource_version(resource_version_id),
        )
