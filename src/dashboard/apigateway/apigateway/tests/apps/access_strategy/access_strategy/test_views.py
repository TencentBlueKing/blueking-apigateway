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
from django.test import TestCase
from django_dynamic_fixture import G

from apigateway.apps.access_strategy.access_strategy.views import AccessStrategyViewSet
from apigateway.apps.access_strategy.models import AccessStrategy, AccessStrategyBinding
from apigateway.common.factories import SchemaFactory
from apigateway.tests.utils.testing import APIRequestFactory, create_gateway, get_response_json

pytestmark = pytest.mark.django_db


@pytest.mark.django_db
class TestAccessStrategyViewSetWithPytest:
    @pytest.mark.parametrize(
        "params, expected",
        [
            (
                {
                    "ip_access_control": {
                        "type": "allow",
                        "ip_group_list": [1, 2, 3],
                    },
                    "rate_limit": None,
                    "name": "test",
                    "type": "ip_access_control",
                    "comment": "comment",
                },
                {
                    "config": {
                        "type": "allow",
                        "ip_group_list": [1, 2, 3],
                    },
                },
            ),
            (
                {
                    "user_verified_unrequired_apps": {
                        "bk_app_code_list": ["test"],
                    },
                    "name": "test",
                    "type": "user_verified_unrequired_apps",
                    "comment": "comment",
                },
                {
                    "config": {
                        "bk_app_code_list": ["test"],
                    }
                },
            ),
        ],
    )
    def test_create(self, request_factory, fake_gateway, mocker, params, expected):
        request = request_factory.post(f"/apis/{fake_gateway.id}/access_strategies/", data=params)
        view = AccessStrategyViewSet.as_view({"post": "create"})
        response = view(request, gateway_id=fake_gateway.id)
        # result = get_response_json(response)

        # assert result["code"] == 0
        assert response.status_code == 200

        access_strategy = AccessStrategy.objects.get(
            api=fake_gateway,
            name=params["name"],
            type=params["type"],
        )
        assert access_strategy.name == params["name"]
        assert access_strategy.config == expected["config"]

        # create again, name + type exist, will error
        request = request_factory.post(f"/apis/{fake_gateway.id}/access_strategies/", data=params)
        view = AccessStrategyViewSet.as_view({"post": "create"})
        response = view(request, gateway_id=fake_gateway.id)
        # result = get_response_json(response)

        # assert result["code"] != 0
        assert response.status_code != 200


