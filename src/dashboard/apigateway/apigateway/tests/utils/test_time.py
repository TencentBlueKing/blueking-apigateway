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
from unittest import mock

import pytest
from django.test import TestCase

from apigateway.utils import time
from apigateway.utils.time import MetricsSmartTimeRange


class TestUtilsTime:
    def test_now_str(self):
        nstr = time.now_str()

        assert len(nstr) == 24

    @pytest.mark.parametrize(
        "params, expected",
        [
            (
                {
                    "days": 1,
                },
                24 * 3600,
            ),
            (
                {
                    "days": 0,
                },
                0,
            ),
        ],
    )
    def test_to_seconds(self, params, expected):
        result = time.to_seconds(days=params.get("days"))
        assert result == expected


class TestSmartTimeRange(TestCase):
    def test_get_head_and_tail(self):
        data = [
            {
                "data": {
                    "time_start": 1572960000,
                    "time_end": 1572990000,
                },
                "expected": (1572960000, 1572990000),
            },
            {
                "data": {
                    "time_start": 1572960000,
                    "time_end": 1572990000,
                    "time_range": 300000,
                },
                "expected": (1572960000, 1572990000),
            },
            {
                "data": {
                    "time_range": 300,
                },
                "mock_now_timestamp": 1572960000,
                "expected": (1572959700, 1572960000),
            },
        ]
        for test in data:
            with mock.patch("apigateway.utils.time.now_timestamp") as mock_now_timestamp:
                mock_now_timestamp.return_value = test.get("mock_now_timestamp")
                smart_time_range = time.SmartTimeRange(**test["data"])
                self.assertEqual(smart_time_range.get_head_and_tail(), test["expected"])

    def test_get_interval(self):
        data = [
            {
                "data": {
                    "time_start": 1572960000,
                    "time_end": 1572990000,
                },
                "expected": "10m",
            },
        ]
        for test in data:
            smart_time_range = time.SmartTimeRange(**test["data"])
            self.assertEqual(smart_time_range.get_interval(), test["expected"])


class TestMetricsSmartTimeRange:
    @pytest.mark.parametrize(
        "time_range_minutes, expected",
        [
            (10, "1m"),
            (59, "1m"),
            (60, "1m"),
            (300, "5m"),
            (360, "5m"),
            (720, "10m"),
            (1440, "30m"),
            (4320, "1h"),
            (10080, "3h"),
            (20000, "12h"),
        ],
    )
    def test_get_recommended_step(self, time_range_minutes, expected):
        smart_time_range = MetricsSmartTimeRange(time_range=time_range_minutes * 60)
        assert smart_time_range.get_interval() == expected
