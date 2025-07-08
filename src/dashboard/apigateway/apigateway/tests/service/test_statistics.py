#
# TencentBlueKing is pleased to support the open source community by making
# 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
# Copyright (C) 2025 Tencent. All rights reserved.
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
import pytest

from apigateway.apps.metrics.models import StatisticsAppRequestByDay, StatisticsGatewayRequestByDay
from apigateway.service.statistics import (
    AppRequestStatistics,
    BaseRequestStatistics,
    GatewayRequestStatistics,
)
from apigateway.utils.time import now_datetime


@pytest.fixture()
def fake_statistics_api_request_metrics(fake_resource):
    fake_gateway = fake_resource.gateway
    return {
        "series": [
            {
                "dimensions": {
                    "api_name": fake_gateway.name,
                    "stage_name": "prod",
                    "resource_name": fake_resource.name,
                    "proxy_error": "0",
                },
                "datapoints": [[5, 1689292799000]],
            },
            {
                "dimensions": {
                    "api_name": fake_gateway.name,
                    "stage_name": "prod",
                    "resource_name": fake_resource.name,
                    "proxy_error": "1",
                },
                "datapoints": [[2, 1689292799000]],
            },
        ]
    }


@pytest.fixture()
def fake_statistics_api_request_duration_metrics(fake_resource):
    fake_gateway = fake_resource.gateway
    return {
        "series": [
            {
                "dimensions": {
                    "api_name": fake_gateway.name,
                    "stage_name": "prod",
                    "resource_name": fake_resource.name,
                },
                "datapoints": [[154, 1689292799000]],
            },
        ]
    }


@pytest.fixture()
def fake_statistics_app_request_metrics(fake_resource):
    fake_gateway = fake_resource.gateway
    return {
        "series": [
            {
                "dimensions": {
                    "api_name": fake_gateway.name,
                    "stage_name": "prod",
                    "resource_name": fake_resource.name,
                },
                "datapoints": [[2, 1689292799000]],
            },
            {
                "dimensions": {
                    "bk_app_code": "app1",
                    "api_name": fake_gateway.name,
                    "stage_name": "prod",
                    "resource_name": fake_resource.name,
                },
                "datapoints": [[0, 1689292799000]],
            },
            {
                "dimensions": {
                    "bk_app_code": "app2",
                    "api_name": fake_gateway.name,
                    "stage_name": "prod",
                    "resource_name": fake_resource.name,
                },
                "datapoints": [[3, 1689292799000]],
            },
            {
                "dimensions": {
                    "bk_app_code": "app2",
                    "api_name": fake_gateway.name,
                    "stage_name": "test",
                    "resource_name": fake_resource.name,
                },
                "datapoints": [[1736, 1689292799000]],
            },
        ]
    }


class TestBaseRequestStatistics:
    def test_get_gateway_id(self, fake_gateway):
        stats_client = BaseRequestStatistics()

        assert stats_client._get_gateway_id(fake_gateway.name) == fake_gateway.id

    def test_get_resource_id(self, fake_resource):
        fake_gateway = fake_resource.gateway

        stats_client = BaseRequestStatistics()

        assert stats_client._gateway_id_to_resources == {}
        assert stats_client._get_resource_id(fake_gateway.id, fake_resource.name) == fake_resource.id
        assert stats_client._get_resource_id(fake_gateway.id, "not-exist-resource") is None
        assert fake_gateway.id in stats_client._gateway_id_to_resources


class TestGatewayRequestStatistics:
    def test_save_gateway_request_data(
        self,
        mocker,
        fake_resource,
        fake_statistics_api_request_metrics,
    ):
        mocker.patch(
            "apigateway.service.statistics.StatisticsGatewayRequestMetrics.query",
            return_value=fake_statistics_api_request_metrics,
        )
        fake_gateway = fake_resource.gateway

        now = now_datetime()

        stats_client = GatewayRequestStatistics()
        stats_client._save_gateway_request_data(now, now, "1m", "my-gateway")

        assert StatisticsGatewayRequestByDay.objects.filter(gateway_id=fake_gateway.id).count() == 1
        record = StatisticsGatewayRequestByDay.objects.get(gateway_id=fake_gateway.id, resource_id=fake_resource.id)
        assert record.total_count == 7
        assert record.failed_count == 2


class TestAppRequestStatistics:
    def test_save_app_request_data(self, mocker, fake_resource, fake_statistics_app_request_metrics):
        fake_gateway = fake_resource.gateway
        mocker.patch(
            "apigateway.service.statistics.StatisticsAppRequestMetrics.query",
            return_value=fake_statistics_app_request_metrics,
        )

        now = now_datetime()

        stats_client = AppRequestStatistics()
        stats_client._save_app_request_data(now, now, "1m", "my-gateway")

        assert StatisticsAppRequestByDay.objects.filter(gateway_id=fake_gateway.id).count() == 3
        assert StatisticsAppRequestByDay.objects.filter(gateway_id=fake_gateway.id, bk_app_code="app2").count() == 2

        record1 = StatisticsAppRequestByDay.objects.get(gateway_id=fake_gateway.id, bk_app_code="")
        assert record1.total_count == 2

        record2 = StatisticsAppRequestByDay.objects.get(
            gateway_id=fake_gateway.id, bk_app_code="app2", stage_name="test"
        )
        assert record2.total_count == 1736
