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
import json
from collections import defaultdict
from typing import Any, Dict, List, Optional

from attrs import define, field

from apigateway.biz.resource_version import ResourceVersionHandler
from apigateway.core.constants import StageStatusEnum
from apigateway.core.models import Gateway, Release, ReleasedResource, ResourceVersion, Stage
from apigateway.core.utils import get_path_display


@define
class ReleasedResourceData:
    id: int
    method: str
    path: str
    match_subpath: bool = field(default=False)
    disabled_stages: List[str] = field(factory=list)
    _contexts: Dict[str, Any] = field(factory=dict)
    verified_user_required: bool = field(init=False)
    resource_perm_required: bool = field(init=False)

    def __attrs_post_init__(self):
        resource_auth_config = json.loads(self._contexts["resource_auth"]["config"])
        self.verified_user_required = self._get_verified_user_required(resource_auth_config)
        self.resource_perm_required = self._get_resource_perm_required(resource_auth_config)

    @classmethod
    def from_data(cls, released_resource_data: Dict[str, Any]):
        return cls(
            id=released_resource_data["id"],
            method=released_resource_data["method"],
            path=released_resource_data["path"],
            match_subpath=released_resource_data.get("match_subpath", False),
            disabled_stages=released_resource_data.get("disabled_stages", []),
            contexts=released_resource_data["contexts"],
        )

    def is_disabled_in_stage(self, stage_name: str) -> bool:
        return stage_name in self.disabled_stages

    @property
    def path_display(self):
        return get_path_display(self.path, self.match_subpath)

    def _get_verified_user_required(self, config: Dict[str, Any]) -> bool:
        return not config.get("skip_auth_verification") and bool(config.get("auth_verified_required"))

    def _get_resource_perm_required(self, config: Dict[str, Any]) -> bool:
        return bool(config.get("resource_perm_required"))


def get_released_resource_data(gateway: Gateway, stage: Stage, resource_id: int) -> Optional[ReleasedResourceData]:
    resource_version_id = (
        Release.objects.filter(gateway=gateway, stage=stage).values_list("resource_version_id", flat=True).first()
    )
    if not resource_version_id:
        return None

    released_resource = ReleasedResource.objects.filter(
        gateway=gateway,
        resource_version_id=resource_version_id,
        resource_id=resource_id,
    ).first()
    if not released_resource:
        return None

    return ReleasedResourceData.from_data(released_resource.data)


def clear_unreleased_resource(gateway_id: int) -> None:
    """清理未发布的资源，如已发布版本被新版本替换的情况"""
    resource_version_ids = Release.objects.get_released_resource_version_ids(gateway_id)
    ReleasedResource.objects.filter(gateway_id=gateway_id).exclude(
        resource_version_id__in=resource_version_ids
    ).delete()


def get_resource_released_stage_count(gateway_id: int, resource_ids: List[int]) -> Dict[int, int]:
    """获取资源已发布环境的数量"""
    resource_version_ids = Release.objects.get_released_resource_version_ids(gateway_id)
    released_stage_count = Release.objects.get_released_stage_count(resource_version_ids)

    resource_released_stage_count: dict = defaultdict(int)

    queryset = ReleasedResource.objects.filter(gateway_id=gateway_id, resource_id__in=resource_ids).values(
        "resource_id", "resource_version_id"
    )
    for resource in queryset:
        resource_id = resource["resource_id"]
        resource_version_id = resource["resource_version_id"]
        resource_released_stage_count[resource_id] += released_stage_count.get(resource_version_id, 0)

    return resource_released_stage_count


def get_resource_released_stages(gateway_id: int, resource_id: int) -> Dict[int, dict]:
    """获取资源已发布的环境信息"""

    rv_id_to_released_resource_map = ReleasedResource.objects.get_resource_version_id_to_obj_map(
        gateway_id, resource_id
    )
    released_stage_id_map = Release.objects.get_stage_id_to_fields_map(
        gateway_id, rv_id_to_released_resource_map.keys()
    )
    resource_version_id_map = ResourceVersion.objects.get_id_to_fields_map(
        gateway_id,
        rv_id_to_released_resource_map.keys(),
    )

    resource_released_stages = {}
    for stage_id, stage_release in released_stage_id_map.items():
        resource_version_id = stage_release["resource_version_id"]
        resource_version = resource_version_id_map[resource_version_id]
        released_resource = rv_id_to_released_resource_map[resource_version_id]
        resource_released_stages[stage_id] = {
            "stage_id": stage_id,
            "resource_version_id": resource_version["id"],
            "resource_version_name": resource_version["name"],
            "resource_version_title": resource_version["title"],
            "resource_version_display": ResourceVersionHandler().get_resource_version_display(resource_version),
            "released_resource": released_resource,
        }

    return resource_released_stages


def get_stage_release(gateway, stage_ids=None):
    """
    获取环境部署信息
    """
    queryset = Release.objects.filter(gateway_id=gateway.id, stage__status=StageStatusEnum.ACTIVE.value)
    if stage_ids is not None:
        queryset = queryset.filter(stage_id__in=stage_ids)

    stage_release = queryset.values(
        "stage_id",
        "resource_version_id",
        "resource_version__name",
        "resource_version__title",
        "resource_version__version",
        "updated_time",
    )
    return {
        release["stage_id"]: {
            "release_status": True,
            "release_time": release["updated_time"],
            "resource_version_id": release["resource_version_id"],
            "resource_version_name": release["resource_version__name"],
            "resource_version_title": release["resource_version__title"],
            "resource_version": {
                "version": release["resource_version__version"],
            },
            "resource_version_display": ResourceVersionHandler().get_resource_version_display(
                {
                    "version": release["resource_version__version"],
                    "name": release["resource_version__name"],
                    "title": release["resource_version__title"],
                }
            ),
        }
        for release in stage_release
    }
