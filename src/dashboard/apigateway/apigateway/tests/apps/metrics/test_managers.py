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

from apigateway.apps.metrics.models import StatisticsAPIRequestByDay, StatisticsAppRequestByDay
from apigateway.core.models import Gateway
from apigateway.tests.utils.testing import dummy_time


class TestStatisticsAPIRequestManager(TestCase):
    def test_filter_and_aggregate_by_api(self):
        gateway_1 = G(Gateway)
        gateway_2 = G(Gateway)

        G(
            StatisticsAPIRequestByDay,
            api_id=gateway_1.id,
            start_time=dummy_time.time,
            total_count=1,
            failed_count=1,
        )
        G(
            StatisticsAPIRequestByDay,
            api_id=gateway_2.id,
            start_time=dummy_time.time,
            total_count=10,
            failed_count=10,
        )
        G(
            StatisticsAPIRequestByDay,
            api_id=gateway_1.id,
            start_time=dummy_time.time,
            total_count=100,
            failed_count=100,
        )

        result = StatisticsAPIRequestByDay.objects.filter_and_aggregate_by_api(
            start_time=dummy_time.time, end_time=dummy_time.time
        )

        self.assertEqual(
            result,
            {
                gateway_1.id: {
                    "api_id": gateway_1.id,
                    "total_count": 101,
                    "failed_count": 101,
                },
                gateway_2.id: {
                    "api_id": gateway_2.id,
                    "total_count": 10,
                    "failed_count": 10,
                },
            },
        )


class TestStatisticsAppRequestManager(TestCase):
    def test_filter_app_and_aggregate_by_api(self):
        gateway_1 = G(Gateway)
        gateway_2 = G(Gateway)

        G(
            StatisticsAppRequestByDay,
            bk_app_code="test1",
            api_id=gateway_1.id,
            start_time=dummy_time.time,
            total_count=1,
            failed_count=1,
        )
        G(
            StatisticsAppRequestByDay,
            bk_app_code="test1",
            api_id=gateway_2.id,
            start_time=dummy_time.time,
            total_count=10,
            failed_count=10,
        )
        G(
            StatisticsAppRequestByDay,
            bk_app_code="test2",
            api_id=gateway_1.id,
            start_time=dummy_time.time,
            total_count=100,
            failed_count=100,
        )

        result = StatisticsAppRequestByDay.objects.filter_app_and_aggregate_by_api(
            start_time=dummy_time.time, end_time=dummy_time.time
        )
        result[gateway_1.id]["bk_app_code_list"] = sorted(result[gateway_1.id]["bk_app_code_list"])

        self.assertEqual(
            result,
            {
                gateway_1.id: {
                    "api_id": gateway_1.id,
                    "bk_app_code_list": ["test1", "test2"],
                },
                gateway_2.id: {
                    "api_id": gateway_2.id,
                    "bk_app_code_list": ["test1"],
                },
            },
        )
