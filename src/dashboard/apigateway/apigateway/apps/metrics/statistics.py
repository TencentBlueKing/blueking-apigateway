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
from collections import defaultdict

from apigateway.apps.metrics.models import StatisticsAPIRequestByDay, StatisticsAppRequestByDay
from apigateway.apps.metrics.stats_helpers import (
    StatisticsAPIRequestDurationMetrics,
    StatisticsAPIRequestMetrics,
    StatisticsAppRequestMetrics,
)
from apigateway.utils.time import utctime


class StatisticsHandler:
    def stats(self, start, end, step):
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
        if not api_request_count.result:
            return

        api_request_duration = StatisticsAPIRequestDurationMetrics().query(end, step)
        if not api_request_duration.result:
            return

        # 统计请求数/失败请求数
        api_request_data = {}
        for item in api_request_count.result:
            key = f'{item.metric["api"]}:{item.metric["stage"]}:{item.metric["resource"]}'

            api_request_data.setdefault(key, defaultdict(int))
            count = int(float(item.value[1]))

            api_request_data[key]["total_count"] += count
            if item.metric["proxy_error"] != "0":
                api_request_data[key]["failed_count"] += count

        # 统计请求总耗时
        for item in api_request_duration.result:
            key = f'{item.metric["api"]}:{item.metric["stage"]}:{item.metric["resource"]}'

            if key in api_request_data:
                api_request_data[key]["total_msecs"] = int(float(item.value[1]))

        # 保存数据
        statistics_record = []
        for key, request_data in api_request_data.items():
            api_id, stage_name, resource_id = key.split(":")

            if request_data["total_count"] == 0 and request_data["failed_count"] == 0:
                continue

            statistics_record.append(
                StatisticsAPIRequestByDay(
                    total_count=request_data["total_count"],
                    failed_count=request_data["failed_count"],
                    total_msecs=request_data["total_msecs"],
                    start_time=utctime(start).datetime,
                    end_time=utctime(end).datetime,
                    api_id=int(api_id),
                    stage_name=stage_name,
                    resource_id=int(resource_id),
                )
            )

        StatisticsAPIRequestByDay.objects.bulk_create(statistics_record, batch_size=100)

    def _save_app_request_data(self, start, end, step):
        app_request_count = StatisticsAppRequestMetrics().query(end, step)
        if not app_request_count.result:
            return

        # 保存数据
        statistics_record = []
        for item in app_request_count.result:
            count = int(float(item.value[1]))

            if count == 0:
                continue

            statistics_record.append(
                StatisticsAppRequestByDay(
                    total_count=count,
                    start_time=utctime(start).datetime,
                    end_time=utctime(end).datetime,
                    bk_app_code=item.metric.get("app_code", ""),
                    api_id=int(item.metric["api"]),
                    stage_name=item.metric["stage"],
                    resource_id=int(item.metric["resource"]),
                )
            )

        StatisticsAppRequestByDay.objects.bulk_create(statistics_record, batch_size=100)
