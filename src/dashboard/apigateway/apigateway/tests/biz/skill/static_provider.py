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
"""内存中的资源定义，测试用"""

from typing import Any, Dict, Iterable, Optional

from apigateway.biz.skill.resource_definition import ResourceDefinition, ResourceParam, ResponseField


class StaticResourceProvider:
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
        params=[
            ResourceParam(
                name=item["name"],
                location=item["in"],
                type=item.get("type") or "",
                required=bool(item.get("required", False)),
                description=item.get("description") or "",
            )
            for item in data.get("params", [])
        ],
        responses=[
            ResponseField(field=item["field"], type=item.get("type") or "", description=item.get("description") or "")
            for item in data.get("response", [])
        ],
    )
