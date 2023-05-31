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
import json

import pytest
from django.http import Http404
from django_dynamic_fixture import G

from apigateway.apps.support.constants import DocLanguageEnum
from apigateway.apps.support.models import ResourceDoc
from apigateway.apps.support.resource_doc import views
from apigateway.apps.support.resource_doc.constants import ZH_RESOURCE_DOC_TMPL
from apigateway.apps.support.resource_doc.import_doc.docs import ArchiveDoc
from apigateway.core.models import Gateway, Resource
from apigateway.tests.utils.testing import APIRequestFactory, create_gateway, get_response_json

pytestmark = pytest.mark.django_db


class TestDeprecatedResourceDocViewSet:
    @pytest.fixture(autouse=True)
    def setup_fixture(self):
        self.factory = APIRequestFactory()
        self.gateway = create_gateway(name="resource-doc")

    def test_retrieve(self):
        resource_1 = G(Resource, api=self.gateway)
        resource_2 = G(Resource, api=self.gateway)
        doc = G(ResourceDoc, api=self.gateway, resource_id=resource_1.id, type="markdown", content="test")

        data = [
            {
                "resource_id": resource_1.id,
                "expected": {
                    "id": doc.id,
                    "type": "markdown",
                    "content": "test",
                    "resource_doc_link": "",
                    "language": "zh",
                },
            },
            {
                "resource_id": resource_2.id,
                "expected": {
                    "id": None,
                    "type": "markdown",
                    "content": ZH_RESOURCE_DOC_TMPL.replace("__API_NAME__", "resource_doc"),
                    "resource_doc_link": "",
                    "language": "zh",
                },
            },
        ]
        for test in data:
            resource_id = test["resource_id"]
            request = self.factory.get(f"/apis/{self.gateway.id}/support/resources/{resource_id}/doc/", data=test)

            view = views.DeprecatedResourceDocViewSet.as_view({"get": "retrieve"})
            response = view(request, gateway_id=self.gateway.id, resource_id=resource_id)

            result = get_response_json(response)
            assert result["code"] == 0
            assert result["data"] == test["expected"]

    def test_update(self):
        resource = G(Resource, api=self.gateway)

        data = [
            {
                # create doc
                "resource_id": resource.id,
                "params": {
                    "type": "markdown",
                    "content": "test",
                },
            },
            {
                # update doc
                "resource_id": resource.id,
                "params": {
                    "type": "markdown",
                    "content": "test-test",
                },
            },
        ]
        for test in data:
            request = self.factory.post(
                f"/apis/{self.gateway.id}/support/resources/{resource.id}/doc/",
                data=test["params"],
            )

            view = views.DeprecatedResourceDocViewSet.as_view({"post": "update"})
            response = view(request, gateway_id=self.gateway.id, resource_id=resource.id)

            result = get_response_json(response)
            assert result["code"] == 0

            doc = ResourceDoc.objects.get(api=self.gateway, resource_id=resource.id)
            assert test["params"]["type"] == doc.type
            assert test["params"]["content"] == doc.content


class TestResourceDocViewSet:
    @pytest.fixture(autouse=True)
    def setup_fixture(self, faker):
        self.factory = APIRequestFactory()
        self.gateway = create_gateway(name=faker.uuid4())

    def test_check_resource_permission(self):
        api1 = G(Gateway)
        api2 = G(Gateway)

        r1 = G(Resource, api=api1)
        r2 = G(Resource, api=api2)

        view = views.ResourceDocViewSet()
        view._check_resource_permission(r1.id, api1.id)

        # 资源不属于网关
        with pytest.raises(Http404):
            view._check_resource_permission(r2.id, api1.id)

    def test_create(self):
        resource = G(Resource, api=self.gateway)

        request = self.factory.post(
            "",
            data={
                "type": "markdown",
                "language": "zh",
                "content": "test",
            },
        )
        view = views.ResourceDocViewSet.as_view({"post": "create"})
        response = view(request, gateway_id=self.gateway.id, resource_id=resource.id)

        result = get_response_json(response)
        assert result["code"] == 0
        assert result["data"]["id"] != 0

    def test_update(self):
        resource = G(Resource, api=self.gateway)
        resource_doc = G(ResourceDoc, resource_id=resource.id, api=self.gateway)

        request = self.factory.put(
            "",
            data={
                "type": "markdown",
                "language": "zh",
                "content": "test",
            },
        )
        view = views.ResourceDocViewSet.as_view({"put": "update"})
        response = view(request, gateway_id=self.gateway.id, resource_id=resource.id, id=resource_doc.id)

        result = get_response_json(response)
        assert result["code"] == 0

    def test_list(self):
        resource = G(Resource, api=self.gateway)
        G(ResourceDoc, resource_id=resource.id, api=self.gateway)

        request = self.factory.get("")
        view = views.ResourceDocViewSet.as_view({"get": "list"})
        response = view(request, gateway_id=self.gateway.id, resource_id=resource.id)

        result = get_response_json(response)
        assert result["code"] == 0
        assert len(result["data"]) == 2


