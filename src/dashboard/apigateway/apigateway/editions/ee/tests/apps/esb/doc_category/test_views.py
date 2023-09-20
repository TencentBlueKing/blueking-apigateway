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
import pytest
from ddf import G

from apigateway.apps.esb.bkcore.models import DocCategory, SystemDocCategory
from apigateway.apps.esb.constants import DataTypeEnum
from apigateway.apps.esb.doc_category import views
from apigateway.tests.utils.testing import get_response_json

pytestmark = [pytest.mark.django_db]


class TestDocCategoryViewSet:
    @pytest.fixture(autouse=True)
    def setup_fixture(self, request_factory):
        self.factory = request_factory

    def test_list(self):
        G(DocCategory)

        request = self.factory.get("/")

        view = views.DocCategoryViewSet.as_view({"get": "list"})
        response = view(request)
        result = get_response_json(response)

        assert response.status_code == 200
        assert len(result["data"]) >= 1

    def test_retrieve(self):
        doc_category = G(DocCategory)

        request = self.factory.get("/")
        view = views.DocCategoryViewSet.as_view({"get": "retrieve"})
        response = view(request, id=doc_category.id)
        result = get_response_json(response)

        assert response.status_code == 200
        assert result["data"]["id"] == doc_category.id

    def test_create(self, settings):
        view = views.DocCategoryViewSet.as_view({"post": "create"})
        request = self.factory.post(
            "/",
            data={
                "name": "test-create",
                "priority": 300,
            },
        )
        response = view(request)
        result = get_response_json(response)
        doc_category = DocCategory.objects.get(id=result["data"]["id"])

        assert response.status_code == 200
        assert doc_category.board == settings.ESB_DEFAULT_BOARD
        assert doc_category.data_type == 3
        assert doc_category.priority == 300
        assert doc_category.name == "test-create"

    def test_update(self):
        doc_category = G(DocCategory)
        view = views.DocCategoryViewSet.as_view({"put": "update"})

        request = self.factory.put(
            "/",
            data={
                "name": "test-update",
                "priority": 3000,
            },
        )
        response = view(request, id=doc_category.id)
        doc_category = DocCategory.objects.get(id=doc_category.id)

        assert response.status_code == 200
        assert doc_category.priority == 3000
        assert doc_category.name == "test-update"

    def test_delete(self):
        doc_category = G(DocCategory, data_type=DataTypeEnum.CUSTOM.value)
        view = views.DocCategoryViewSet.as_view({"delete": "destroy"})

        request = self.factory.delete("/")
        response = view(request, id=doc_category.id)
        get_response_json(response)

        assert response.status_code == 200
        assert not DocCategory.objects.filter(id=doc_category.id).exists()

        # official, delete fail
        doc_category = G(DocCategory, data_type=DataTypeEnum.OFFICIAL_PUBLIC.value)
        response = view(request, id=doc_category.id)
        # result = get_response_json(response)
        _ = get_response_json(response)

        assert response.status_code == 400
        assert DocCategory.objects.filter(id=doc_category.id).exists()

        # system-doc-category exists, delete fail
        doc_category = G(DocCategory, data_type=DataTypeEnum.CUSTOM.value)
        G(SystemDocCategory, doc_category=doc_category)
        response = view(request, id=doc_category.id)
        # result = get_response_json(response)
        _ = get_response_json(response)

        assert response.status_code == 400
        assert DocCategory.objects.filter(id=doc_category.id).exists()
        assert SystemDocCategory.objects.filter(doc_category_id=doc_category.id).exists()
