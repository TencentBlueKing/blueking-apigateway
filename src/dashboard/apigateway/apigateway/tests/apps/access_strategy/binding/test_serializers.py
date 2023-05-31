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

from apigateway.apps.access_strategy.binding import serializers
from apigateway.apps.access_strategy.models import AccessStrategy
from apigateway.core.models import Gateway


class TestAccessStrategyBindingBatchSLZ(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.gateway = G(Gateway)
        cls.access_strategy = G(AccessStrategy, api=cls.gateway, type="ip_access_control")

    def test_to_internal_value(self):
        data = [
            {
                "scope_type": "stage",
                "scope_ids": [1, 2, 3],
                "type": "ip_access_control",
                "expected": {
                    "scope_type": "stage",
                    "scope_ids": [1, 2, 3],
                    "type": "ip_access_control",
                    "access_strategy": self.access_strategy,
                },
                "will_error": False,
            },
            {
                "scope_type": "stage",
                "scope_ids": [1, 2, 3],
                "type": "rate_limit",
                "will_error": True,
            },
        ]
        for test in data:
            slz = serializers.AccessStrategyBindingBatchSLZ(
                data=test,
                context={"access_strategy": self.access_strategy},
            )
            slz.is_valid()
            if test.get("will_error"):
                self.assertTrue(slz.errors)
            else:
                self.assertEqual(slz.validated_data, test["expected"])
