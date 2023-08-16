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

from apigateway.apps.esb.bkcore.models import ComponentSystem, DocCategory
from apigateway.apps.esb.constants import DataTypeEnum
from apigateway.apps.esb.system import views
from apigateway.tests.utils.testing import get_response_json

pytestmark = [pytest.mark.django_db]


class TestSystemViewSet:
    @pytest.fixture(autouse=True)
    def setup_fixture(self, request_factory):
        self.factory = request_factory

    def test_list(self):
        G(ComponentSystem)

        request = self.factory.get("/")

        view = views.SystemViewSet.as_view({"get": "list"})
        response = view(request)
        result = get_response_json(response)

        assert response.status_code == 200
        assert len(result["data"]) >= 1

    def test_retrieve(self):
        system = G(ComponentSystem)

        request = self.factory.get("/")

        view = views.SystemViewSet.as_view({"get": "retrieve"})
        response = view(request, id=system.id)
        result = get_response_json(response)

        assert response.status_code == 200
        assert result["data"]["id"] == system.id

    def test_create(self, settings):
        doc_category = G(DocCategory, board=settings.ESB_DEFAULT_BOARD)
        view = views.SystemViewSet.as_view({"post": "create"})
        request = self.factory.post(
            "/",
            data={
                "name": "test_create",
                "description": "desc",
                "comment": "comment",
                "timeout": None,
                "maintainers": ["admin"],
                "doc_category_id": doc_category.id,
            },
        )
        response = view(request)
        result = get_response_json(response)
        system = ComponentSystem.objects.get(id=result["data"]["id"])

        assert response.status_code == 200
        assert system.board == settings.ESB_DEFAULT_BOARD
        assert system.data_type == 3
        assert system.timeout is None

    def test_update(self, settings):
        system = G(ComponentSystem)
        doc_category = G(DocCategory, board=settings.ESB_DEFAULT_BOARD)
        view = views.SystemViewSet.as_view({"put": "update"})

        request = self.factory.put(
            "/",
            data={
                "name": "test_udpate",
                "description": "desc",
                "comment": "comment",
                "timeout": 30,
                "maintainers": ["admin"],
                "doc_category_id": doc_category.id,
            },
        )
        response = view(request, id=system.id)
        get_response_json(response)
        system = ComponentSystem.objects.get(id=system.id)

        assert response.status_code == 200
        assert system.timeout == 30
        assert system.maintainers == ["admin"]

    def test_delete(self):
        view = views.SystemViewSet.as_view({"delete": "destroy"})

        system = G(ComponentSystem, data_type=DataTypeEnum.CUSTOM.value)
        request = self.factory.delete("/")
        response = view(request, id=system.id)
        get_response_json(response)

        assert response.status_code == 200
        assert not ComponentSystem.objects.filter(id=system.id).exists()

        # system is official
        system = G(ComponentSystem, data_type=DataTypeEnum.OFFICIAL_PUBLIC.value)
        request = self.factory.delete("/")
        response = view(request, id=system.id)

        assert response.status_code == 400
        assert ComponentSystem.objects.filter(id=system.id).exists()
