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
"""资源定义补丁快照：data/skill/resources/{gateway}.yaml，只给内置 Skill 用。

网关没有导入 OpenAPI schema 时，用快照补参数和响应；快照里有的资源，参数和响应整体以快照为准，
方法、路径、说明、认证仍取发布数据。
"""

import datetime
from pathlib import Path
from typing import Dict, List, Optional, Union

import yaml
from pydantic import BaseModel, ConfigDict, Field, StrictBool, StrictStr, ValidationError, field_validator

from .resource_definition import ResourceParam, ResponseField


class SkillSnapshotError(Exception):
    pass


class _SnapshotModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class SnapshotParam(_SnapshotModel):
    name: StrictStr
    location: StrictStr = Field(alias="in")
    type: StrictStr = ""
    required: StrictBool = False
    description: StrictStr = ""


class SnapshotResponseField(_SnapshotModel):
    field: StrictStr
    type: StrictStr = ""
    description: StrictStr = ""


class SnapshotResource(_SnapshotModel):
    resource: StrictStr
    reason: StrictStr
    source_date: Union[datetime.date, StrictStr]
    source: StrictStr
    params: List[SnapshotParam] = Field(default_factory=list)
    responses: List[SnapshotResponseField] = Field(default_factory=list)

    @field_validator("reason", "source")
    @classmethod
    def _check_not_empty(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("不能为空")
        return value

    def to_params(self) -> List[ResourceParam]:
        return [
            ResourceParam(
                name=item.name,
                location=item.location,
                type=item.type,
                required=item.required,
                description=item.description,
            )
            for item in self.params
        ]

    def to_responses(self) -> List[ResponseField]:
        return [
            ResponseField(field=item.field, type=item.type, description=item.description) for item in self.responses
        ]


class SnapshotFile(_SnapshotModel):
    gateway: StrictStr
    resources: List[SnapshotResource]


class PatchSnapshotStore:
    """按网关懒加载快照文件；文件格式不对时抛 SkillSnapshotError"""

    def __init__(self, directory: Path):
        self.directory = Path(directory)
        self._files: Dict[str, Dict[str, SnapshotResource]] = {}

    def get(self, gateway: str, resource: str) -> Optional[SnapshotResource]:
        if gateway not in self._files:
            self._files[gateway] = self._load(gateway)
        return self._files[gateway].get(resource)

    def _load(self, gateway: str) -> Dict[str, SnapshotResource]:
        path = self.directory / f"{gateway}.yaml"
        if not path.is_file():
            return {}
        try:
            snapshot = SnapshotFile.model_validate(yaml.safe_load(path.read_text(encoding="utf-8")))
        except (yaml.YAMLError, ValidationError) as err:
            raise SkillSnapshotError(f"快照 {path.name} 格式不正确：{err}") from None
        if snapshot.gateway != gateway:
            raise SkillSnapshotError(f"快照 {path.name} 的 gateway 应为 {gateway}：{snapshot.gateway}")
        return {item.resource: item for item in snapshot.resources}
