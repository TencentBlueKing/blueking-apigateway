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
from typing import Any, Dict, List, Optional, Set

from apigateway.apps.support.constants import DocSourceEnum, DocTypeEnum
from apigateway.apps.support.models import ResourceDoc

from .models import BaseDoc


class ResourceDocImporter:
    def __init__(
        self,
        gateway_id: int,
        selected_resource_docs: Optional[List[Dict[str, Any]]] = None,
    ):
        self.gateway_id = gateway_id
        self.selected_resource_docs = selected_resource_docs

    def import_docs(self, docs: List[BaseDoc]):
        docs = self._filter_valid_docs(docs)
        docs = self._filter_selected_docs(docs)
        self._save_docs(docs)

    def _filter_valid_docs(self, docs: List[BaseDoc]) -> List[BaseDoc]:
        """
        过滤出有效的资源文档
        - 去除资源不存在的文档
        """
        return [doc for doc in docs if doc.resource]

    def _filter_selected_docs(self, docs: List[BaseDoc]) -> List[BaseDoc]:
        selected_docs = []
        selected_resource_doc_keys = self._get_selected_resource_doc_keys()
        for doc in docs:
            doc_key = f"{doc.language.value}:{doc.resource_name}"
            if selected_resource_doc_keys is not None and doc_key not in selected_resource_doc_keys:
                continue

            selected_docs.append(doc)

        return selected_docs

    def _save_docs(self, docs: List[BaseDoc]):
        add_resource_docs = []
        update_resource_docs = []
        for doc in docs:
            if doc.resource_doc is None:
                add_resource_docs.append(
                    ResourceDoc(
                        api_id=self.gateway_id,
                        resource_id=doc.resource.id,
                        language=doc.language.value,
                        type=DocTypeEnum.MARKDOWN.value,
                        source=DocSourceEnum.IMPORT.value,
                        content=doc.content,
                    )
                )
            else:
                doc.resource_doc.type = DocTypeEnum.MARKDOWN.value
                doc.resource_doc.source = DocSourceEnum.IMPORT.value
                doc.resource_doc.content = doc.content
                update_resource_docs.append(doc.resource_doc)

        if add_resource_docs:
            ResourceDoc.objects.bulk_create(add_resource_docs, batch_size=100)

        if update_resource_docs:
            ResourceDoc.objects.bulk_update(
                update_resource_docs,
                fields=["type", "source", "content"],
                batch_size=100,
            )

    def _get_selected_resource_doc_keys(self) -> Optional[Set[str]]:
        """选择的资源文档 key 的集合，key 为 "{language}:{resource_name}"，如：{"en:get_user"}"""
        if self.selected_resource_docs is None:
            return None

        return {f"{doc['language']}:{doc['resource_name']}" for doc in self.selected_resource_docs}
