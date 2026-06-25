# -*- coding: utf-8 -*-
#
# TencentBlueKing is pleased to support the open source community by making
# 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
# Copyright (C) Tencent. All rights reserved.
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


class TestMetricsQuerySummaryInputSLZ(TestCase):
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
            slz = serializers.MetricsQuerySummaryInputSLZ(data=test["data"])
            slz.is_valid(raise_exception=True)
            self.assertEqual(slz.validated_data, test["expected"])


class TestMetricsQuerySummaryCallerListInputSLZ(TestCase):
    def test_validate(self):
        data = [
            {
                "data": {
                    "stage_id": 1,
                    "time_start": int(time.time()),
                    "time_end": int(time.time()),
                },
                "expected": {
                    "stage_id": 1,
                    "time_start": int(time.time()),
                    "time_end": int(time.time()),
                },
            }
        ]
        for test in data:
            slz = serializers.MetricsQuerySummaryCallerListInputSLZ(data=test["data"])
            slz.is_valid(raise_exception=True)
            self.assertEqual(slz.validated_data, test["expected"])


class TestMetricsQuerySummaryResourceAppExportInputSLZ(TestCase):
    def test_validate(self):
        timestamp = int(time.time())
        data = {
            "stage_id": 1,
            "resource_id": 1,
            "bk_app_code": "app01",
            "time_start": timestamp,
            "time_end": timestamp,
        }

        slz = serializers.MetricsQuerySummaryResourceAppExportInputSLZ(data=data)
        slz.is_valid(raise_exception=True)

        self.assertEqual(
            slz.validated_data,
            {
                "stage_id": 1,
                "resource_id": 1,
                "bk_app_code": "app01",
                "time_start": timestamp,
                "time_end": timestamp,
            },
        )

    def test_validate_missing_time_range(self):
        slz = serializers.MetricsQuerySummaryResourceAppExportInputSLZ(data={"stage_id": 1})

        self.assertFalse(slz.is_valid())
        self.assertEqual(str(slz.errors["non_field_errors"][0]), "缺少 time_start 或 time_end 参数。")

    def test_validate_without_stage_id(self):
        timestamp = int(time.time())
        slz = serializers.MetricsQuerySummaryResourceAppExportInputSLZ(
            data={
                "time_start": timestamp,
                "time_end": timestamp,
            }
        )

        slz.is_valid(raise_exception=True)
        self.assertEqual(
            slz.validated_data,
            {
                "time_start": timestamp,
                "time_end": timestamp,
            },
        )
