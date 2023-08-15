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
from typing import Any, Dict, List, Optional

from attrs import define, field

from apigateway.core.models import Gateway, Release, ReleasedResource, Stage
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
