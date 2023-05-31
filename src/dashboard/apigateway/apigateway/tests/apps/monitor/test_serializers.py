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

from apigateway.apps.label.models import APILabel
from apigateway.apps.monitor import serializers
from apigateway.apps.monitor.models import AlarmRecord, AlarmStrategy
from apigateway.core.models import Gateway
from apigateway.tests.utils.testing import create_request, dummy_time


class TestDetectConfigSLZ(TestCase):
    def test_to_internal_value(self):
        data = [
            # ok
            {
                "duration": 60,
                "method": "gte",
                "count": 0,
            },
            # error, method invalid
            {
                "duration": 60,
                "method": "test",
                "count": 0,
                "will_error": True,
            },
        ]
        for test in data:
            slz = serializers.DetectConfigSLZ(data=test)
            slz.is_valid()
            if test.pop("will_error", False):
                self.assertTrue(slz.errors)
            else:
                self.assertEqual(slz.validated_data, test)


class TestNoticeConfigSLZ(TestCase):
    def test_to_internal_value(self):
        data = [
            # ok
            {
                "notice_way": ["wechat"],
                "notice_role": ["maintainer"],
                "notice_extra_receiver": [],
            },
            # ok
            {
                "notice_way": ["wechat"],
                "notice_role": [],
                "notice_extra_receiver": ["admin"],
            },
            # error, notice_way invalid
            {
                "notice_way": ["test"],
                "notice_role": [],
                "notice_extra_receiver": ["admin"],
                "will_error": True,
            },
            # error, notice_role, notice_extra_receiver are empty
            {
                "notice_way": ["wechat"],
                "notice_role": [],
                "notice_extra_receiver": [],
                "will_error": True,
            },
        ]
        for test in data:
            slz = serializers.NoticeConfigSLZ(data=test)
            slz.is_valid()
            if test.pop("will_error", False):
                self.assertTrue(slz.errors)
            else:
                self.assertEqual(slz.validated_data, test)


class TestAlarmStrategySLZ(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.gateway = G(Gateway)
        cls.request = create_request
        cls.request.gateway = cls.gateway

    def test_to_internal_value(self):
        label_1 = G(APILabel, api=self.gateway)
        label_2 = G(APILabel, api=self.gateway)

        data = [
            {
                "id": 1,
                "name": "test",
                "alarm_type": "resource_backend",
                "alarm_subtype": "status_code_5xx",
                "api_label_ids": [label_1.id, label_2.id],
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
                "expected": {
                    "api": self.gateway,
                    "name": "test",
                    "alarm_type": "resource_backend",
                    "alarm_subtype": "status_code_5xx",
                    "api_label_ids": [label_1.id, label_2.id],
                    "config": json.dumps(
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
                                "notice_role": ["maintainer"],
                                "notice_extra_receiver": ["admin"],
                            },
                        }
                    ),
                },
            }
        ]
        for test in data:
            slz = serializers.AlarmStrategySLZ(data=test, context={"request": self.request})
            slz.is_valid()
            self.assertEqual(slz.validated_data, test["expected"])

    def test_to_representation(self):
        label_1 = G(APILabel, api=self.gateway)
        label_2 = G(APILabel, api=self.gateway)

        data = [
            {
                "instance": G(
                    AlarmStrategy,
                    api=self.gateway,
                    name="test",
                    alarm_type="resource_backend",
                    alarm_subtype="status_code_5xx",
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
                ),
                "api_label_ids": [label_1.id, label_2.id],
                "expected": {
                    "id": None,
                    "name": "test",
                    "alarm_type": "resource_backend",
                    "alarm_subtype": "status_code_5xx",
                    "api_label_ids": sorted([label_1.id, label_2.id]),
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
                            "notice_role": ["creator", "maintainer"],
                            "notice_extra_receiver": ["admin"],
                        },
                    },
                },
            }
        ]
        for test in data:
            test["instance"].api_labels.set(test["api_label_ids"])
            test["expected"]["id"] = test["instance"].id

            slz = serializers.AlarmStrategySLZ(instance=test["instance"])
            slz_data = slz.data

            slz_data["api_label_ids"] = sorted(slz_data["api_label_ids"])
            self.assertEqual(slz_data, test["expected"], dict(slz_data))


class TestAlarmRecordSLZ(TestCase):
    def test_to_representation(self):
        gateway = G(Gateway)
        alarm_strategy = G(AlarmStrategy, api=gateway, name="test")
        alarm_record = G(AlarmRecord, created_time=dummy_time.time)
        alarm_record.alarm_strategies.set([alarm_strategy])

        slz = serializers.AlarmRecordSLZ(instance=alarm_record)

        self.assertEqual(
            slz.data,
            {
                "id": alarm_record.id,
                "alarm_id": alarm_record.alarm_id,
                "status": alarm_record.status,
                "message": alarm_record.message,
                "created_time": dummy_time.str,
                "alarm_strategy_names": ["test"],
            },
        )
