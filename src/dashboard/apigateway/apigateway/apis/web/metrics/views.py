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
import math

from django.http import Http404
from drf_yasg.utils import swagger_auto_schema
from rest_framework import generics, status

from apigateway.apps.metrics.constants import MetricsNumberEnum, MetricsRangeEnum
from apigateway.apps.metrics.prometheus.dimension import MetricsNumberFactory, MetricsRangeFactory
from apigateway.core.models import Resource, Stage
from apigateway.utils.responses import OKJsonResponse
from apigateway.utils.time import SmartTimeRange

from .serializers import MetricsQueryNumberInputSLZ, MetricsQueryRangeInputSLZ


class MetricsSmartTimeRange(SmartTimeRange):
    def get_recommended_step(self) -> str:
        """根据 time_start, time_end，获取推荐的步长"""
        start, end = self.get_head_and_tail()

        return self._calculate_step(start, end)

    def _calculate_step(self, start: int, end: int) -> str:
        """
        :param start: 起始时间戳
        :param end: 结束时间戳
        :returns: 推荐步长

        step via the gap of query time
        1m  <- 1h
        5m  <- 6h
        10m <- 12h
        30m <- 24h
        1h  <- 72h
        3h  <- 7d
        12h <- >7d
        """
        step_options = ["1m", "5m", "10m", "30m", "1h", "3h", "12h"]

        gap_minutes = math.ceil((end - start) / 60)
        if gap_minutes <= 60:
            index = 0
        elif gap_minutes <= 360:
            index = 1
        elif gap_minutes <= 720:
            index = 2
        elif gap_minutes <= 1440:
            index = 3
        elif gap_minutes <= 4320:
            index = 4
        elif gap_minutes <= 10080:
            index = 5
        else:
            index = 6

        return step_options[index]


class QueryRangeApi(generics.ListAPIView):
    @swagger_auto_schema(
        query_serializer=MetricsQueryRangeInputSLZ,
        responses={status.HTTP_200_OK: ""},
        operation_description="查询 metrics",
        tags=["WebAPI.Metrics"],
    )
    def get(self, request, *args, **kwargs):
        slz = MetricsQueryRangeInputSLZ(data=request.query_params)
        slz.is_valid(raise_exception=True)

        data = slz.validated_data
        stage_name = Stage.objects.get_name(request.gateway.id, data["stage_id"])
        if not stage_name:
            raise Http404

        resource_name = None
        if data.get("resource_id"):
            resource_name = (
                Resource.objects.filter(gateway=request.gateway, id=data["resource_id"])
                .values_list("name", flat=True)
                .first()
            )

        smart_time_range = MetricsSmartTimeRange(
            data.get("time_start"),
            data.get("time_end"),
            data.get("time_range"),
        )
        time_start, time_end = smart_time_range.get_head_and_tail()
        step = smart_time_range.get_recommended_step()

        metrics = MetricsRangeFactory.create_metrics(MetricsRangeEnum(data["metrics"]))

        data = metrics.query_range(
            gateway_name=request.gateway.name,
            stage_id=data.get("stage_id", 0),
            stage_name=stage_name,
            resource_id=data.get("resource_id", 0),
            resource_name=resource_name,
            start=time_start,
            end=time_end,
            step=step,
        )
        return OKJsonResponse(data=data)


class QueryNumberApi(generics.ListAPIView):
    @swagger_auto_schema(
        query_serializer=MetricsQueryNumberInputSLZ,
        responses={status.HTTP_200_OK: ""},
        operation_description="查询 metrics",
        tags=["WebAPI.Metrics"],
    )
    def get(self, request, *args, **kwargs):
        slz = MetricsQueryNumberInputSLZ(data=request.query_params)
        slz.is_valid(raise_exception=True)
        data = slz.validated_data
        stage_name = Stage.objects.get_name(request.gateway.id, data["stage_id"])
        if not stage_name:
            raise Http404
        resource_name = None
        if data.get("resource_id"):
            resource_name = (
                Resource.objects.filter(gateway=request.gateway, id=data["resource_id"])
                .values_list("name", flat=True)
                .first()
            )

        smart_time_range = MetricsSmartTimeRange(
            data.get("time_start"),
            data.get("time_end"),
            data.get("time_range"),
        )
        time_start, time_end = smart_time_range.get_head_and_tail()
        step = smart_time_range.get_recommended_step()

        # 暂时只有总数和健康率，所以总数是必需需要计算的
        metrics = MetricsNumberFactory.create_metrics(MetricsNumberEnum.REQUESTS_TOTAL)

        request_total_data = metrics.query_range(
            gateway_name=request.gateway.name,
            stage_id=data.get("stage_id", 0),
            stage_name=stage_name,
            resource_id=data.get("resource_id", 0),
            resource_name=resource_name,
            start=time_start,
            end=time_end,
            step=step,
        )
        # 计算总数
        request_total_number = self._get_data_differ_number(request_total_data)

        if data["metrics"] == MetricsNumberEnum.HEALTH_RATE.value:
            # 总数为0直接返回0
            if request_total_number == 0:
                return OKJsonResponse(data=0)
            metrics = MetricsNumberFactory.create_metrics(data["metrics"])
            failed_500_status_data = metrics.query_range(
                gateway_name=request.gateway.name,
                stage_id=data.get("stage_id", 0),
                stage_name=stage_name,
                resource_id=data.get("resource_id", 0),
                resource_name=resource_name,
                start=time_start,
                end=time_end,
                step=step,
            )
            failed_500_status_number = self._get_data_differ_number(failed_500_status_data)
            # 健康率 = 1 - （500 状态码请求数/总请求数）
            return OKJsonResponse(data=1 - (failed_500_status_number / request_total_number))

        return OKJsonResponse(data=request_total_number)

    def _get_data_differ_number(self, data: dict) -> int:
        # 检查传入的数据是否为None或不是字典
        if data is None or not isinstance(data, dict):
            return 0

        # 检查'data'键和'series'列表的存在性和非空性
        # 返回的没有没有数据的情况是这样的 {"result": true, "code": 200, "message": "OK", "data": {"metrics": [], "series": []}}
        if (
            "data" in data
            and isinstance(data["data"], dict)
            and "series" in data["data"]
            and isinstance(data["data"]["series"], list)
            and len(data["data"]["series"]) > 0
        ):
            # 获取'datapoints'列表
            datapoints = data["data"]["series"][0].get("datapoints", [])

            # 检查'datapoints'列表非空并且至少有两个数据点
            if len(datapoints) > 1:
                # 获取最后一条数据点和第一条数据点
                last_value = datapoints[-1][0]
                first_value = datapoints[0][0]

                # 如果 first_value 为 None，将 first_value 设为 0
                # 示例: {"result": true, "code": 200, "message": "OK", "data": {"metrics": [], "series": [{"datapoints": [[null, 1708290000000], [9, 1727161200000], [41, 1728370800000], [41, 1728374400000]]}]}}
                first_number = 0 if first_value is None else first_value

                # 如果 last_value 为 None，将 last_value 设为倒数第二条数据点的值
                # 示例：{"result": true, "code": 200, "message": "OK", "data": {"metrics": [], "series": [{"datapoints": [[30, 1728291600000], [44, 1728460800000], [44, 1728464400000], [null, 1758373200000]]}]}}
                last_number = datapoints[-2][0] if last_value is None and len(datapoints) > 1 else last_value

                # 返回计算的差值，并确保结果是整数
                return int(last_number) - int(first_number)

        # 如果没有有效数据，返回0
        return 0
