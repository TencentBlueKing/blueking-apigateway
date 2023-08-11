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

from apigateway.apis.open.metrics import views
from apigateway.apps.metrics.models import StatisticsAPIRequestByDay, StatisticsAppRequestByDay
from apigateway.core.models import Gateway
from apigateway.tests.utils.testing import APIRequestFactory, dummy_time, get_response_json


class TestStatisticsV1ViewSet(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.factory = APIRequestFactory()

    def test_query_api_request(self):
        api = G(Gateway, name="test", _maintainers="admin1;admin2")

        G(
            StatisticsAPIRequestByDay,
            api_id=api.id,
            start_time=dummy_time.time,
            total_count=1,
            failed_count=1,
        )
        G(
            StatisticsAppRequestByDay,
            bk_app_code="test",
            api_id=api.id,
            start_time=dummy_time.time,
            total_count=1,
            failed_count=1,
        )

        data = [
            {
                "start_time": dummy_time.timestamp,
                "end_time": dummy_time.timestamp,
            },
        ]
        for test in data:
            request = self.factory.get("/api/v1/apis/metrics/statistics/query-api-metrics/", data=test)

            view = views.StatisticsV1ViewSet.as_view({"get": "query_api_metrics"})
            response = view(request)

            result = get_response_json(response)
            self.assertEqual(result["code"], 0, json.dumps(result))
            self.assertEqual(response.status_code, 200, json.dumps(result))
            self.assertEqual(
                result["data"],
                [
                    {
                        "api_id": api.id,
                        "api_name": api.name,
                        "api_maintainers": api.maintainers,
                        "total_count": 1,
                        "failed_count": 1,
                        "bk_app_code_list": ["test"],
                    }
                ],
            )
