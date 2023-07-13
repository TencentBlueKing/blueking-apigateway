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


class TestQueryRangeAPIView:
    def test_get(self, mocker, fake_stage, request_view):
        mocker.patch(
            "apigateway.apps.metrics.views.DimensionMetricsFactory.create_dimension_metrics",
            return_value=mocker.Mock(query_range=mocker.Mock(return_value={"foo": "bar"})),
        )

        response = request_view(
            "GET",
            "metrics.query_range",
            path_params={
                "gateway_id": fake_stage.api.id,
            },
            data={
                "stage_id": fake_stage.id,
                "dimension": "all",
                "metrics": "requests",
                "time_range": 300,
            },
        )
        result = response.json()
        assert response.status_code == 200
        assert result["result"] is True
        assert result["data"] == {"foo": "bar"}

        # stage not found
        response = request_view(
            "GET",
            "metrics.query_range",
            path_params={
                "gateway_id": fake_stage.api.id,
            },
            data={
                "stage_id": 0,
                "dimension": "all",
                "metrics": "requests",
                "time_range": 300,
            },
        )
        assert response.status_code == 404
