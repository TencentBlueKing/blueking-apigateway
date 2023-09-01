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
import json

from apigateway.apps.support.constants import DocLanguageEnum
from apigateway.biz.resource_doc.importer.models import ArchiveDoc


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
    def post(self, request_view, fake_gateway, mocker, faker, fake_tgz_file):
        mocker.patch("apigateway.apis.web.resource_doc.views.ArchiveParser.parse", return_value=[])
        mocker.patch("apigateway.apis.web.resource_doc.views.DocImporter.import_docs")

        resp = request_view(
            method="POST",
            view_name="resource_doc.import.by_archive",
            path_params={"gateway_id": fake_gateway.id},
            data={
                "selected_resource_docs": json.dumps(
                    [
                        {
                            "language": "zh",
                            "resource_name": faker.pystr(),
                        }
                    ]
                ),
                "file": fake_tgz_file,
            },
            format="multipart",
        )

        assert resp.status_code == 200


class TestDocImportBySwaggerApi:
    def test_post(self, request_view, fake_gateway, mocker, faker):
        mocker.patch("apigateway.apis.web.resource_doc.views.SwaggerParser.parse", return_value=[])
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

        assert resp.status_code == 200


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
