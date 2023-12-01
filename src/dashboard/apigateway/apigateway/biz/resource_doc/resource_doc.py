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
import datetime
from collections import defaultdict
from typing import Dict, List, Optional

from apigateway.apps.support.constants import DocLanguageEnum
from apigateway.apps.support.models import ResourceDoc
from apigateway.common.constants import LanguageCodeEnum

from .constants import EN_RESOURCE_DOC_TMPL, ZH_RESOURCE_DOC_TMPL


class ResourceDocHandler:
    @staticmethod
    def get_docs(resource_ids: List[int]) -> Dict[int, List]:
        if not resource_ids:
            return {}

        queryset = ResourceDoc.objects.filter(resource_id__in=resource_ids).values("id", "resource_id", "language")

        docs = defaultdict(list)
        for doc in queryset:
            docs[doc["resource_id"]].append(
                {
                    "id": doc["id"],
                    "language": doc["language"],
                }
            )

        return docs

    @staticmethod
    def get_docs_by_language(resource_ids: List[int], language: str) -> Dict[int, Dict]:
        if not (resource_ids and language):
            return {}

        queryset = ResourceDoc.objects.filter(resource_id__in=resource_ids, language=language).values(
            "id", "resource_id", "language"
        )
        return {doc["resource_id"]: {"id": doc["id"], "language": doc["language"]} for doc in queryset}

    @staticmethod
    def get_resource_doc_tmpl(gateway_name: str, language: str) -> str:
        """获取资源文档模板"""
        # 将模板中的网关名替换为当前网关名（作为包名，将中折线替换为下划线）
        if language == DocLanguageEnum.ZH.value:
            template = ZH_RESOURCE_DOC_TMPL

        elif language == DocLanguageEnum.EN.value:
            template = EN_RESOURCE_DOC_TMPL

        else:
            template = ""

        return template.replace("__GATEWAY_NAME__", gateway_name.replace("-", "_"))

    @staticmethod
    def get_doc_language(language_code: str) -> str:
        doc_languages = {
            LanguageCodeEnum.ZH_HANS.value: DocLanguageEnum.ZH.value,
            LanguageCodeEnum.EN.value: DocLanguageEnum.EN.value,
        }
        return doc_languages.get(language_code, DocLanguageEnum.ZH.value)

    @staticmethod
    def get_last_updated_time(gateway_id: int) -> Optional[datetime.datetime]:
        """获取网关下资源文档的最近更新时间"""
        return (
            ResourceDoc.objects.filter(gateway_id=gateway_id)
            .order_by("-updated_time")
            .values_list("updated_time", flat=True)
            .first()
        )
