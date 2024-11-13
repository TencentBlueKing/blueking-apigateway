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
from ddf import G

from apigateway.core.models import Resource


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
                    "datapoints": []
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
        assert result["data"]["series"][0]["target"] == "name=testname001"
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
