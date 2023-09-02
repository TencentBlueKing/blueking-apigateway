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
import datetime

from django.test import TestCase
from django_dynamic_fixture import G

from apigateway.apps.label.models import APILabel, ResourceLabel
from apigateway.apps.monitor.models import AlarmRecord, AlarmStrategy
from apigateway.core.models import Gateway, Resource
from apigateway.tests.utils.testing import dummy_time


class TestAlarmStrategyManager(TestCase):
    def test_create_default_strategy(self):
        gateway = G(Gateway)
        data = [
            {
                "gateway": gateway,
                "created_by": "admin",
            },
        ]
        for test in data:
            AlarmStrategy.objects.create_default_strategy(
                test["gateway"],
                created_by=test["created_by"],
            )

            strategy_queryset = AlarmStrategy.objects.filter(gateway=gateway)
            self.assertEqual(strategy_queryset.count(), 3)

            strategy = strategy_queryset.first()
            self.assertEqual(strategy.gateway, test["gateway"])
            self.assertEqual(strategy.enabled, True)
            self.assertEqual(strategy.created_by, "admin")

    def test_get_resource_alarm_strategy(self):
        gateway_1 = G(Gateway)
        gateway_2 = G(Gateway)
        resource_1 = G(Resource, gateway=gateway_2)
        resource_2 = G(Resource, gateway=gateway_2)

        api_label = G(APILabel, gateway=gateway_2)
        G(ResourceLabel, resource=resource_1, api_label=api_label)

        alarm_strategy = G(
            AlarmStrategy,
            gateway=gateway_2,
            enabled=True,
            alarm_subtype="status_code_5xx",
        )
        alarm_strategy.api_labels.set([api_label.id])

        alarm_strategy_2 = G(
            AlarmStrategy,
            gateway=gateway_2,
            enabled=True,
            alarm_subtype="status_code_5xx",
        )

        data = [
            # gateway alarm-strategy not exist
            {
                "gateway_id": gateway_1.id,
                "resource_id": 1,
                "expected": [],
            },
            {
                "gateway_id": gateway_2.id,
                "resource_id": resource_1.id,
                "expected": [alarm_strategy, alarm_strategy_2],
            },
            {
                "gateway_id": gateway_2.id,
                "resource_id": resource_2.id,
                "expected": [alarm_strategy_2],
            },
        ]
        for test in data:
            result = AlarmStrategy.objects.get_resource_alarm_strategy(
                test["gateway_id"],
                test["resource_id"],
                "status_code_5xx",
            )
            self.assertEqual(result, test["expected"])

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