class TestArchiveDocParseViewSet:
    @pytest.fixture(autouse=True)
    def setup_fixture(self, faker):
        self.factory = APIRequestFactory()
        self.gateway = create_gateway(name=faker.uuid4())

    def test_parse(self, mocker, faker, fake_zip_file):
        mocker.patch(
            "apigateway.apps.support.resource_doc.views.ArchiveImportDocManager.parse_doc_file",
            return_value=[
                ArchiveDoc(
                    language=DocLanguageEnum.ZH,
                    resource_name=faker.pystr(),
                    filename=faker.pystr(),
                    resource_doc_path=faker.pystr(),
                )
            ],
        )
        request = self.factory.post(
            "",
            data={
                "file": fake_zip_file,
            },
            format="multipart",
        )
        view = views.ArchiveDocParseViewSet.as_view({"post": "parse"})
        response = view(request, gateway_id=self.gateway.id)

        result = get_response_json(response)
        assert result["code"] == 0


class TestResourceDocImportExportViewSet:
    @pytest.fixture(autouse=True)
    def setup_fixture(self, faker):
        self.factory = APIRequestFactory()
        self.gateway = create_gateway(name=faker.uuid4())

    def test_import_by_archive(self, mocker, fake_zip_file):
        mocker.patch(
            "apigateway.apps.support.resource_doc.views.ArchiveImportDocManager.import_docs",
            return_value=None,
        )
        mocker.patch(
            "apigateway.apps.support.resource_doc.views.Resource.objects.filter_resource_name_to_id",
            return_value={"get_user": 1},
        )

        request = self.factory.post(
            "",
            data={
                "selected_resource_docs": json.dumps(
                    [
                        {
                            "language": "zh",
                            "resource_name": "get_user",
                        }
                    ]
                ),
                "file": fake_zip_file,
            },
            format="multipart",
        )

        view = views.ResourceDocImportExportViewSet.as_view({"post": "import_by_archive"})
        response = view(request, gateway_id=self.gateway.id)

        result = get_response_json(response)
        assert result["code"] == 0, result

    def test_import_by_swagger(self, mocker, faker):
        mocker.patch(
            "apigateway.apps.support.resource_doc.views.SwaggerImportDocManager.import_docs",
            return_value=None,
        )
        mocker.patch(
            "apigateway.apps.support.resource_doc.views.Resource.objects.filter_resource_name_to_id",
            return_value={"get_user": 1},
        )

        request = self.factory.post(
            "",
            data={
                "selected_resource_docs": [
                    {
                        "language": "zh",
                        "resource_name": "get_user",
                    }
                ],
                "swagger": faker.pystr(),
            },
        )
        view = views.ResourceDocImportExportViewSet.as_view({"post": "import_by_swagger"})
        response = view(request, gateway_id=self.gateway.id)

        result = get_response_json(response)
        assert result["code"] == 0

    def test_export(self, faker):
        resource = G(Resource, api=self.gateway, name=faker.pystr())
        G(ResourceDoc, resource_id=resource.id, api=self.gateway)

        request = self.factory.post(
            "",
            data={
                "export_type": "all",
                "file_type": "zip",
            },
        )
        view = views.ResourceDocImportExportViewSet.as_view({"post": "export"})
        response = view(request, gateway_id=self.gateway.id)

        assert response.status_code == 200
