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
import hashlib
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Sequence, Set, TypeVar

from apigateway.apps.support.constants import DocSourceEnum, DocTypeEnum
from apigateway.apps.support.models import ResourceDoc, ResourceDocSwagger
from apigateway.apps.support.resource_doc.import_doc.docs import BaseDoc
from apigateway.core.models import Resource

DocType = TypeVar("DocType", bound=BaseDoc)


@dataclass
class DocsHandler:
    gateway_id: int
    allow_overwrite: bool = False
    selected_language: str = ""
    selected_resource_docs: Optional[List[Dict[str, Any]]] = None

    def __post_init__(self):
        self.selected_resource_doc_keys: Optional[Set[str]] = None
        if self.selected_resource_docs is not None:
            self.selected_resource_doc_keys = {
                f"{doc['resource_id']}:{doc['language']}" for doc in self.selected_resource_docs
            }

    def handle(self, docs: Sequence[DocType]) -> Sequence[DocType]:
        docs = self.enrich_docs(self.gateway_id, docs)
        docs = self.filter_valid_docs(docs)
        docs = self.filter_selected_docs(
            docs,
            self.allow_overwrite,
            self.selected_language,
            self.selected_resource_doc_keys,
        )
        return self.save_docs(self.gateway_id, docs)

    def enrich_docs(self, gateway_id: int, docs: Sequence[DocType]) -> Sequence[DocType]:
        """增强 docs 配置

        - 设置资源 ID
        - 设置资源文档 ID
        - 设置关联的 swagger 文档 ID

        note: en/zh share the same resource_id, use the doc_key to distinguish
        """
        resource_name_to_id = Resource.objects.filter_resource_name_to_id(gateway_id)
        doc_key_to_id = ResourceDoc.objects.get_doc_key_to_id(gateway_id)
        doc_id_to_swagger_id = ResourceDocSwagger.objects.get_resource_doc_id_to_id(gateway_id)

        doc_key_to_content_md5 = ResourceDoc.objects.query_doc_key_to_content_md5(gateway_id)

        for doc in docs:
            doc.resource_id = resource_name_to_id.get(doc.resource_name)
            doc.resource_doc_id = doc_key_to_id.get(doc.doc_key)  # type: ignore
            doc.resource_doc_swagger_id = doc_id_to_swagger_id.get(doc.resource_doc_id)  # type: ignore

            doc.has_changed = True
            if doc.doc_key is not None:
                old_md5 = doc_key_to_content_md5.get(doc.doc_key)
                current_md5 = self._generate_md5(doc.resource_doc_markdown)
                doc.has_changed = old_md5 != current_md5

        return docs

    def _generate_md5(self, content: str) -> str:
        return hashlib.md5(content.encode("utf-8")).hexdigest()

    def filter_valid_docs(self, docs: Sequence[DocType]) -> Sequence[DocType]:
        return [doc for doc in docs if doc.resource_id]

    def filter_selected_docs(
        self,
        docs: Sequence[DocType],
        allow_overwrite: bool,
        selected_language: str,
        selected_resource_doc_keys: Optional[Set[str]],
    ) -> Sequence[DocType]:
        selected_docs = []

        for doc in docs:
            if selected_language and selected_language != doc.language.value:
                continue

            if not allow_overwrite and doc.resource_doc_id:
                continue

            if selected_resource_doc_keys is not None and doc.doc_key not in selected_resource_doc_keys:
                continue

            selected_docs.append(doc)

        return selected_docs

    def save_docs(self, gateway_id: int, docs: Sequence[DocType]) -> Sequence[DocType]:
        for doc in docs:
            obj, _ = ResourceDoc.objects.update_or_create(
                api_id=gateway_id,
                resource_id=doc.resource_id,
                language=doc.language.value,
                defaults={
                    "type": DocTypeEnum.MARKDOWN.value,
                    "source": DocSourceEnum.IMPORT.value,
                    "content": doc.resource_doc_markdown,
                },
            )
            doc.resource_doc_id = obj.id

        return docs
