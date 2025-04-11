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
import time

import pytest
from ddf import G

from apigateway.apps.metrics.models import StatisticsAppRequestByDay, StatisticsGatewayRequestByDay
from apigateway.core.models import Resource
from apigateway.utils.time import utctime


class TestQueryRangeApi:
    def test_get(self, mocker, fake_stage, request_view):
        resource_obj = G(Resource, name="testname001", gateway=fake_stage.gateway)

        data = {
            "metrics": [],
            "series": [
                {
                    "alias": "_result_",
                    "metric_field": "_result_",
                    "unit": "",
                    "target": 'route="bk-esb.prod.{}"'.format(resource_obj.id),
                    "dimensions": {"route": "bk-esb.prod.2152"},
                    "datapoints": [],
                },
                {
                    "alias": "_result_",
                    "metric_field": "_result_",
                    "unit": "",
                    "target": 'route="bk-esb.prod.1234"',
                    "dimensions": {"route": "bk-esb.prod.1234"},
                    "datapoints": [],
                },
                {
                    "alias": "_result_",
                    "metric_field": "_result_",
                    "unit": "",
                    "target": "",
                    "dimensions": {},
                    "datapoints": [],
                },
            ],
        }

        mocker.patch(
            "apigateway.apis.web.metrics.views.MetricsRangeFactory.create_metrics",
            return_value=mocker.Mock(query_range=mocker.Mock(return_value=data)),
        )

        response = request_view(
            "GET",
            "metrics.query_range",
            path_params={
                "gateway_id": fake_stage.gateway.id,
            },
            data={
                "stage_id": fake_stage.id,
                "metrics": "ingress",
                "time_range": 300,
            },
        )
        result = response.json()

        assert response.status_code == 200
        assert result["data"]["series"][0]["target"] == 'name="testname001"'
        assert result["data"]["series"][1]["target"] == 'route="bk-esb.prod.1234"'
        assert len(result["data"]["series"]) == 2

        mocker.patch(
            "apigateway.apis.web.metrics.views.MetricsRangeFactory.create_metrics",
            return_value=mocker.Mock(query_range=mocker.Mock(return_value={"foo": "bar"})),
        )

        response = request_view(
            "GET",
            "metrics.query_range",
            path_params={
                "gateway_id": fake_stage.gateway.id,
            },
            data={
                "stage_id": fake_stage.id,
                "metrics": "requests",
                "time_range": 300,
            },
        )
        result = response.json()
        assert response.status_code == 200
        assert result["data"] == {"foo": "bar"}

        # stage not found
        response = request_view(
            "GET",
            "metrics.query_range",
            path_params={
                "gateway_id": fake_stage.gateway.id,
            },
            data={
                "stage_id": 0,
                "metrics": "requests",
                "time_range": 300,
            },
        )
        assert response.status_code == 404


class TestQueryInstantApi:
    def test_get(self, mocker, fake_stage, request_view):
        mocker.patch(
            "apigateway.apis.web.metrics.views.MetricsInstantFactory.create_metrics",
            return_value=mocker.Mock(query_instant=mocker.Mock(return_value={"instant": 0})),
        )

        response = request_view(
            "GET",
            "metrics.query_instant",
            path_params={
                "gateway_id": fake_stage.gateway.id,
            },
            data={
                "stage_id": fake_stage.id,
                "metrics": "requests_total",
                "time_range": 300,
            },
        )
        result = response.json()
        assert response.status_code == 200
        assert result["data"] == {"instant": 0}  # 没有数据的情况

        # stage not found
        response = request_view(
            "GET",
            "metrics.query_instant",
            path_params={
                "gateway_id": fake_stage.gateway.id,
            },
            data={
                "stage_id": 0,
                "metrics": "requests_total",
                "time_range": 300,
            },
        )
        assert response.status_code == 404


