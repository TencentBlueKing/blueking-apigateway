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
from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple

from apigateway.apps.support.constants import DocLanguageEnum
from apigateway.apps.support.models import ReleasedResourceDoc
from apigateway.biz.released_resource import ReleasedResourceData, ReleasedResourceHandler


@dataclass
class ResourceDocData:
    language: str
    content: str
    updated_time: str


class ReleasedResourceDocData(ResourceDocData):
    @classmethod
    def from_data(cls, released_resource_doc: Dict[str, Any]) -> "ReleasedResourceDocData":
        return cls(
            language=released_resource_doc["language"],
            content=released_resource_doc["content"],
            updated_time=released_resource_doc.get("updated_time") or "2020-06-01 12:17:16+0800",
        )


@dataclass
class DummyResourceDocData(ResourceDocData):
    @classmethod
    def create(cls, language: str) -> "DummyResourceDocData":
        return cls(language=language, content="", updated_time="")


class ReleasedResourceDocHandler:
    @staticmethod
    def get_released_resource_doc_data(
        gateway_id: int,
        stage_name: str,
        resource_name: str,
        language: str = DocLanguageEnum.ZH.value,
    ) -> Tuple[Optional[ReleasedResourceData], Optional[ResourceDocData]]:
        released_resource = ReleasedResourceHandler.get_released_resource(
            gateway_id=gateway_id,
            stage_name=stage_name,
            resource_name=resource_name,
        )
        if not released_resource:
            return None, None

        doc = ReleasedResourceDoc.objects.filter(
            gateway_id=gateway_id,
            resource_version_id=released_resource.resource_version_id,
            resource_id=released_resource.resource_id,
            language=language,
        ).first()
        if not doc:
            return ReleasedResourceData.from_data(released_resource.data), DummyResourceDocData.create(language)

        return ReleasedResourceData.from_data(released_resource.data), ReleasedResourceDocData.from_data(doc.data)
