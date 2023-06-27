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
import os
from tempfile import TemporaryDirectory

import pytest
from ddf import G

from apigateway.apps.support.constants import DocLanguageEnum
from apigateway.apps.support.models import ResourceDoc, ResourceDocSwagger
from apigateway.apps.support.resource_doc.import_doc.docs import ArchiveDoc, SwaggerDoc
from apigateway.apps.support.resource_doc.import_doc.managers import ArchiveImportDocManager, SwaggerImportDocManager
from apigateway.core.models import Gateway, Resource
from apigateway.utils.file import write_to_file

pytestmark = pytest.mark.django_db


class TestArchiveImportDocManager:
    def test_import_docs(self, mocker, fake_zip_file):
        mocker.patch(
            "apigateway.apps.support.resource_doc.import_doc.managers.ArchiveFileFactory.from_fileobj",
            return_value=mocker.MagicMock(
                **{"extractall.return_value": {"en/get_user.md": "/path/to/en/get_user.md"}}
            ),
        )
        mocker.patch(
            "apigateway.apps.support.resource_doc.import_doc.managers.DocsHandler.handle",
            side_effect=lambda docs: docs,
        )
        gateway = G(Gateway)
        resource = G(Resource, api=gateway, name="get_user")

        manager = ArchiveImportDocManager()
        result = manager.import_docs(
            gateway.id,
            [{"language": "en", "resource_id": resource.id}],
            fake_zip_file,
        )

        assert result is None

    def test_parse_doc_file(self, mocker, fake_zip_file):
        with TemporaryDirectory() as output:
            path = os.path.join(output, "get_user.md")
            write_to_file("# get_user", path)

            mocker.patch(
                "apigateway.apps.support.resource_doc.import_doc.managers.ArchiveFileFactory.from_fileobj",
                return_value=mocker.MagicMock(**{"extractall.return_value": {"en/get_user.md": path}}),
            )
            gateway = G(Gateway)
            resource = G(Resource, name="get_user", api=gateway)

            manager = ArchiveImportDocManager()
            result = manager.parse_doc_file(gateway.id, fake_zip_file)
            assert len(result) == 1
            assert result[0].resource_id == resource.id

    def test_delete_resource_doc_swagger(self):
        gateway = G(Gateway)
        resource = G(Resource, api=gateway)
        resource_doc = G(ResourceDoc, resource_id=resource.id, api=gateway)
        resource_doc_swagger = G(ResourceDocSwagger, resource_doc=resource_doc, api=gateway)

        doc = ArchiveDoc(
            language=DocLanguageEnum.ZH,
            resource_name=resource.name,
            resource_id=resource.id,
            resource_doc_id=resource_doc.id,
            resource_doc_swagger_id=resource_doc_swagger.id,
        )
        manager = ArchiveImportDocManager()
        manager._delete_resource_doc_swagger(gateway.id, [doc])

        assert not ResourceDocSwagger.objects.filter(resource_doc_id=resource_doc.id).exists()


class TestSwaggerImportDocManager:
    def test_import_docs(self, mocker):
        mocker.patch(
            "apigateway.apps.support.resource_doc.import_doc.managers.SwaggerParser.parse",
            return_value=[
                SwaggerDoc(
                    language=DocLanguageEnum.EN,
                    resource_name="get_user",
                )
            ],
        )
        mocker.patch(
            "apigateway.apps.support.resource_doc.import_doc.managers.SwaggerDoc.resource_doc_markdown",
            new_callable=mocker.PropertyMock(return_value=""),
        )

        gateway = G(Gateway)
        resource = G(Resource, api=gateway, name="get_user")

        manager = SwaggerImportDocManager()
        result = manager.import_docs(
            gateway.id,
            DocLanguageEnum.EN,
            [{"language": "en", "resource_id": resource.id}],
            "swagger",
        )

        assert result is None

    def test_save_resource_doc_swagger(self):
        gateway = G(Gateway)
        resource = G(Resource, api=gateway)
        resource_doc = G(ResourceDoc, resource_id=resource.id, api=gateway)

        doc = SwaggerDoc(
            language=DocLanguageEnum.ZH,
            resource_name=resource.name,
            resource_id=resource.id,
            resource_doc_id=resource_doc.id,
        )

        manager = SwaggerImportDocManager()
        manager._save_resource_doc_swagger(gateway.id, [doc])
        assert doc.resource_doc_swagger_id != 0

        manager._save_resource_doc_swagger(gateway.id, [doc])
        assert doc.resource_doc_swagger_id != 0
