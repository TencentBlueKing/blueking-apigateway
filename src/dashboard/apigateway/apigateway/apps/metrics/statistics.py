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
import logging
from collections import defaultdict
from typing import Optional

from apigateway.core.models import Gateway, Resource
from apigateway.utils.time import utctime

from .models import StatisticsAPIRequestByDay, StatisticsAppRequestByDay
from .prometheus.statistics import (
    StatisticsAPIRequestDurationMetrics,
    StatisticsAPIRequestMetrics,
    StatisticsAppRequestMetrics,
)

logger = logging.getLogger(__name__)


class StatisticsHandler:
    def __init__(self):
        self._gateway_name_to_id = dict(Gateway.objects.all().values_list("name", "id"))

        # gateway_id -> resource_name -> resource_id, e.g. {1: {"echo": 10}}
        self._gateway_id_to_resources = {}

    def stats(self, start: int, end: int, step: str):
        # 1. 清理统计时间重复的数据
        self._clear_data_by_stats_time(start)

        # 2. 写入统计数据
        self._save_api_request_data(start, end, step)
        self._save_app_request_data(start, end, step)

    def _clear_data_by_stats_time(self, start):
        start_time = utctime(start).datetime

        StatisticsAPIRequestByDay.objects.filter(start_time=start_time).delete()
        StatisticsAppRequestByDay.objects.filter(start_time=start_time).delete()

    def _save_api_request_data(self, start, end, step):
        api_request_count = StatisticsAPIRequestMetrics().query(end, step)
        if not api_request_count.get("series"):
            logger.error("The resource request data obtained from Prometheus is empty, skip statistics.")
            return

        api_request_duration = StatisticsAPIRequestDurationMetrics().query(end, step)
        if not api_request_duration.get("series"):
            logger.warning("The resource request duration data obtained from Prometheus is empty.")
            # 获取失败，则数据中不记录耗时，但不影响核心服务

        # 统计请求数/失败请求数
        api_request_data = defaultdict(dict)
        for item in api_request_count["series"]:
            dimensions = item["dimensions"]

            gateway_name = dimensions["api_name"]
            key = f'{dimensions["stage_name"]}:{dimensions["resource_name"]}'
            api_request_data[gateway_name].setdefault(key, defaultdict(float))

            count = item["datapoints"][0][0]
            api_request_data[gateway_name][key]["total_count"] += count
            if dimensions["proxy_error"] != "0":
                api_request_data[gateway_name][key]["failed_count"] += count

        # 统计请求总耗时
        for item in api_request_duration.get("series", []):
            dimensions = item["dimensions"]

            gateway_name = dimensions["api_name"]
            key = f'{dimensions["stage_name"]}:{dimensions["resource_name"]}'

            if gateway_name in api_request_data and key in api_request_data[gateway_name]:
                api_request_data[gateway_name][key]["total_msecs"] = item["datapoints"][0][0]

        # 保存数据
        statistics_record = []
        for gateway_name, gateway_request_data in api_request_data.items():
            gateway_id = self._get_gateway_id(gateway_name)
            if not gateway_id:
                logger.warning("gateway (name=%s) does not exist, skip save api statistics.", gateway_name)
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
                        gateway_name,
                    )
                    continue

                statistics_record.append(
                    StatisticsAPIRequestByDay(
                        total_count=int(request_data["total_count"]),
                        failed_count=int(request_data["failed_count"]),
                        total_msecs=int(request_data["total_msecs"]),
                        start_time=utctime(start).datetime,
                        end_time=utctime(end).datetime,
                        api_id=gateway_id,
                        stage_name=stage_name,
                        resource_id=resource_id,
                    )
                )

        StatisticsAPIRequestByDay.objects.bulk_create(statistics_record, batch_size=100)

    def _save_app_request_data(self, start, end, step):
        app_request_count = StatisticsAppRequestMetrics().query(end, step)
        if not app_request_count.get("series"):
            logger.error("The app request data obtained from Prometheus is empty, skip statistics.")
            return

        # 保存数据
        statistics_record = []
        for item in app_request_count.get("series", []):
            count = int(item["datapoints"][0][0])

            if count == 0:
                continue

            dimensions = item["dimensions"]
            gateway_name = dimensions["api_name"]
            resource_name = dimensions["resource_name"]
            bk_app_code = dimensions.get("bk_app_code") or dimensions.get("app_code", "")

            gateway_id = self._get_gateway_id(gateway_name)
            if not gateway_id:
                logger.warning("gateway (name=%s) does not exist, skip save app statistics.", gateway_name)
                continue

            resource_id = self._get_resource_id(gateway_id, resource_name)
            if not resource_id:
                logger.warning(
                    "resource (name=%s) of gateway (name=%s) does not exist, skip save app statistics.",
                    resource_name,
                    gateway_name,
                )
                continue

            statistics_record.append(
                StatisticsAppRequestByDay(
                    total_count=count,
                    start_time=utctime(start).datetime,
                    end_time=utctime(end).datetime,
                    bk_app_code=bk_app_code,
                    api_id=gateway_id,
                    stage_name=dimensions["stage_name"],
                    resource_id=resource_id,
                )
            )

        StatisticsAppRequestByDay.objects.bulk_create(statistics_record, batch_size=100)

    def _get_gateway_id(self, gateway_name: str) -> Optional[int]:
        return self._gateway_name_to_id.get(gateway_name)

    def _get_resource_id(self, gateway_id: int, resource_name: str) -> Optional[int]:
        if gateway_id not in self._gateway_id_to_resources:
            self._gateway_id_to_resources[gateway_id] = Resource.objects.filter_resource_name_to_id(gateway_id)

        return self._gateway_id_to_resources[gateway_id].get(resource_name)
