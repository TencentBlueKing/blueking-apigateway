# -*- coding: utf-8 -*-
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
import re
import textwrap
from dataclasses import dataclass
from typing import List, Optional

from tencent_apigateway_common.django.translation import get_current_language_code

from apigateway.utils.jinja2 import render_to_string

from .constants import BKAPI_AUTHORIZATION_DESCRIPTIONS, RESOURCE_URL_PARTS, APIDocTypeEnum


@dataclass
class ResourceDocHelper:
    stage_name: str
    resource: dict
    doc: dict
    resource_url: str
    api_maintainers: List[str]

    def get_doc(self) -> dict:
        # 资源不存在
        if not self.resource:
            return {}

        return {
            "type": APIDocTypeEnum.MARKDOWN.value,
            "content": self._get_doc_content(),
            "updated_time": self.doc.get("updated_time", ""),
        }

    def _get_doc_content(self) -> str:
        parts = [
            self._get_resource_url_part(),
            self._get_common_request_params_part(),
            self._replace_bkapi_authorization_description(self.doc.get("content")),
        ]
        return "\n\n".join(filter(None, parts))

    def _get_resource_url_part(self) -> str:
        if not self.resource:
            return ""

        part = RESOURCE_URL_PARTS.get(get_current_language_code(), "")
        part = part.format(
            stage_name=self.stage_name,
            method=self.resource["method"],
            resource_url=self.resource_url,
        )

        return textwrap.dedent(part).strip()

    def _get_common_request_params_part(self) -> str:
        """公共请求参数"""
        description = render_to_string(
            BKAPI_AUTHORIZATION_DESCRIPTIONS.get(get_current_language_code(), ""),
            app_verified_required=self.resource.get("app_verified_required", False),
            user_verified_required=self.resource.get("user_verified_required", False),
        )
        return description.strip()

    def _replace_bkapi_authorization_description(self, content: Optional[str]) -> Optional[str]:
        if not content:
            return None

        return re.sub(r"{{ *bkapi_authorization_description *}}", "", content)
