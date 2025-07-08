# -*- coding: utf-8 -*-
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
import logging
from collections import defaultdict
from typing import Dict, List, Optional

from apigateway.apps.metrics.models import StatisticsAppRequestByDay, StatisticsGatewayRequestByDay
from apigateway.core.constants import GatewayStatusEnum
from apigateway.core.models import Gateway, Resource
from apigateway.utils.time import utctime

from .prometheus.statistics import (
    StatisticsAppRequestMetrics,
    StatisticsGatewayRequestMetrics,
)

logger = logging.getLogger(__name__)


class StatisticsHandler:
    def stats(self, start: int, end: int, step: str):
        gateway_stats = GatewayRequestStatistics()
        gateway_stats.delete_statistics_by_time(start)
        gateway_stats.statistics(start, end, step)

        app_stats = AppRequestStatistics()
        app_stats.delete_statistics_by_time(start)
        app_stats.statistics(start, end, step)


class BaseRequestStatistics:
    def __init__(self):
        self._gateway_name_to_id = dict(Gateway.objects.all().values_list("name", "id"))

        # gateway_id -> resource_name -> resource_id, e.g. {1: {"echo": 10}}
        self._gateway_id_to_resources = {}

    def _get_active_gateway_names(self) -> List[str]:
        # 如果网关已下线，则不再统计
        return list(Gateway.objects.filter(status=GatewayStatusEnum.ACTIVE.value).values_list("name", flat=True))

    def _get_gateway_id(self, gateway_name: str) -> Optional[int]:
        return self._gateway_name_to_id.get(gateway_name)

    def _get_resource_id(self, gateway_id: int, resource_name: str) -> Optional[int]:
        if gateway_id not in self._gateway_id_to_resources:
            resource_name_to_id = dict(Resource.objects.filter(gateway_id=gateway_id).values_list("name", "id"))
            self._gateway_id_to_resources[gateway_id] = resource_name_to_id

        return self._gateway_id_to_resources[gateway_id].get(resource_name)


class GatewayRequestStatistics(BaseRequestStatistics):
    def delete_statistics_by_time(self, timestamp: int):
        # 清理指定日期的统计数据
        StatisticsGatewayRequestByDay.objects.filter(start_time=utctime(timestamp).datetime).delete()

    def statistics(self, start: int, end: int, step: str):
        # 按网关拉取，写入新数据；全量拉取时，数据量过大可能拉不到
        for gateway_name in self._get_active_gateway_names():
            self._save_gateway_request_data(start, end, step, gateway_name)

    def _save_gateway_request_data(self, start: int, end: int, step: str, gateway_name: str):
        gateway_request_count = StatisticsGatewayRequestMetrics().query(end, step, gateway_name)
        if not gateway_request_count.get("series"):
            logger.info(
                "gateway: %s, the resource request data obtained from Prometheus is empty, skip statistics.",
                gateway_name,
            )
            return

        # 统计请求数/失败请求数
        gateway_name_to_request_data: Dict = defaultdict(dict)
        for item in gateway_request_count["series"]:
            dimensions = item["dimensions"]

            _gateway_name = dimensions["api_name"]
            key = f"{dimensions['stage_name']}:{dimensions['resource_name']}"
            gateway_name_to_request_data[_gateway_name].setdefault(key, defaultdict(float))

            count = item["datapoints"][0][0]
            gateway_name_to_request_data[_gateway_name][key]["total_count"] += count
            if dimensions["proxy_error"] != "0":
                gateway_name_to_request_data[_gateway_name][key]["failed_count"] += count

        # 保存数据
        statistics_record = []
        for _gateway_name, gateway_request_data in gateway_name_to_request_data.items():
            gateway_id = self._get_gateway_id(_gateway_name)
            if not gateway_id:
                logger.warning("gateway (name=%s) does not exist, skip save api statistics.", _gateway_name)
                continue

            for key, request_data in gateway_request_data.items():
                if int(request_data["total_count"]) == 0 and int(request_data["failed_count"]) == 0:
                    continue

                stage_name, resource_name = key.split(":")
                resource_id = self._get_resource_id(gateway_id, resource_name)
                if not resource_id:
                    logger.warning(
                        "resource (name=%s) of gateway (name=%s) does not exist, skip save api statistics.",
                        resource_name,
                        _gateway_name,
                    )
                    continue

                statistics_record.append(
                    StatisticsGatewayRequestByDay(
                        total_count=int(request_data["total_count"]),
                        failed_count=int(request_data["failed_count"]),
                        start_time=utctime(start).datetime,
                        end_time=utctime(end).datetime,
                        gateway_id=gateway_id,
                        stage_name=stage_name,
                        resource_id=resource_id,
                    )
                )

        StatisticsGatewayRequestByDay.objects.bulk_create(statistics_record, batch_size=100)


class AppRequestStatistics(BaseRequestStatistics):
    def delete_statistics_by_time(self, timestamp: int):
        # 清理指定日期的统计数据
        StatisticsAppRequestByDay.objects.filter(start_time=utctime(timestamp).datetime).delete()

    def statistics(self, start: int, end: int, step: str):
        # 按网关拉取，写入新数据；全量拉取时，数据量过大可能拉不到
        for gateway_name in self._get_active_gateway_names():
            self._save_app_request_data(start, end, step, gateway_name)

    def _save_app_request_data(self, start: int, end: int, step: str, gateway_name: str):
        app_request_count = StatisticsAppRequestMetrics().query(end, step, gateway_name)
        if not app_request_count.get("series"):
            logger.info(
                "gateway: %s, the app request data obtained from Prometheus is empty, skip statistics.", gateway_name
            )
            return

        # 保存数据
        statistics_record = []
        for item in app_request_count.get("series", []):
            count = int(item["datapoints"][0][0])

            if count == 0:
                continue

            dimensions = item["dimensions"]
            _gateway_name = dimensions["api_name"]
            resource_name = dimensions["resource_name"]
            bk_app_code = dimensions.get("bk_app_code") or dimensions.get("app_code", "")

            gateway_id = self._get_gateway_id(_gateway_name)
            if not gateway_id:
                logger.warning("gateway (name=%s) does not exist, skip save app statistics.", _gateway_name)
                continue

            resource_id = self._get_resource_id(gateway_id, resource_name)
            if not resource_id:
                logger.warning(
                    "resource (name=%s) of gateway (name=%s) does not exist, skip save app statistics.",
                    resource_name,
                    _gateway_name,
                )
                continue

            statistics_record.append(
                StatisticsAppRequestByDay(
                    total_count=count,
                    start_time=utctime(start).datetime,
                    end_time=utctime(end).datetime,
                    bk_app_code=bk_app_code,
                    gateway_id=gateway_id,
                    stage_name=dimensions["stage_name"],
                    resource_id=resource_id,
                )
            )

        StatisticsAppRequestByDay.objects.bulk_create(statistics_record, batch_size=100)
