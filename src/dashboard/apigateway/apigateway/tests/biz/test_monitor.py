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

import pytest
from django_dynamic_fixture import G

from apigateway.apps.monitor.models import AlarmRecord, AlarmStrategy
from apigateway.biz.monitor import ResourceMonitorHandler
from apigateway.tests.utils.testing import create_gateway, dummy_time


class TestResourceMonitorHandler:
    @pytest.fixture(autouse=True)
    def setup_fixtures(self):
        self.gateway = create_gateway()

    def test_statistics_api_alarm_record(self):
        strategy_1 = G(AlarmStrategy, gateway=self.gateway)
        strategy_2 = G(AlarmStrategy, gateway=self.gateway)

        alarm_record_1 = G(AlarmRecord, created_time=dummy_time.time)
        alarm_record_1.alarm_strategies.set([strategy_1])

        alarm_record_2 = G(AlarmRecord, created_time=dummy_time.time)
        alarm_record_2.alarm_strategies.set([strategy_1])

        alarm_record_3 = G(AlarmRecord, created_time=dummy_time.time + datetime.timedelta(seconds=-300))
        alarm_record_3.alarm_strategies.set([strategy_2])

        data = [
            {
                "params": {
                    "user_name": "admin",
                    "name": self.gateway.name,
                    "time_start": dummy_time.time,
                    "time_end": dummy_time.time + datetime.timedelta(seconds=10),
                },
                "expected": [
                    {
                        "api_id": self.gateway.id,
                        "api_name": self.gateway.name,
                        "alarm_record_count": 2,
                        "strategy_summary": [
                            {
                                "id": strategy_1.id,
                                "name": strategy_1.name,
                                "alarm_record_count": 2,
                                "latest_alarm_record": {
                                    "id": alarm_record_2.id,
                                    "message": alarm_record_2.message,
                                    "created_time": dummy_time.str,
                                },
                            },
                        ],
                    }
                ],
            },
        ]

        for test in data:
            result = ResourceMonitorHandler.statistics_api_alarm_record(
                username=test["params"].get("user_name"),
                name=test["params"].get("name"),
                time_start=test["params"].get("time_start"),
                time_end=test["params"].get("time_end"),
            )
            assert result == test["expected"]