class TestQuerySummaryApi:
    @pytest.fixture(autouse=True)
    def setup_fixtures(self, fake_stage):
        self.resource_obj1 = G(Resource, name="test1", gateway=fake_stage.gateway)
        self.resource_obj2 = G(Resource, name="test2", gateway=fake_stage.gateway)
        G(
            StatisticsGatewayRequestByDay,
            gateway_id=fake_stage.gateway.id,
            stage_name=fake_stage.name,
            resource_id=self.resource_obj1.id,
            total_count=100,
            failed_count=10,
            total_msecs=600,
            start_time=utctime(int(time.time())).datetime,
            end_time=utctime(int(time.time())).datetime,
        )
        G(
            StatisticsGatewayRequestByDay,
            gateway_id=fake_stage.gateway.id,
            stage_name=fake_stage.name,
            resource_id=self.resource_obj2.id,
            total_count=200,
            failed_count=20,
            total_msecs=800,
            start_time=utctime(int(time.time())).datetime,
            end_time=utctime(int(time.time())).datetime,
        )

    def test_get_requests_total(self, fake_stage, request_view):
        response = request_view(
            "GET",
            "metrics.query_summary",
            path_params={
                "gateway_id": fake_stage.gateway.id,
            },
            data={
                "type": "gateway",
                "stage_id": fake_stage.id,
                "metrics": "requests_total",
                "time_dimension": "day",
                "time_start": int((datetime.datetime.now() + datetime.timedelta(days=-1)).timestamp()),
                "time_end": int(time.time()),
            },
        )
        result = response.json()
        assert response.status_code == 200
        assert len(result["data"]["series"]) == 1
        assert result["data"]["series"]["datapoints"][0][0] == 300

    def test_get_requests_total_by_week(self, fake_stage, request_view):
        response = request_view(
            "GET",
            "metrics.query_summary",
            path_params={
                "gateway_id": fake_stage.gateway.id,
            },
            data={
                "type": "gateway",
                "stage_id": fake_stage.id,
                "metrics": "requests_total",
                "time_dimension": "week",
                "time_start": int((datetime.datetime.now() + datetime.timedelta(days=-1)).timestamp()),
                "time_end": int(time.time()),
            },
        )
        result = response.json()
        assert response.status_code == 200
        assert len(result["data"]["series"]) == 1

    def test_get_requests_total_by_month(self, fake_stage, request_view):
        response = request_view(
            "GET",
            "metrics.query_summary",
            path_params={
                "gateway_id": fake_stage.gateway.id,
            },
            data={
                "type": "gateway",
                "stage_id": fake_stage.id,
                "metrics": "requests_total",
                "time_dimension": "month",
                "time_start": int((datetime.datetime.now() + datetime.timedelta(days=-1)).timestamp()),
                "time_end": int(time.time()),
            },
        )
        result = response.json()
        assert response.status_code == 200
        assert len(result["data"]["series"]) == 1

    def test_get_requests_failed_total(self, fake_stage, request_view):
        response = request_view(
            "GET",
            "metrics.query_summary",
            path_params={
                "gateway_id": fake_stage.gateway.id,
            },
            data={
                "type": "gateway",
                "stage_id": fake_stage.id,
                "metrics": "requests_failed_total",
                "time_dimension": "day",
                "time_start": int((datetime.datetime.now() + datetime.timedelta(days=-1)).timestamp()),
                "time_end": int(time.time()),
            },
        )
        result = response.json()
        assert response.status_code == 200
        assert len(result["data"]["series"]) == 1
        assert result["data"]["series"]["datapoints"][0][0] == 30

    def test_get_resource_id(self, fake_stage, request_view):
        response = request_view(
            "GET",
            "metrics.query_summary",
            path_params={
                "gateway_id": fake_stage.gateway.id,
            },
            data={
                "type": "gateway",
                "stage_id": fake_stage.id,
                "metrics": "requests_total",
                "time_dimension": "day",
                "resource_id": self.resource_obj1.id,
                "time_start": int((datetime.datetime.now() + datetime.timedelta(days=-1)).timestamp()),
                "time_end": int(time.time()),
            },
        )
        result = response.json()
        assert response.status_code == 200
        assert len(result["data"]["series"]) == 1
        assert result["data"]["series"]["datapoints"][0][0] == 100

    def test_get_bk_app_code(self, fake_stage, request_view):
        resource_obj3 = G(Resource, name="test3", gateway=fake_stage.gateway)
        G(
            StatisticsAppRequestByDay,
            gateway_id=fake_stage.gateway.id,
            stage_name=fake_stage.name,
            resource_id=resource_obj3.id,
            bk_app_code="app1",
            total_count=100,
            failed_count=10,
            total_msecs=600,
            start_time=utctime(int(time.time())).datetime,
            end_time=utctime(int(time.time())).datetime,
        )
        G(
            StatisticsAppRequestByDay,
            gateway_id=fake_stage.gateway.id,
            stage_name=fake_stage.name,
            resource_id=resource_obj3.id,
            bk_app_code="app2",
            total_count=200,
            failed_count=20,
            total_msecs=800,
            start_time=utctime(int(time.time())).datetime,
            end_time=utctime(int(time.time())).datetime,
        )

        response = request_view(
            "GET",
            "metrics.query_summary",
            path_params={
                "gateway_id": fake_stage.gateway.id,
            },
            data={
                "metrics": "requests_total",
                "time_dimension": "day",
                "stage_id": fake_stage.id,
                "bk_app_code": "app1",
                "time_start": int((datetime.datetime.now() + datetime.timedelta(days=-1)).timestamp()),
                "time_end": int(time.time()),
            },
        )
        result = response.json()

        assert response.status_code == 200
        assert len(result["data"]["series"]) == 1
        assert result["data"]["series"]["datapoints"][0][0] == 100

    def test_get_empty_metrics(self, fake_stage, request_view):
        response = request_view(
            "GET",
            "metrics.query_summary",
            path_params={
                "gateway_id": fake_stage.gateway.id,
            },
            data={
                "metrics": "",
                "time_dimension": "day",
                "stage_id": fake_stage.id,
                "time_start": int((datetime.datetime.now() + datetime.timedelta(days=-1)).timestamp()),
                "time_end": int((datetime.datetime.now()).timestamp()),
            },
        )
        assert response.status_code == 400


class TestQuerySummaryExportApi:
    def test_get(self, request_view, fake_stage):
        response = request_view(
            "GET",
            "metrics.query_summary_export",
            path_params={
                "gateway_id": fake_stage.gateway.id,
            },
            data={
                "type": "gateway",
                "stage_id": fake_stage.id,
                "metrics": "requests_total",
                "time_dimension": "day",
                "time_start": int((datetime.datetime.now() + datetime.timedelta(days=-1)).timestamp()),
                "time_end": int(time.time()),
            },
        )

        assert response.status_code == 200
