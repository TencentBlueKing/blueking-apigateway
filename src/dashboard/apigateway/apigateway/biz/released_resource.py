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
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from apigateway.core.constants import StageStatusEnum
from apigateway.core.models import Gateway, Release, ReleasedResource, Stage
from apigateway.core.utils import get_path_display, get_resource_doc_link


@dataclass
class ReleasedResourceData:
    id: int
    name: str
    method: str
    path: str
    description: str = field(default="")
    description_en: Optional[str] = field(default=None)
    match_subpath: bool = field(default=False)
    is_public: bool = field(default=False)
    allow_apply_permission: bool = field(default=False)
    disabled_stages: List[str] = field(default_factory=list)
    contexts: Dict[str, Any] = field(default_factory=dict)
    verified_app_required: bool = field(init=False)
    verified_user_required: bool = field(init=False)
    resource_perm_required: bool = field(init=False)

    def __post_init__(self):
        resource_auth_config = json.loads(self.contexts["resource_auth"]["config"])
        self.verified_app_required = bool(resource_auth_config.get("app_verified_required", True))
        self.verified_user_required = self._get_verified_user_required(resource_auth_config)
        self.resource_perm_required = self._get_resource_perm_required(resource_auth_config)

    @classmethod
    def from_data(cls, released_resource_data: Dict[str, Any]) -> "ReleasedResourceData":
        return cls(
            id=released_resource_data["id"],
            name=released_resource_data["name"],
            method=released_resource_data["method"],
            path=released_resource_data["path"],
            description=released_resource_data.get("description", ""),
            description_en=released_resource_data.get("description_en"),
            match_subpath=released_resource_data.get("match_subpath", False),
            is_public=released_resource_data["is_public"],
            allow_apply_permission=released_resource_data.get("allow_apply_permission", True),
            disabled_stages=released_resource_data.get("disabled_stages") or [],
            contexts=released_resource_data["contexts"],
        )

    def is_disabled_in_stage(self, stage_name: str) -> bool:
        return stage_name in self.disabled_stages

    @property
    def path_display(self):
        return get_path_display(self.path, self.match_subpath)

    def _get_verified_user_required(self, config: Dict[str, Any]) -> bool:
        return not config.get("skip_auth_verification", False) and bool(config.get("auth_verified_required", False))

    def _get_resource_perm_required(self, config: Dict[str, Any]) -> bool:
        return bool(config.get("resource_perm_required", False))


def get_released_resource_data(gateway: Gateway, stage: Stage, resource_id: int):
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


class ReleasedResourceHandler:
    # TODO 待重构
    @staticmethod
    def clear_unreleased_resource(gateway_id: int) -> None:
        """清理未发布的资源，如已发布版本被新版本替换的情况"""
        resource_version_ids = Release.objects.get_released_resource_version_ids(gateway_id)
        ReleasedResource.objects.filter(gateway_id=gateway_id).exclude(
            resource_version_id__in=resource_version_ids
        ).delete()

    # TODO 待重构
    @staticmethod
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
            "resource_version__schema_version",
            "updated_time",
            "updated_by",
        )
        return {
            release["stage_id"]: {
                "release_status": True,
                "release_time": release["updated_time"],
                "resource_version_id": release["resource_version_id"],
                "resource_version_name": release["resource_version__name"],
                "resource_version_title": release["resource_version__title"],
                "resource_version": {
                    "version": release["resource_version__version"]
                    if release["resource_version__version"] != ""
                    else release["resource_version__title"]
                },
                "resource_version_schema_version": release["resource_version__schema_version"],
                "resource_version_display": release["resource_version__version"],
                "release_by": release["updated_by"],
            }
            for release in stage_release
        }

    @staticmethod
    def get_latest_doc_link(resource_ids: List[int]) -> Dict[int, str]:
        if not resource_ids:
            return {}

        resource_version_ids = ReleasedResource.objects.filter_resource_version_ids(resource_ids)
        released_stage_names = Release.objects.get_resource_version_released_stage_names(resource_version_ids)

        # 按照资源版本从小到大排序，可使最新版本数据覆盖前面版本的数据
        released_resources = ReleasedResource.objects.filter(resource_id__in=resource_ids).order_by(
            "resource_id", "resource_version_id"
        )

        doc_links = {}
        for resource in released_resources:
            stage_names = released_stage_names.get(resource.resource_version_id)
            if not stage_names:
                continue

            disabled_stages = resource.data.get("disabled_stages") or []
            recommended_stage = ReleasedResource.objects.get_recommended_stage_name(stage_names, disabled_stages)
            if not recommended_stage:
                continue

            doc_links[resource.resource_id] = get_resource_doc_link(
                resource.gateway.name,
                recommended_stage,
                resource.resource_name,
            )

        return doc_links

    @staticmethod
    def get_public_released_resource_data_list(gateway_id: int, stage_name: str) -> List[ReleasedResourceData]:
        """获取网关环境下，已发布的，可公开的资源数据"""
        release = (
            Release.objects.filter(gateway_id=gateway_id, stage__name=stage_name)
            .prefetch_related("resource_version")
            .first()
        )
        if not release:
            return []

        resources = [ReleasedResourceData.from_data(resource) for resource in release.resource_version.data]
        return list(filter(lambda resource: resource.is_public, resources))

    @staticmethod
    def get_released_resource(gateway_id: int, stage_name: str, resource_name: str) -> Optional[ReleasedResource]:
        resource_version_id = (
            Release.objects.filter(
                gateway_id=gateway_id,
                stage__name=stage_name,
            )
            .values_list("resource_version_id", flat=True)
            .first()
        )
        if not resource_version_id:
            return None

        resource = ReleasedResource.objects.filter(
            gateway_id=gateway_id,
            resource_version_id=resource_version_id,
            resource_name=resource_name,
        ).first()
        if not resource:
            return None

        return resource
