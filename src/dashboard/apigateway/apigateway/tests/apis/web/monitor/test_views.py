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
import json

from django.test import TestCase
from django_dynamic_fixture import G
from rest_framework.fields import DateTimeField

from apigateway.apis.web.monitor.views import (
    AlarmRecordListApi,
    AlarmRecordRetrieveApi,
    AlarmRecordSummaryListApi,
    AlarmStrategyListCreateApi,
    AlarmStrategyRetrieveUpdateDestroyApi,
    AlarmStrategyUpdateStatusApi,
)
from apigateway.apps.label.models import APILabel
from apigateway.apps.monitor.models import AlarmRecord, AlarmStrategy
from apigateway.common.factories import SchemaFactory
from apigateway.tests.utils.testing import APIRequestFactory, create_gateway, dummy_time, get_response_json


class TestAlarmStrategyListCreateApi(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.factory = APIRequestFactory()
        cls.gateway = create_gateway()
        cls.label = G(APILabel, api=cls.gateway)

    def test_create(self):
        data = [
            {
                "name": "test",
                "alarm_type": "resource_backend",
                "alarm_subtype": "status_code_5xx",
                "api_label_ids": [self.label.id],
                "config": {
                    "detect_config": {
                        "duration": 60,
                        "method": "gte",
                        "count": 10,
                    },
                    "converge_config": {
                        "duration": 60,
                    },
                    "notice_config": {
                        "notice_way": ["wechat", "im"],
                        "notice_role": ["maintainer"],
                        "notice_extra_receiver": ["admin"],
                    },
                },
            },
        ]
        for test in data:
            request = self.factory.post(f"/apis/{self.gateway.id}/monitors/alarm/strategies/", data=test)

            view = AlarmStrategyListCreateApi.as_view()
            response = view(request, gateway_id=self.gateway.id)

            result = get_response_json(response)
            # self.assertEqual(result["code"], 0, result)
            self.assertEqual(response.status_code, 201, result)

            strategy = AlarmStrategy.objects.get(api=self.gateway, name="test")
            self.assertEqual(strategy.api_labels.count(), len(test["api_label_ids"]))

    def test_list(self):
        api_label = G(APILabel, api=self.gateway, name="test")

        strategy_1 = G(AlarmStrategy, api=self.gateway, name="list-01", updated_time=dummy_time.time)
        strategy_1.api_labels.add(api_label)

        strategy_2 = G(AlarmStrategy, api=self.gateway, name="list-02", updated_time=dummy_time.time)

        data = [
            {
                "params": {},
                "expected": [
                    {
                        "id": strategy_2.id,
                        "name": strategy_2.name,
                        "alarm_type": strategy_2.alarm_type,
                        "alarm_subtype": strategy_2.alarm_subtype,
                        "enabled": strategy_2.enabled,
                        "updated_time": dummy_time.str,
                        "api_label_names": [],
                    },
                    {
                        "id": strategy_1.id,
                        "name": strategy_1.name,
                        "alarm_type": strategy_1.alarm_type,
                        "alarm_subtype": strategy_1.alarm_subtype,
                        "enabled": strategy_1.enabled,
                        "updated_time": dummy_time.str,
                        "api_label_names": [api_label.name],
                    },
                ],
            },
            {
                "params": {
                    "query": "list-02",
                },
                "expected": [
                    {
                        "id": strategy_2.id,
                        "name": strategy_2.name,
                        "alarm_type": strategy_2.alarm_type,
                        "alarm_subtype": strategy_2.alarm_subtype,
                        "enabled": strategy_2.enabled,
                        "updated_time": dummy_time.str,
                        "api_label_names": [],
                    },
                ],
            },
            {
                "params": {
                    "api_label_id": api_label.id,
                },
                "expected": [
                    {
                        "id": strategy_1.id,
                        "name": strategy_1.name,
                        "alarm_type": strategy_1.alarm_type,
                        "alarm_subtype": strategy_1.alarm_subtype,
                        "enabled": strategy_1.enabled,
                        "updated_time": dummy_time.str,
                        "api_label_names": [api_label.name],
                    },
                ],
            },
        ]

        for test in data:
            request = self.factory.get(f"/apis/{self.gateway.id}/monitors/alarm/strategies/", data=test["params"])

            view = AlarmStrategyListCreateApi.as_view()
            response = view(request, gateway_id=self.gateway.id)

            result = get_response_json(response)
            # self.assertEqual(result["code"], 0)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(result["data"]["results"], test["expected"])


class TestAlarmStrategyRetrieveUpdateDestroyApi(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.factory = APIRequestFactory()
        cls.gateway = create_gateway()
        cls.label = G(APILabel, api=cls.gateway)

    def test_retrieve(self):
        alarm_strategy = G(
            AlarmStrategy,
            api=self.gateway,
            name="test",
            alarm_type="resource_backend",
            _api_label_ids=f"{self.label.id}",
            _config=json.dumps(
                {
                    "detect_config": {
                        "duration": 60,
                        "method": "gte",
                        "count": 10,
                    },
                    "converge_config": {
                        "duration": 60,
                    },
                    "notice_config": {
                        "notice_way": ["wechat", "im"],
                        "notice_role": ["creator", "maintainer"],
                        "notice_extra_receiver": ["admin"],
                    },
                }
            ),
        )

        request = self.factory.get(f"/apis/{self.gateway.id}/monitors/alarm/strategies/{alarm_strategy.id}/")

        view = AlarmStrategyRetrieveUpdateDestroyApi.as_view()
        response = view(request, gateway_id=self.gateway.id, id=alarm_strategy.id)

        result = get_response_json(response)
        # self.assertEqual(result["code"], 0, result)
        self.assertEqual(response.status_code, 200, result)

    def test_update(self):
        alarm_strategy = G(
            AlarmStrategy,
            api=self.gateway,
            schema=SchemaFactory().get_monitor_alarm_strategy_schema(),
        )
        data = [
            {
                "name": "test",
                "alarm_type": "resource_backend",
                "alarm_subtype": "status_code_5xx",
                "api_label_ids": [self.label.id],
                "config": {
                    "detect_config": {
                        "duration": 60,
                        "method": "gte",
                        "count": 10,
                    },
                    "converge_config": {
                        "duration": 60,
                    },
                    "notice_config": {
                        "notice_way": ["wechat", "im"],
                        "notice_role": ["maintainer"],
                        "notice_extra_receiver": ["admin"],
                    },
                },
            },
        ]
        for test in data:
            request = self.factory.put(
                f"/apis/{self.gateway.id}/monitors/alarm/strategies/{alarm_strategy.id}/", data=test
            )

            view = AlarmStrategyRetrieveUpdateDestroyApi.as_view()
            response = view(request, gateway_id=self.gateway.id, id=alarm_strategy.id)

            result = get_response_json(response)
            self.assertEqual(response.status_code, 204, result)

    def test_destroy(self):
        alarm_strategy = G(AlarmStrategy, api=self.gateway)

        request = self.factory.delete(f"/apis/{self.gateway.id}/monitors/alarm/strategies/{alarm_strategy.id}/")

        view = AlarmStrategyRetrieveUpdateDestroyApi.as_view()
        response = view(request, gateway_id=self.gateway.id, id=alarm_strategy.id)

        self.assertEqual(response.status_code, 204)


class TestAlarmStrategyUpdateStatusApi(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.factory = APIRequestFactory()
        cls.gateway = create_gateway()
        cls.label = G(APILabel, api=cls.gateway)

    def test_update_status(self):
        alarm_strategy = G(
            AlarmStrategy,
            api=self.gateway,
            name="test",
            alarm_type="resource_backend",
            _api_label_ids=f"{self.label.id}",
            _config=json.dumps(
                {
                    "detect_config": {
                        "duration": 60,
                        "method": "gte",
                        "count": 10,
                    },
                    "converge_config": {
                        "duration": 60,
                    },
                    "notice_config": {
                        "notice_way": ["wechat", "im"],
                        "notice_role": ["creator", "maintainer"],
                        "notice_extra_receiver": ["admin"],
                    },
                }
            ),
            schema=SchemaFactory().get_monitor_alarm_strategy_schema(),
        )

        data = {
            "enabled": False,
        }

        request = self.factory.put(
            f"/apis/{self.gateway.id}/monitors/alarm/strategies/{alarm_strategy.id}/update_status/",
            data=data,
        )

        view = AlarmStrategyUpdateStatusApi.as_view()
        response = view(request, gateway_id=self.gateway.id, id=alarm_strategy.id)

        result = get_response_json(response)
        self.assertEqual(response.status_code, 204, result)


class TestAlarmRecordListApi(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.factory = APIRequestFactory()
        cls.gateway = create_gateway()

    def test_list(self):
        strategy_1 = G(AlarmStrategy, api=self.gateway)
        strategy_2 = G(AlarmStrategy, api=self.gateway)

        record = G(AlarmRecord, api=self.gateway, status="received")
        record.alarm_strategies.set([strategy_1])

        record = G(AlarmRecord, api=self.gateway, status="received")
        record.alarm_strategies.set([strategy_1])

        record = G(AlarmRecord, api=self.gateway, status="skipped")
        record.alarm_strategies.set([strategy_2])

        data = [
            {
                "expected": {
                    "count": 3,
                },
            },
            {
                "alarm_strategy_id": strategy_1.id,
                "expected": {
                    "count": 2,
                },
            },
            {
                "status": "skipped",
                "expected": {
                    "count": 1,
                },
            },
        ]

        for test in data:
            request = self.factory.get(f"/apis/{self.gateway.id}/monitors/alarm/records/", data=test)

            view = AlarmRecordListApi.as_view()
            response = view(request, gateway_id=self.gateway.id)

            result = get_response_json(response)
            # self.assertEqual(result["code"], 0)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(len(result["data"]["results"]), test["expected"]["count"])


class TestAlarmRecordRetrieveApi(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.factory = APIRequestFactory()
        cls.gateway = create_gateway()

    def test_retrieve(self):
        strategy = G(AlarmStrategy, api=self.gateway)
        alarm_record = G(AlarmRecord, api=self.gateway)
        alarm_record.alarm_strategies.set([strategy])

        request = self.factory.get(f"/apis/{self.gateway.id}/monitors/alarm/records/{alarm_record.id}/")

        view = AlarmRecordRetrieveApi.as_view()
        response = view(request, gateway_id=self.gateway.id, id=alarm_record.id)

        result = get_response_json(response)
        # self.assertEqual(result["code"], 0, result)
        self.assertEqual(response.status_code, 200, result)


class TestAlarmRecordSummaryListApi(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.factory = APIRequestFactory()
        cls.gateway = create_gateway()

    def test_get(self):
        strategy_1 = G(AlarmStrategy, api=self.gateway)
        strategy_2 = G(AlarmStrategy, api=self.gateway)

        alarm_record_1 = G(AlarmRecord, created_time=dummy_time.time)
        alarm_record_1.alarm_strategies.set([strategy_1])

        alarm_record_2 = G(AlarmRecord, created_time=dummy_time.time)
        alarm_record_2.alarm_strategies.set([strategy_1])

        alarm_record_3 = G(AlarmRecord, created_time=dummy_time.time + datetime.timedelta(seconds=-300))
        alarm_record_3.alarm_strategies.set([strategy_2])

        data = [
            {
                "params": {},
                "expected": [
                    {
                        "api_id": self.gateway.id,
                        "api_name": self.gateway.name,
                        "alarm_record_count": 3,
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
                            {
                                "id": strategy_2.id,
                                "name": strategy_2.name,
                                "alarm_record_count": 1,
                                "latest_alarm_record": {
                                    "id": alarm_record_3.id,
                                    "message": alarm_record_3.message,
                                    "created_time": DateTimeField().to_representation(alarm_record_3.created_time),
                                },
                            },
                        ],
                    }
                ],
            },
            {
                "params": {
                    "time_start": dummy_time.timestamp,
                    "time_end": dummy_time.timestamp + 10,
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
            request = self.factory.get("/apis/monitors/alarm/records/summary/", data=test["params"])

            view = AlarmRecordSummaryListApi.as_view()
            response = view(request)

            result = get_response_json(response)
            # self.assertEqual(result["code"], 0, result)
            self.assertEqual(response.status_code, 200, result)
            self.assertEqual(result["data"], test["expected"])
