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

from apigateway.apis.open.resource import views
from apigateway.core.models import Resource
from apigateway.tests.utils.testing import get_response_json

pytestmark = pytest.mark.django_db


class TestResourceSyncV1ViewSet:
    def test_sync(self, request_factory, fake_gateway, mocker):
        r1 = G(Resource, api=fake_gateway)
        r2 = G(Resource, api=fake_gateway)

        mocker.patch(
            "apigateway.apis.open.resource.views.GatewayRelatedAppPermission.has_permission",
            return_value=True,
        )

        mocker.patch(
            "apigateway.apis.open.resource.views.ResourcesImporter",
            return_value=mocker.MagicMock(
                load_import_resources_by_swagger=mocker.MagicMock(return_value=None),
                import_resources=mocker.MagicMock(return_value=None),
                allow_overwrite=True,
                imported_resources=[
                    {"id": 1, "_is_created": True},
                    {"id": r1.id, "_is_updated": True},
                ],
                get_deleted_resources=mocker.MagicMock(return_value=[{"id": r2.id}]),
            ),
        )

        request = request_factory.post("", data={"content": "test", "delete": True})
        request.gateway = fake_gateway
        request.user = mocker.MagicMock(username="admin")

        view = views.ResourceSyncV1ViewSet.as_view({"post": "sync"})
        response = view(request, gateway_name=fake_gateway.name)
        result = get_response_json(response)

        assert result["code"] == 0, result
        assert result["data"] == {
            "added": [{"id": 1}],
            "updated": [{"id": r1.id}],
            "deleted": [{"id": r2.id}],
        }
