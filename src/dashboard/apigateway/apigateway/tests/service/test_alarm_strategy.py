#
# TencentBlueKing is pleased to support the open source community by making
# 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
# Copyright (C) 2025 Tencent. All rights reserved.
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
from django.test import TestCase
from django_dynamic_fixture import G

from apigateway.apps.monitor.models import AlarmStrategy
from apigateway.core.models import Gateway
from apigateway.service.alarm_strategy import create_default_alarm_strategy
from apigateway.tests.utils.testing import create_gateway


class TestAlarmStrategy(TestCase):
    @pytest.fixture(autouse=True)
    def setup_fixtures(self):
        self.gateway = create_gateway()

    def test_create_default_alarm_strategy(self):
        gateway = G(Gateway)
        data = [
            {
                "gateway": gateway,
                "created_by": "admin",
            },
        ]
        for test in data:
            create_default_alarm_strategy(
                test["gateway"],
                created_by=test["created_by"],
            )

            strategy_queryset = AlarmStrategy.objects.filter(gateway=gateway)
            self.assertEqual(strategy_queryset.count(), 3)

            strategy = strategy_queryset.first()
            self.assertEqual(strategy.gateway, test["gateway"])
            self.assertEqual(strategy.enabled, True)
            self.assertEqual(strategy.created_by, "admin")