class TestAccessStrategyViewSet(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.factory = APIRequestFactory()
        cls.gateway = create_gateway()

    def test_list(self):
        G(AccessStrategy, api=self.gateway, name="test-01")
        G(AccessStrategy, api=self.gateway, name="test-02")

        data = [
            {
                "expected": {
                    "count": 2,
                }
            },
            {
                "query": "test-01",
                "expected": {
                    "count": 1,
                },
            },
        ]
        for test in data:
            request = self.factory.get(f"/apis/{self.gateway.id}/access_strategies/", data=test)

            view = AccessStrategyViewSet.as_view({"get": "list"})
            response = view(request, gateway_id=self.gateway.id)

            result = get_response_json(response)
            # self.assertEqual(result["code"], 0, result)
            assert response.status_code == 200
            self.assertEqual(result["data"]["count"], test["expected"]["count"])

    def test_update(self):
        access_strategy = G(
            AccessStrategy,
            api=self.gateway,
            type="ip_access_control",
            _config=json.dumps(
                {
                    "type": "allow",
                    "ip_group_list": [1, 2, 3],
                }
            ),
            schema=SchemaFactory().get_access_strategy_schema("ip_access_control"),
        )

        data = [
            # ok
            {
                "name": "test-update",
                "type": "ip_access_control",
                "comment": "comment",
                "ip_access_control": {
                    "type": "allow",
                    "ip_group_list": [4, 5, 6],
                },
                "expected": {
                    "config": {
                        "type": "allow",
                        "ip_group_list": [4, 5, 6],
                    }
                },
            },
            # error, type not equal
            {
                "name": "test-update",
                "type": "rate_limit",
                "comment": "comment",
                "rate_limit": {
                    "rates": {
                        "__default": [
                            {
                                "tokens": 100,
                                "period": 60,
                            }
                        ]
                    },
                },
                "will_error": True,
            },
            # error, ip_access_control.type not equal
            {
                "name": "test-update",
                "type": "ip_access_control",
                "comment": "comment",
                "ip_access_control": {
                    "type": "deny",
                    "ip_group_list": [4, 5, 6],
                },
                "will_error": True,
            },
        ]
        for test in data:
            request = self.factory.put(f"/apis/{self.gateway.id}/access_strategies/{access_strategy.id}/", data=test)

            view = AccessStrategyViewSet.as_view({"put": "update"})
            response = view(request, gateway_id=self.gateway.id, id=access_strategy.id)

            result = get_response_json(response)

            if test.get("will_error"):
                # self.assertNotEqual(result["code"], 0, result)
                self.assertNotEqual(response.status_code, 200, "")
            else:
                # self.assertEqual(result["code"], 0, result)
                self.assertEqual(response.status_code, 200, result)

                strategy = AccessStrategy.objects.get(api=self.gateway, name=test["name"], type=test["type"])

                self.assertEqual(strategy.name, test["name"])
                self.assertEqual(strategy.comment, test["comment"])
                self.assertEqual(strategy.config, test["expected"]["config"])

    def test_retrieve(self):
        data = [
            {
                "instance": G(
                    AccessStrategy,
                    api=self.gateway,
                    type="ip_access_control",
                    _config=json.dumps(
                        {
                            "type": "allow",
                            "ip_group_list": [1, 2, 3],
                        }
                    ),
                    schema=SchemaFactory().get_access_strategy_schema("ip_access_control"),
                ),
                "expected": {
                    "rate_limit": None,
                    "user_verified_unrequired_apps": None,
                    "error_status_code_200": None,
                    "cors": None,
                    "circuit_breaker": None,
                },
            },
            {
                "instance": G(
                    AccessStrategy,
                    api=self.gateway,
                    type="rate_limit",
                    _config=json.dumps(
                        {
                            "rates": {
                                "__default": [
                                    {
                                        "tokens": 100,
                                        "period": 60,
                                    }
                                ]
                            }
                        }
                    ),
                    schema=SchemaFactory().get_access_strategy_schema("rate_limit"),
                ),
                "expected": {
                    "ip_access_control": None,
                    "user_verified_unrequired_apps": None,
                    "error_status_code_200": None,
                    "cors": None,
                    "circuit_breaker": None,
                },
            },
        ]

        for test in data:
            instance = test["instance"]

            request = self.factory.get(f"/apis/{self.gateway.id}/access_strategies/{instance.id}/")

            view = AccessStrategyViewSet.as_view({"get": "retrieve"})
            response = view(request, gateway_id=self.gateway.id, id=instance.id)

            result = get_response_json(response)
            # self.assertEqual(result["code"], 0)
            self.assertEqual(response.status_code, 200)

            test["expected"].update(
                {
                    "id": instance.id,
                    "name": instance.name,
                    "type": instance.type,
                    "comment": instance.comment,
                    instance.type: instance.config,
                }
            )
            self.assertEqual(result["data"], test["expected"])

    def test_destroy(self):
        access_strategy = G(AccessStrategy, api=self.gateway)
        binding = G(AccessStrategyBinding, access_strategy=access_strategy)

        request = self.factory.delete(f"/apis/{self.gateway.id}/access_strategies/{access_strategy.id}/")

        view = AccessStrategyViewSet.as_view({"delete": "destroy"})
        response = view(request, gateway_id=self.gateway.id, id=access_strategy.id)

        # result = get_response_json(response)
        # self.assertEqual(result["code"], 0)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(AccessStrategy.objects.filter(id=access_strategy.id).exists())
        self.assertFalse(AccessStrategyBinding.objects.filter(id=binding.id).exists())
