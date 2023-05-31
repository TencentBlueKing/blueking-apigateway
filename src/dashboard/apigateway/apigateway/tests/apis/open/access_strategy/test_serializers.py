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

from apigateway.apis.open.access_strategy import serializers
from apigateway.apps.access_strategy.models import AccessStrategy, IPGroup
from apigateway.core.models import Gateway
from apigateway.tests.utils.testing import create_request


class TestIPGroupV1SLZ(TestCase):
    def test_validate(self):
        data = [
            {
                "params": {
                    "name": "test",
                    "ips": "1.0.0.1",
                    "comment": "test",
                    "action": "set",
                },
                "will_error": False,
            },
            {
                "params": {
                    "name": "test",
                    "ips": "1.0.0.1",
                    "comment": "test",
                    "action": "append",
                },
                "will_error": False,
            },
            {
                "params": {
                    "name": "test",
                    "ips": "1.0.0.1",
                    "comment": "test",
                    "action": "test",
                },
                "will_error": True,
            },
        ]

        for test in data:
            slz = serializers.IPGroupV1SLZ(data=test["params"])
            slz.is_valid()
            if test.get("will_error"):
                self.assertTrue(slz.errors)
            else:
                self.assertEqual(slz.validated_data, test["params"])

    def test_get_valid_ips(self):
        data = [
            {
                "ips": "",
                "expected": "",
            },
            {
                "ips": "1.0.0.1",
                "expected": "1.0.0.1",
            },
            {
                "ips": "1.0.0.1\n\n1.0.0.2",
                "expected": "1.0.0.1\n1.0.0.2",
            },
            {
                "ips": "1.0.0.1\n\n1.0.0.2\n# 1.0.0.3\n",
                "expected": "1.0.0.1\n1.0.0.2",
            },
            {
                "ips": "a.1.0.1",
                "will_error": True,
            },
        ]

        for test in data:
            slz = serializers.IPGroupV1SLZ(
                data={
                    "name": "test",
                    "ips": test["ips"],
                    "action": "append",
                }
            )
            slz.is_valid()
            if test.get("will_error"):
                self.assertTrue(slz.errors)
            else:
                self.assertEqual(slz.validated_data["ips"], test["expected"])


class TestAccessStrategyAddIPGroupsV1SLZ(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.gateway = G(Gateway)
        cls.request = create_request()
        cls.request.gateway = cls.gateway

    def test_validate(self):
        strategy = G(AccessStrategy, api=self.gateway, type="ip_access_control")
        strategy_2 = G(AccessStrategy, api=self.gateway, type="rate_limit")
        ip_group = G(IPGroup, api=self.gateway)

        data = [
            # access-strategy/ip-group-list is ok
            {
                "access_strategy_ids": [strategy.id],
                "ip_group_list": [ip_group.id],
                "will_error": False,
            },
            # access-strategy is invalid
            {
                "access_strategy_ids": [strategy_2.id],
                "ip_group_list": [ip_group.id],
                "will_error": True,
            },
            # ip-group is invalid
            {
                "access_strategy_ids": [strategy.id],
                "ip_group_list": [0],
                "will_error": True,
            },
        ]
        for test in data:
            slz = serializers.AccessStrategyAddIPGroupsV1SLZ(
                data=test,
                context={
                    "request": self.request,
                },
            )
            slz.is_valid()
            if test.get("will_error"):
                self.assertTrue(slz.errors)
            else:
                self.assertEqual(slz.validated_data["access_strategy_ids"], test["access_strategy_ids"])
