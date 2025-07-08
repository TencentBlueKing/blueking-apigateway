# -*- coding: utf-8 -*-
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
import datetime

from django.test import TestCase
from django_dynamic_fixture import G

from apigateway.apps.monitor.models import AlarmRecord, AlarmStrategy
from apigateway.core.models import Gateway
from apigateway.tests.utils.testing import dummy_time


class TestAlarmStrategyManager(TestCase):
    def test_annotate_alarm_record_by_strategy(self):
        gateway = G(Gateway)

        strategy_1 = G(AlarmStrategy, gateway=gateway)
        strategy_2 = G(AlarmStrategy, gateway=gateway)

        record_1 = G(AlarmRecord, created_time=dummy_time.time)
        record_1.alarm_strategies.set([strategy_1])

        record_2 = G(AlarmRecord, created_time=dummy_time.time)
        record_2.alarm_strategies.set([strategy_1, strategy_2])

        data = [
            {
                "gateway_ids": [gateway.id],
                "expected": [
                    {
                        "id": strategy_1.id,
                        "alarm_record_count": 2,
                    },
                    {
                        "id": strategy_2.id,
                        "alarm_record_count": 1,
                    },
                ],
            },
            {
                "gateway_ids": [gateway.id],
                "time_start": dummy_time.time + datetime.timedelta(seconds=10),
                "time_end": dummy_time.time + datetime.timedelta(seconds=20),
                "expected": [],
            },
        ]
        for test in data:
            result = AlarmStrategy.objects.annotate_alarm_record_by_strategy(
                gateway_ids=test["gateway_ids"],
                time_start=test.get("time_start"),
                time_end=test.get("time_end"),
            )
            result = sorted(
                [
                    {
                        "id": strategy.id,
                        "alarm_record_count": strategy.alarm_record_count,
                    }
                    for strategy in result
                ],
                key=lambda x: x["id"],
            )
            self.assertEqual(result, test["expected"])

    def test_annotate_alarm_record_by_api(self):
        gateway = G(Gateway)

        strategy_1 = G(AlarmStrategy, gateway=gateway)
        strategy_2 = G(AlarmStrategy, gateway=gateway)

        record_1 = G(AlarmRecord, created_time=dummy_time.time)
        record_1.alarm_strategies.set([strategy_1])

        record_2 = G(AlarmRecord, created_time=dummy_time.time)
        record_2.alarm_strategies.set([strategy_1, strategy_2])

        data = [
            {
                "gateway_ids": [gateway.id],
                "expected": {
                    gateway.id: 2,
                },
            },
            {
                "gateway_ids": [gateway.id],
                "time_start": dummy_time.time + datetime.timedelta(seconds=10),
                "time_end": dummy_time.time + datetime.timedelta(seconds=20),
                "expected": {
                    gateway.id: 0,
                },
            },
        ]
        for test in data:
            result = AlarmStrategy.objects.annotate_alarm_record_by_gateway(
                gateway_ids=test["gateway_ids"],
                time_start=test.get("time_start"),
                time_end=test.get("time_end"),
            )
            self.assertEqual(result, test["expected"])
