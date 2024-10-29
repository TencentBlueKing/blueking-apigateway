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
from unittest import mock

from django_dynamic_fixture import G

from apigateway.core.constants import GatewayStatusEnum
from apigateway.core.models import Gateway, Release
from apigateway.tests.utils.testing import get_response_json


class TestGatewayListApi:
    def test_list(self, request_view, fake_gateway, mocker):
        g1 = G(Gateway, status=GatewayStatusEnum.ACTIVE.value, is_public=False)
        G(Release, gateway=g1)
        g2 = G(Gateway, status=GatewayStatusEnum.INACTIVE.value, is_public=True)
        G(Release, gateway=g2)

        _ = G(Gateway, status=GatewayStatusEnum.ACTIVE.value, is_public=True)

        # released
        g4 = G(Gateway, status=GatewayStatusEnum.ACTIVE.value, is_public=True)
        G(Release, gateway=g4)
        G(Release, gateway=fake_gateway)

        resp = request_view(
            method="GET",
            view_name="openapi.v2.inner.gateway.list",
            app=mock.MagicMock(app_code="test"),
        )
        result = resp.json()
        assert resp.status_code == 200
        assert len(result["data"]) == 2


class TestGatewayRetrieveApi:
    def test_retrieve(self, request_to_view, request_factory, fake_gateway):
        request = request_factory.get("")
        request.gateway = fake_gateway
        request.app = mock.MagicMock(app_code="test")
        response = request_to_view(
            request,
            view_name="openapi.v2.inner.gateway.retrieve",
            path_params={"gateway_name": fake_gateway.name},
        )
        result = get_response_json(response)

        assert response.status_code == 200
        assert result["data"]["name"] == fake_gateway.name
