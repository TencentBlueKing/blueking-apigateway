# -*- coding: utf-8 -*-
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
from ddf import G
from django.test import Client
from django.urls import reverse

from apigateway.core.models import Gateway, Release


class TestGatewayListApi:
    def test_list(self, request_view, fake_gateway):
        G(Release, gateway=fake_gateway)

        resp = request_view(
            method="GET",
            view_name="docs.gateway.list",
        )
        result = resp.json()

        assert resp.status_code == 200
        assert len(result["data"]["results"]) >= 1

    def test_list_paginates_after_official_sort(self, request_view, unique_id):
        normal_gateway = G(
            Gateway,
            name=f"zz-normal-{unique_id[:8]}",
            status=1,
            is_public=True,
            tenant_mode="single",
            tenant_id="default",
        )
        official_gateway = G(
            Gateway,
            name=f"aa-official-{unique_id[:8]}",
            status=1,
            is_public=True,
            is_official=True,
            tenant_mode="single",
            tenant_id="default",
        )
        G(Release, gateway=normal_gateway)
        G(Release, gateway=official_gateway)

        resp = request_view(
            method="GET",
            view_name="docs.gateway.list",
            data={
                "keyword": unique_id[:8],
                "limit": 1,
            },
        )
        result = resp.json()

        assert resp.status_code == 200
        assert result["data"]["count"] == 2
        assert len(result["data"]["results"]) == 1
        assert result["data"]["results"][0]["id"] == official_gateway.id
        assert result["data"]["results"][0]["is_official"] is True


class TestGatewayRetrieveApi:
    def test_retrieve_without_login(self, fake_gateway):
        resp = Client().get(reverse("docs.gateway.retrieve", kwargs={"gateway_name": fake_gateway.name}))

        assert resp.status_code == 401

    def test_retrieve(self, request_view, fake_gateway, fake_sdk):
        resp = request_view(
            method="GET",
            view_name="docs.gateway.retrieve",
            path_params={"gateway_name": fake_gateway.name},
            gateway=fake_gateway,
        )
        result = resp.json()

        assert resp.status_code == 200
        assert result["data"]["is_official"] is False

        assert len(result["data"]["sdks"]) == 1

        fake_gateway.is_public = False
        fake_gateway.save()

        resp = request_view(
            method="GET",
            view_name="docs.gateway.retrieve",
            path_params={"gateway_name": fake_gateway.name},
            gateway=fake_gateway,
        )
        assert resp.status_code == 404
