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
from typing import Optional

from django.conf import settings

from apigateway.biz.released_resource import ReleasedResourceData
from apigateway.biz.resource_url import ResourceURLHandler
from apigateway.core.models import Gateway
from apigateway.core.utils import get_path_display, get_resource_url
from apigateway.utils.jinja2 import render_to_string

from .constants import BKAPI_AUTHORIZATION_DESCRIPTIONS, RESOURCE_URL_PARTS, APIDocTypeEnum
from .released_resource_doc import ReleasedResourceDocData


class DocGenerator:
    def __init__(
        self,
        gateway: Gateway,
        stage_name: str,
        resource_data: ReleasedResourceData,
        doc_data: ReleasedResourceDocData,
        language: str,
    ):
        self.gateway = gateway
        self.stage_name = stage_name
        self.resource_data = resource_data
        self.doc_data = doc_data
        self.language = language

    def get_doc(self) -> dict:
        return {
            "type": APIDocTypeEnum.MARKDOWN.value,
            "content": self._get_doc_content(),
            "updated_time": self.doc_data.updated_time,
        }

    def _get_doc_content(self) -> str:
        parts = [
            self._get_resource_url_part(),
            self._get_common_request_params_part(),
            self._replace_bkapi_authorization_description(self.doc_data.content),
        ]
        return "\n\n".join(filter(None, parts))

    def _get_resource_url_part(self) -> str:
        part = RESOURCE_URL_PARTS.get(self.language, "")
        part = part.format(
            stage_name=self.stage_name,
            method=self.resource_data.method,
            resource_url=self._get_resource_url(),
        )

        return textwrap.dedent(part).strip()

    def _get_common_request_params_part(self) -> str:
        """公共请求参数"""
        description = render_to_string(
            BKAPI_AUTHORIZATION_DESCRIPTIONS.get(self.language, ""),
            verified_app_required=self.resource_data.verified_app_required,
            verified_user_required=self.resource_data.verified_user_required,
            docs_urls=getattr(settings, "DOCS_URLS", {}),
            settings=settings,
        )
        return description.strip()

    def _replace_bkapi_authorization_description(self, content: Optional[str]) -> Optional[str]:
        if not content:
            return None

        return re.sub(r"{{ *bkapi_authorization_description *}}", "", content)

    def _get_resource_url(self):
        return get_resource_url(
            resource_url_tmpl=ResourceURLHandler.get_resource_url_tmpl(self.gateway.name, self.stage_name),
            gateway_name=self.gateway.name,
            stage_name=self.stage_name,
            resource_path=get_path_display(self.resource_data.path, self.resource_data.match_subpath),
        )
