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
"""从目标环境当前发布的版本读取资源定义。

方法、路径、说明、认证取发布数据；参数和响应取 OpenAPI schema，传入快照目录时用补丁快照补。
网关或环境未启用、发布或资源不存在、资源不是 standard，或该环境在资源的 disabled_stages 里，都视为资源不存在。
"""

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Dict, Optional, Tuple

from apigateway.biz.released_resource import ReleasedResourceData
from apigateway.core.constants import GatewayStatusEnum, ResourceKindEnum, StageStatusEnum
from apigateway.core.models import Gateway, Release, ReleasedResource, Stage
from apigateway.service.resource_version import get_resource_id_to_schema_by_resource_version

from .patch_snapshot import PatchSnapshotStore, SnapshotResource
from .resource_definition import ResourceDefinition
from .schema_converter import convert_schema_params, convert_schema_responses, has_non_json_request_body

if TYPE_CHECKING:
    from pathlib import Path


@dataclass
class _StageResources:
    resources: Dict[str, ReleasedResourceData]
    schemas: Dict[int, Dict[str, Any]]


class ReleasedResourceProvider:
    """同一网关、环境只查一次数据库，结果缓存在实例内，实例的生命周期是一次注入或一次上传"""

    def __init__(self, snapshot_dir: Optional[Path] = None):
        self._snapshots = PatchSnapshotStore(snapshot_dir) if snapshot_dir else None
        self._stages: Dict[Tuple[str, str], Optional[_StageResources]] = {}

    def get_resource(self, gateway: str, stage: str, resource: str) -> Optional[ResourceDefinition]:
        stage_resources = self._get_stage_resources(gateway, stage)
        if stage_resources is None:
            return None
        data = stage_resources.resources.get(resource)
        if data is None or stage in data.disabled_stages:
            return None

        definition = ResourceDefinition(
            gateway=gateway,
            stage=stage,
            resource=resource,
            method=data.method,
            path=data.path,
            description=data.description,
            app_verified_required=data.verified_app_required,
            user_verified_required=data.verified_user_required,
            resource_perm_required=data.resource_perm_required,
        )
        if not data.is_public:
            definition.warnings.append(f"{gateway}.{resource}：资源未公开，调用方无法申请权限")

        schema = stage_resources.schemas.get(data.id) or {}
        snapshot = self._snapshots.get(gateway, resource) if self._snapshots else None
        _fill_params_and_responses(definition, schema, snapshot)
        return definition

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


def _fill_params_and_responses(
    definition: ResourceDefinition, schema: Dict[str, Any], snapshot: Optional[SnapshotResource]
) -> None:
    """快照里有的资源，参数和响应整体以快照为准，不做字段级合并"""
    where = f"{definition.gateway}.{definition.resource}"
    # SKILL.md 的请求体只渲染 application/json，快照里的 body 参数同样会按 JSON 渲染，补不了
    if has_non_json_request_body(schema):
        definition.errors.append(f"{where}：请求体不是 application/json，SKILL.md 只能描述 JSON 请求体")
        return

    params = convert_schema_params(schema)
    responses = convert_schema_responses(schema)
    if snapshot:
        definition.params = snapshot.to_params()
        definition.responses = snapshot.to_responses()
        if params or responses:
            definition.warnings.append(
                f"{where}：资源已有 schema，核对后删除 resources/{definition.gateway}.yaml 里的这条快照"
            )
        return

    definition.params = params
    definition.responses = responses
    if not (params or responses):
        definition.errors.append(f"{where}：资源无 schema、无快照，参数和响应字段无法核对")
