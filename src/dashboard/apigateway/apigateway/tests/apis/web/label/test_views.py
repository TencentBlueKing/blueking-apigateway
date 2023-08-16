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
import arrow
from django.test import TestCase
from django_dynamic_fixture import G

from apigateway.apis.web.label.views import GatewayLabelListCreateApi, GatewayLabelRetrieveUpdateDestroyApi
from apigateway.apps.label.models import APILabel
from apigateway.tests.utils.testing import APIRequestFactory, create_gateway, get_response_json


class TestGatewayLabelListCreateApi(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.factory = APIRequestFactory()
        cls.gateway = create_gateway()

    def test_create(self):
        data = {
            "name": "api-label-create-test",
        }
        request = self.factory.post(f"/gateways/{self.gateway.id}/labels/", data=data)

        view = GatewayLabelListCreateApi.as_view()
        response = view(request, gateway_id=self.gateway.id)

        result = get_response_json(response)

        self.assertEqual(response.status_code, 201, result)
        self.assertEqual(APILabel.objects.filter(api=self.gateway, name=data["name"]).count(), 1)

    def test_list(self):
        G(APILabel, api=self.gateway, name="list-01")
        G(APILabel, api=self.gateway, name="test-01")

        data = [
            {
                "expected": 2,
            },
            {
                "name": "list",
                "expected": 1,
            },
            {
                "name": "not-exist",
                "expected": 0,
            },
        ]

        for test in data:
            request = self.factory.get(f"/gateways/{self.gateway.id}/labels/", data=test)

            view = GatewayLabelListCreateApi.as_view()
            response = view(request, gateway_id=self.gateway.id)

            result = get_response_json(response)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(len(result["data"]["results"]), test["expected"])


class TestAPILabelViewSet(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.factory = APIRequestFactory()
        cls.gateway = create_gateway()

    def test_retrieve(self):
        updated_time = arrow.get("2019-01-01 12:30:00").datetime
        api_label = G(APILabel, api=self.gateway, name="test", updated_time=updated_time)

        request = self.factory.get(f"/gateways/{self.gateway.id}/labels/{api_label.id}/")

        view = GatewayLabelRetrieveUpdateDestroyApi.as_view()
        response = view(request, gateway_id=self.gateway.id, id=api_label.id)

        result = get_response_json(response)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            result["data"],
            {
                "id": api_label.id,
                "name": "test",
                "updated_time": "2019-01-01 20:30:00",
            },
        )

    def test_update(self):
        api_label = G(APILabel, api=self.gateway, name="test-01")
        data = {"name": "test-02"}

        request = self.factory.put(f"/gateways/{self.gateway.id}/labels/{api_label.id}/", data=data)

        view = GatewayLabelRetrieveUpdateDestroyApi.as_view()
        response = view(request, gateway_id=self.gateway.id, id=api_label.id)

        self.assertEqual(response.status_code, 204)

        self.assertFalse(APILabel.objects.filter(api=self.gateway, name="test-01").exists())
        self.assertTrue(APILabel.objects.filter(api=self.gateway, name="test-02").exists())

    def test_destroy(self):
        api_label = G(APILabel, api=self.gateway)

        request = self.factory.delete(f"/gateways/{self.gateway.id}/labels/{api_label.id}/")

        view = GatewayLabelRetrieveUpdateDestroyApi.as_view()
        response = view(request, gateway_id=self.gateway.id, id=api_label.id)

        self.assertEqual(response.status_code, 204)
        self.assertFalse(APILabel.objects.filter(id=api_label.id).exists())
