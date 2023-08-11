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

from django.test import TestCase
from django_dynamic_fixture import G

from apigateway.apis.open.access_strategy import views
from apigateway.apps.access_strategy.models import AccessStrategy, AccessStrategyBinding, IPGroup
from apigateway.common.factories import SchemaFactory
from apigateway.core.models import Stage
from apigateway.tests.utils.testing import APIRequestFactory, create_gateway, get_response_json


class TestIPGroupV1ViewSet(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.factory = APIRequestFactory()

    def test_post(self):
        gateway = create_gateway()

        data = [
            # new ip-group
            {
                "params": {
                    "name": "test",
                    "ips": "1.0.0.1",
                    "action": "append",
                },
                "expected": {
                    "ips": "1.0.0.1",
                    "created": True,
                },
            },
            # append ip to exist ip-group
            {
                "params": {
                    "name": "test",
                    "ips": "1.0.0.2",
                    "action": "append",
                },
                "expected": {
                    "ips": "1.0.0.1\n1.0.0.2",
                    "created": False,
                },
            },
            # append exist ip to exist ip-group
            {
                "params": {
                    "name": "test",
                    "ips": "1.0.0.2",
                    "action": "append",
                },
                "expected": {
                    "ips": "1.0.0.1\n1.0.0.2",
                    "created": False,
                },
            },
            # set ip to ip-group
            {
                "params": {
                    "name": "test",
                    "ips": "1.0.0.2",
                    "action": "set",
                },
                "expected": {
                    "ips": "1.0.0.2",
                    "created": False,
                },
            },
        ]

        for test in data:
            request = self.factory.post(
                f"/api/v1/apis/{gateway.id}/access-strategies/ip-groups/",
                data=test["params"],
            )

            view = views.IPGroupV1ViewSet.as_view({"post": "post"})
            response = view(request, gateway_id=gateway.id)

            result = get_response_json(response)
            # self.assertEqual(result["code"], 0, result)
            self.assertEqual(response.status_code, 200, result)
            self.assertEqual(result["data"]["created"], test["expected"]["created"])

            ip_group = IPGroup.objects.get(api=gateway, name=test["params"]["name"])
            self.assertEqual(ip_group._ips, test["expected"]["ips"])


class TestAccessStrategyAddIPGroupsV1APIView(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.factory = APIRequestFactory()
        cls.gateway = create_gateway()

    def test_post(self):
        strategy = G(
            AccessStrategy,
            api=self.gateway,
            type="ip_access_control",
            schema=SchemaFactory().get_access_strategy_schema("ip_access_control"),
            _config=json.dumps(
                {
                    "type": "allow",
                    "ip_group_list": [],
                }
            ),
        )

        ip_group_1 = G(IPGroup, api=self.gateway)
        ip_group_2 = G(IPGroup, api=self.gateway)
        ip_group_3 = G(IPGroup, api=self.gateway)

        data = [
            {
                "params": {
                    "access_strategy_ids": [strategy.id],
                    "ip_group_list": [ip_group_1.id],
                },
                "expected": {
                    "ip_group_list": [ip_group_1.id],
                },
            },
            {
                "params": {
                    "access_strategy_ids": [strategy.id],
                    "ip_group_list": [ip_group_1.id, ip_group_2.id],
                },
                "expected": {
                    "ip_group_list": [ip_group_1.id, ip_group_2.id],
                },
            },
            {
                "params": {
                    "access_strategy_ids": [strategy.id, strategy.id],
                    "ip_group_list": [ip_group_2.id, ip_group_3.id],
                },
                "expected": {
                    "ip_group_list": [ip_group_1.id, ip_group_2.id, ip_group_3.id],
                },
            },
        ]

        for test in data:
            request = self.factory.post(
                f"/api/v1/apis/{self.gateway.id}/access-strategies/add-ip-groups-to-strategies/",
                data=test["params"],
            )

            view = views.AccessStrategyAddIPGroupsV1APIView.as_view()
            response = view(request, gateway_id=self.gateway.id)

            result = get_response_json(response)
            # self.assertEqual(result["code"], 0, result)
            self.assertEqual(response.status_code, 200, result)

            strategy = AccessStrategy.objects.get(id=strategy.id)
            self.assertEqual(strategy.config["ip_group_list"], test["expected"]["ip_group_list"])


class TestAccessStrategySyncViewSet:
    def test_sync(self, fake_gateway, request_factory, mocker):
        mocker.patch(
            "apigateway.apis.open.access_strategy.views.GatewayRelatedAppPermission.has_permission",
            return_value=True,
        )
        stage = G(Stage, api=fake_gateway, name="prod")

        request = request_factory.post(
            f"/api/v1/apis/{fake_gateway.name}/access_strategies/sync/",
            data={
                "name": "rate_limit_prod",
                "comment": "sync",
                "scope_type": "stage",
                "type": "rate_limit",
                "rate_limit": {
                    "rates": {
                        "__default": [
                            {
                                "tokens": 100,
                                "period": 60,
                            }
                        ]
                    }
                },
                "scopes": [
                    {
                        "name": "prod",
                    }
                ],
            },
        )
        request.gateway = fake_gateway

        view = views.AccessStrategySyncViewSet.as_view({"post": "sync"})
        response = view(request, gateway_name=fake_gateway.name)

        result = get_response_json(response)

        assert result["code"] == 0, result
        assert AccessStrategy.objects.filter(api=fake_gateway, type="rate_limit", name="rate_limit_prod").exists()
        assert AccessStrategyBinding.objects.filter(
            scope_type="stage",
            scope_id=stage.id,
            type="rate_limit",
        ).exists()
