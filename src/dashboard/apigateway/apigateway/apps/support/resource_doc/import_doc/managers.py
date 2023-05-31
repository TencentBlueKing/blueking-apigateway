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
from tempfile import TemporaryDirectory
from typing import IO, Any, AnyStr, Dict, List, Optional, Sequence

from apigateway.apps.support.constants import DocLanguageEnum
from apigateway.apps.support.models import ResourceDocSwagger
from apigateway.apps.support.resource_doc.import_doc.docs import ArchiveDoc, BaseDoc, SwaggerDoc
from apigateway.apps.support.resource_doc.import_doc.handlers import DocsHandler
from apigateway.apps.support.resource_doc.import_doc.parsers import ArchiveParser, SwaggerParser
from apigateway.apps.support.utils import ArchiveFileFactory


class ArchiveImportDocManager:
    """通过归档文件导入资源文档"""

    def import_docs(self, gateway_id: int, selected_resource_docs: Optional[List[Dict[str, Any]]], archive_file: Any):
        parser = ArchiveParser()
        handler = DocsHandler(
            gateway_id=gateway_id,
            allow_overwrite=True,
            selected_language="",
            selected_resource_docs=selected_resource_docs,
        )

        with TemporaryDirectory() as output_dir:
            files = ArchiveFileFactory.from_fileobj(archive_file).extractall(output_dir, archive_file)

            docs = parser.parse(files)
            handled_docs = handler.handle(docs)

            self._delete_resource_doc_swagger(gateway_id, handled_docs)

    def parse_doc_file(self, gateway_id: int, archive_file: IO[AnyStr]) -> Sequence[ArchiveDoc]:
        """解析文档文件，将文档文件中的文件名（如：`zh/get_user.md`）解析出其对应的资源、资源文档"""
        parser = ArchiveParser()
        handler = DocsHandler(gateway_id=gateway_id)

        filenames = ArchiveFileFactory.from_fileobj(archive_file).get_names(archive_file)
        docs = parser.parse({name: "" for name in filenames})
        return handler.enrich_docs(gateway_id, docs)

    def _delete_resource_doc_swagger(self, gateway_id: int, docs: Sequence[BaseDoc]):
        """删除关联的 swagger 文档"""
        # 此次为归档文件方式导入，如果资源前文档通过 swagger 方式导入，删除对应的 swagger 扩展文档
        resource_doc_swagger_ids = [doc.resource_doc_swagger_id for doc in docs if doc.resource_doc_swagger_id]
        if resource_doc_swagger_ids:
            ResourceDocSwagger.objects.filter(api_id=gateway_id, id__in=resource_doc_swagger_ids).delete()


class SwaggerImportDocManager:
    """通过 Swagger 描述导入资源文档"""

    def import_docs(
        self,
        gateway_id: int,
        selected_language: DocLanguageEnum,
        selected_resource_docs: Optional[List[Dict[str, Any]]],
        swagger: str,
    ):
        parser = SwaggerParser()
        handler = DocsHandler(
            gateway_id=gateway_id,
            allow_overwrite=True,
            selected_language=selected_language.value,
            selected_resource_docs=selected_resource_docs,
        )

        docs = parser.parse(swagger, language=selected_language)
        handled_docs = handler.handle(docs)

        self._save_resource_doc_swagger(gateway_id, handled_docs)

    def _save_resource_doc_swagger(self, gateway_id: int, docs: Sequence[SwaggerDoc]):
        """保存关联的 swagger 文档"""
        for doc in docs:
            obj, _ = ResourceDocSwagger.objects.update_or_create(
                api_id=gateway_id,
                resource_doc_id=doc.resource_doc_id,
                defaults={
                    "swagger": doc.resource_doc_swagger,
                },
            )
            doc.resource_doc_swagger_id = obj.id

        return docs
