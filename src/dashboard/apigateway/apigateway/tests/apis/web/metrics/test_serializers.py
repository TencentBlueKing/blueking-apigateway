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
import time

from django.test import TestCase

from apigateway.apis.web.metrics import serializers


class TestMetricsQueryRangeSLZ(TestCase):
    def test_validate(self):
        data = [
            {
                "data": {
                    "stage_id": 1,
                    "resource_id": 1,
                    "metrics": "requests",
                    "time_start": 1,
                    "time_end": 2,
                    "time_range": 1,
                },
                "expected": {
                    "stage_id": 1,
                    "resource_id": 1,
                    "metrics": "requests",
                    "time_start": 1,
                    "time_end": 2,
                    "time_range": 1,
                },
            },
        ]
        for test in data:
            slz = serializers.MetricsQueryRangeInputSLZ(data=test["data"])
            slz.is_valid()
            self.assertEqual(slz.validated_data, test["expected"])


class TestMetricsQueryInstantSLZ(TestCase):
    def test_validate(self):
        data = [
            {
                "data": {
                    "stage_id": 1,
                    "resource_id": 1,
                    "metrics": "requests_total",
                    "time_start": 1,
                    "time_end": 2,
                    "time_range": 1,
                },
                "expected": {
                    "stage_id": 1,
                    "resource_id": 1,
                    "metrics": "requests_total",
                    "time_start": 1,
                    "time_end": 2,
                    "time_range": 1,
                },
            },
        ]
        for test in data:
            slz = serializers.MetricsQueryInstantInputSLZ(data=test["data"])
            slz.is_valid()
            self.assertEqual(slz.validated_data, test["expected"])


class TestMetricsQueryRequestInputSLZ(TestCase):
    def test_validate(self):
        data = [
            {
                "data": {
                    "stage_id": 1,
                    "resource_id": 1,
                    "metrics": "requests_total",
                    "time_dimension": "day",
                    "bk_app_code": "",
                    "time_start": int(time.time()),
                    "time_end": int(time.time()),
                },
                "expected": {
                    "stage_id": 1,
                    "resource_id": 1,
                    "metrics": "requests_total",
                    "time_dimension": "day",
                    "bk_app_code": "",
                    "time_start": int(time.time()),
                    "time_end": int(time.time()),
                },
            },
            {
                "data": {
                    "stage_id": 1,
                    "resource_id": 1,
                    "metrics": "requests_total",
                    "time_dimension": "day",
                    "bk_app_code": "app01",
                    "time_start": int(time.time()),
                    "time_end": int(time.time()),
                },
                "expected": {
                    "stage_id": 1,
                    "resource_id": 1,
                    "metrics": "requests_total",
                    "time_dimension": "day",
                    "bk_app_code": "app01",
                    "time_start": int(time.time()),
                    "time_end": int(time.time()),
                },
            },
        ]
        for test in data:
            slz = serializers.MetricsQueryRequestInputSLZ(data=test["data"])
            slz.is_valid(raise_exception=True)
            self.assertEqual(slz.validated_data, test["expected"])
