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
import json

import pytest

from apigateway.apps.support.constants import DocLanguageEnum
from apigateway.biz.resource_doc import NoResourceDocError, ResourceDocJinja2TemplateError
from apigateway.biz.resource_doc.importer import ArchiveDoc


class TestDocArchiveParseApi:
    def test_post(self, request_view, fake_gateway, mocker, faker, fake_tgz_file):
        mocker.patch(
            "apigateway.apis.web.resource_doc.views.ArchiveParser.parse",
            return_value=[
                ArchiveDoc(
                    resource_name=faker.pystr(),
                    language=DocLanguageEnum.ZH,
                    content=faker.pystr(),
                    content_changed=True,
                    filename=faker.pystr(),
                )
            ],
        )

        resp = request_view(
            method="POST",
            view_name="resource_doc.archive.parse",
            path_params={"gateway_id": fake_gateway.id},
            data={
                "file": fake_tgz_file,
            },
            format="multipart",
        )

        assert resp.status_code == 200


class TestDocImportByArchiveApi:
    def test_post(self, request_view, fake_gateway, mocker, fake_tgz_file):
        docs = [
            ArchiveDoc(
                resource_name="get_user",
                language=DocLanguageEnum.ZH,
                content="# user",
                content_changed=True,
                filename="zh/get_user.md",
            )
        ]
        parser = mocker.patch("apigateway.apis.web.resource_doc.views.ArchiveParser", autospec=True)
        parser.return_value.parse.return_value = docs
        importer = mocker.patch("apigateway.apis.web.resource_doc.views.DocImporter", autospec=True)
        selected = [{"language": "zh", "resource_name": "get_user"}]
        resp = request_view(
            method="POST",
            view_name="resource_doc.import.by_archive",
            path_params={"gateway_id": fake_gateway.id},
            data={"selected_resource_docs": json.dumps(selected), "file": fake_tgz_file},
            format="multipart",
        )
        assert resp.status_code == 204
        parser.assert_called_once_with(gateway_id=fake_gateway.id)
        assert parser.return_value.parse.call_count == 1
        importer.assert_called_once_with(gateway_id=fake_gateway.id, selected_resource_docs=selected)
        importer.return_value.import_docs.assert_called_once_with(docs=docs)


class TestDocImportBySwaggerApi:
    def test_post(self, request_view, fake_gateway, mocker, faker):
        mocker.patch("apigateway.apis.web.resource_doc.views.OpenAPIParser.parse", return_value=[])
        mocker.patch("apigateway.apis.web.resource_doc.views.DocImporter.import_docs")

        resp = request_view(
            method="POST",
            view_name="resource_doc.import.by_swagger",
            path_params={"gateway_id": fake_gateway.id},
            data={
                "selected_resource_docs": [
                    {
                        "language": "zh",
                        "resource_name": "get_user",
                    }
                ],
                "swagger": faker.pystr(),
                "language": "zh",
            },
        )

        assert resp.status_code == 204


class TestDocExportApi:
    def test_post(self, request_view, fake_resource_doc):
        fake_gateway = fake_resource_doc.gateway

        resp = request_view(
            method="POST",
            view_name="resource_doc.export",
            path_params={"gateway_id": fake_gateway.id},
            data={
                "export_type": "all",
                "file_type": "tgz",
            },
        )

        assert resp.status_code == 200


@pytest.mark.parametrize(
    "error, status, code",
    [
        (NoResourceDocError(), 400, "INVALID_ARGUMENT"),
        (ResourceDocJinja2TemplateError("resource.md", ValueError("bad template")), 500, "INTERNAL"),
    ],
)
def test_archive_import_reports_parse_error_without_importing(
    request_view, fake_gateway, fake_tgz_file, mocker, error, status, code
):
    mocker.patch("apigateway.apis.web.resource_doc.views.ArchiveParser.parse", side_effect=error)
    importer = mocker.patch("apigateway.apis.web.resource_doc.views.DocImporter.import_docs")
    response = request_view(
        method="POST",
        view_name="resource_doc.import.by_archive",
        path_params={"gateway_id": fake_gateway.id},
        format="multipart",
        data={"selected_resource_docs": "[]", "file": fake_tgz_file},
    )
    assert response.status_code == status
    assert response.json()["error"]["code"] == code
    importer.assert_not_called()
