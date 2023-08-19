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
class TestResourceDocImportByArchiveApi:
    def test_post(self, request_view, mocker, fake_tgz_file, ignore_related_app_permission, fake_gateway):
        mocker.patch("apigateway.apis.open.resource_doc.views.ArchiveParser.parse", return_value=[])
        mocker.patch("apigateway.apis.open.resource_doc.views.ResourceDocImporter.import_docs")

        resp = request_view(
            method="POST",
            view_name="openapi.resource_doc.import.by_archive",
            path_params={"gateway_name": fake_gateway.name},
            data={
                "file": fake_tgz_file,
            },
            format="multipart",
        )
        result = resp.json()

        assert resp.status_code == 200
        assert result["code"] == 0


class TestResourceDocImportBySwaggerApi:
    def test_post(self, request_view, mocker, faker, ignore_related_app_permission, fake_gateway):
        mocker.patch("apigateway.apis.web.resource_doc.views.SwaggerParser.parse", return_value=[])
        mocker.patch("apigateway.apis.web.resource_doc.views.ResourceDocImporter.import_docs")

        resp = request_view(
            method="POST",
            view_name="openapi.resource_doc.import.by_swagger",
            path_params={"gateway_name": fake_gateway.name},
            data={
                "swagger": faker.pystr(),
                "language": "zh",
            },
        )
        result = resp.json()

        assert resp.status_code == 200
        assert result["code"] == 0
