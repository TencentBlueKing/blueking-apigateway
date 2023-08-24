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
from django.test import TestCase
from django_dynamic_fixture import G

from apigateway.apps.access_strategy.binding.views import AccessStrategyBindingBatchViewSet
from apigateway.apps.access_strategy.models import AccessStrategy, AccessStrategyBinding
from apigateway.core.models import Stage
from apigateway.tests.utils.testing import APIRequestFactory, create_gateway, get_response_json


class TestAccessStrategyBindingBatchViewSet(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.factory = APIRequestFactory()
        cls.gateway = create_gateway()

    def test_bind(self):
        gateway = create_gateway()
        stage_1 = G(Stage, gateway=gateway)
        stage_2 = G(Stage, gateway=gateway)
        stage_3 = G(Stage, gateway=gateway)
        access_strategy_1 = G(AccessStrategy, api=gateway, type="ip_access_control")
        access_strategy_2 = G(AccessStrategy, api=gateway, type="ip_access_control")

        data = [
            # bind stage
            {
                "access_strategy": access_strategy_1,
                "scope_type": "stage",
                "scope_ids": [stage_1.id],
                "type": "ip_access_control",
                "expected": {
                    "access_strategy_1": {
                        "count": 1,
                    },
                    "access_strategy_2": {
                        "count": 0,
                    },
                },
            },
            # bind another stages on the same access_strategy
            {
                "access_strategy": access_strategy_1,
                "scope_type": "stage",
                "scope_ids": [stage_2.id, stage_3.id],
                "type": "ip_access_control",
                "expected": {
                    "access_strategy_1": {
                        "count": 3,
                    },
                    "access_strategy_2": {
                        "count": 0,
                    },
                },
            },
            # bind stage to another access_strategy
            {
                "access_strategy": access_strategy_2,
                "scope_type": "stage",
                "scope_ids": [stage_3.id],
                "type": "ip_access_control",
                "expected": {
                    "access_strategy_1": {
                        "count": 2,
                    },
                    "access_strategy_2": {
                        "count": 1,
                    },
                },
            },
            # bind another stage on the same access_strategy, but delete=True
            {
                "access_strategy": access_strategy_1,
                "scope_type": "stage",
                "scope_ids": [stage_2.id],
                "type": "ip_access_control",
                "delete": True,
                "expected": {
                    "access_strategy_1": {
                        "count": 1,
                    },
                    "access_strategy_2": {
                        "count": 1,
                    },
                },
            },
            # empty stage
            {
                "access_strategy": access_strategy_1,
                "scope_type": "stage",
                "scope_ids": [],
                "type": "ip_access_control",
                "delete": True,
                "expected": {
                    "access_strategy_1": {
                        "count": 0,
                    },
                    "access_strategy_2": {
                        "count": 1,
                    },
                },
            },
        ]

        for test in data:
            access_strategy = test.pop("access_strategy")
            request = self.factory.post(
                f"/apis/{gateway.id}/access_strategies/{access_strategy.id}/bindings/",
                data=test,
            )

            view = AccessStrategyBindingBatchViewSet.as_view({"post": "bind"})
            response = view(request, gateway_id=gateway.id, access_strategy_id=access_strategy.id)

            result = get_response_json(response)
            self.assertEqual(response.status_code, 200, result)

            self.assertEqual(
                AccessStrategyBinding.objects.filter(
                    scope_type=test["scope_type"], type=test["type"], access_strategy=access_strategy_1
                ).count(),
                test["expected"]["access_strategy_1"]["count"],
            )
            self.assertEqual(
                AccessStrategyBinding.objects.filter(
                    scope_type=test["scope_type"], type=test["type"], access_strategy=access_strategy_2
                ).count(),
                test["expected"]["access_strategy_2"]["count"],
            )

    def test_list(self):
        access_strategy = G(AccessStrategy, api=self.gateway, type="ip_access_control")
        stage = G(Stage, gateway=self.gateway)
        G(
            AccessStrategyBinding,
            scope_type="stage",
            scope_id=stage.id,
            type="ip_access_control",
            access_strategy=access_strategy,
        )

        params = {
            "scope_type": "stage",
            "type": "ip_access_control",
        }
        request = self.factory.get(
            f"/apis/{self.gateway.id}/access_strategies/{access_strategy.id}/bindings/", data=params
        )

        view = AccessStrategyBindingBatchViewSet.as_view({"get": "list"})
        response = view(request, gateway_id=self.gateway.id, access_strategy_id=access_strategy.id)

        result = get_response_json(response)
        self.assertEqual(response.status_code, 200)

        self.assertEqual(
            result["data"]["results"],
            [
                {
                    "scope_type": "stage",
                    "type": "ip_access_control",
                    "scope_id": stage.id,
                }
            ],
        )

    def test_unbind(self):
        access_strategy = G(AccessStrategy, api=self.gateway, type="ip_access_control")
        stage = G(Stage, gateway=self.gateway)
        binding = G(
            AccessStrategyBinding,
            scope_type="stage",
            scope_id=stage.id,
            type="ip_access_control",
            access_strategy=access_strategy,
        )

        data = {
            "scope_type": "stage",
            "scope_ids": [stage.id],
            "type": "ip_access_control",
        }

        request = self.factory.delete(
            f"/apis/{self.gateway.id}/access_strategies/{access_strategy.id}/bindings/", data=data
        )

        view = AccessStrategyBindingBatchViewSet.as_view({"delete": "unbind"})
        response = view(request, gateway_id=self.gateway.id, access_strategy_id=access_strategy.id)

        self.assertEqual(response.status_code, 200)

        self.assertFalse(AccessStrategyBinding.objects.filter(id=binding.id).exists())

    def test_diff(self):
        access_strategy_1 = G(AccessStrategy, api=self.gateway, type="ip_access_control")
        access_strategy_2 = G(AccessStrategy, api=self.gateway, type="ip_access_control")

        stage_1 = G(Stage, gateway=self.gateway)
        stage_2 = G(Stage, gateway=self.gateway)
        stage_3 = G(Stage, gateway=self.gateway)

        G(
            AccessStrategyBinding,
            scope_type="stage",
            scope_id=stage_1.id,
            type="ip_access_control",
            access_strategy=access_strategy_1,
        )
        G(
            AccessStrategyBinding,
            scope_type="stage",
            scope_id=stage_2.id,
            type="ip_access_control",
            access_strategy=access_strategy_2,
        )

        data = [
            # 全解绑
            {
                "params": {
                    "scope_type": "stage",
                    "type": "ip_access_control",
                    "scope_ids": [],
                },
                "expected": {
                    "unbind": [
                        {
                            "scope_type": "stage",
                            "scope_id": stage_1.id,
                            "type": "ip_access_control",
                            "access_strategy_id": access_strategy_1.id,
                            "access_strategy_name": access_strategy_1.name,
                        },
                    ],
                    "normal_bind": [],
                    "overwrite_bind": [],
                },
            },
            # 仅新增
            {
                "params": {
                    "scope_type": "stage",
                    "type": "ip_access_control",
                    "scope_ids": [stage_1.id, stage_3.id],
                },
                "expected": {
                    "unbind": [],
                    "normal_bind": [
                        {
                            "scope_type": "stage",
                            "scope_id": stage_3.id,
                            "type": "ip_access_control",
                            "access_strategy_id": 0,
                            "access_strategy_name": "",
                        },
                    ],
                    "overwrite_bind": [],
                },
            },
            # 仅覆盖
            {
                "params": {
                    "scope_type": "stage",
                    "type": "ip_access_control",
                    "scope_ids": [stage_1.id, stage_2.id],
                },
                "expected": {
                    "unbind": [],
                    "normal_bind": [],
                    "overwrite_bind": [
                        {
                            "scope_type": "stage",
                            "scope_id": stage_2.id,
                            "type": "ip_access_control",
                            "access_strategy_id": access_strategy_2.id,
                            "access_strategy_name": access_strategy_2.name,
                        },
                    ],
                },
            },
            # 覆盖，删除，新增
            {
                "params": {
                    "scope_type": "stage",
                    "type": "ip_access_control",
                    "scope_ids": [stage_2.id, stage_3.id],
                },
                "expected": {
                    "unbind": [
                        {
                            "scope_type": "stage",
                            "scope_id": stage_1.id,
                            "type": "ip_access_control",
                            "access_strategy_id": access_strategy_1.id,
                            "access_strategy_name": access_strategy_1.name,
                        },
                    ],
                    "normal_bind": [
                        {
                            "scope_type": "stage",
                            "scope_id": stage_3.id,
                            "type": "ip_access_control",
                            "access_strategy_id": 0,
                            "access_strategy_name": "",
                        },
                    ],
                    "overwrite_bind": [
                        {
                            "scope_type": "stage",
                            "scope_id": stage_2.id,
                            "type": "ip_access_control",
                            "access_strategy_id": access_strategy_2.id,
                            "access_strategy_name": access_strategy_2.name,
                        },
                    ],
                },
            },
            # 不变
            {
                "params": {
                    "scope_type": "stage",
                    "type": "ip_access_control",
                    "scope_ids": [stage_1.id],
                },
                "expected": {
                    "unbind": [],
                    "normal_bind": [],
                    "overwrite_bind": [],
                },
            },
        ]

        for test in data:
            request = self.factory.post(
                f"/apis/{self.gateway.id}/access_strategies/{access_strategy_1.id}/bindings/diff/",
                data=test["params"],
            )

            view = AccessStrategyBindingBatchViewSet.as_view({"post": "diff"})
            response = view(request, gateway_id=self.gateway.id, access_strategy_id=access_strategy_1.id)

            result = get_response_json(response)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(result["data"], test["expected"])
