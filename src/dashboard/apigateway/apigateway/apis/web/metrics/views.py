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
import csv
from io import StringIO
from typing import Any, List

from django.http import Http404
from django.utils.translation import gettext as _
from drf_yasg.utils import swagger_auto_schema
from rest_framework import generics, status

from apigateway.apps.metrics.constants import (
    MetricsInstantEnum,
    MetricsRangeEnum,
)
from apigateway.apps.metrics.prometheus.dimension import (
    MetricsInstantFactory,
    MetricsRangeFactory,
    MetricsSummaryFactory,
)
from apigateway.core.models import Resource, Stage
from apigateway.utils.responses import DownloadableResponse, OKJsonResponse
from apigateway.utils.time import MetricsSmartTimeRange

from .serializers import MetricsQueryInstantInputSLZ, MetricsQueryRangeInputSLZ, MetricsQuerySummaryInputSLZ


class QueryRangeApi(generics.ListAPIView):
    @staticmethod
    def get_series_resource_id_index_map(series):
        ids_data = {}

        for index in range(len(series)):
            try:
                id_ = int(series[index]["target"].split('"')[1].split(".")[2])
                ids_data[id_] = index
            except Exception:
                pass

        return ids_data

    @swagger_auto_schema(
        query_serializer=MetricsQueryRangeInputSLZ(),
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
        step = smart_time_range.get_interval()

        metrics_name = data["metrics"]
        metrics = MetricsRangeFactory.create_metrics(MetricsRangeEnum(metrics_name))

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

        series = [s for s in data.get("series", []) if s["target"].strip()]
        if series:
            data["series"] = series

            if metrics_name in ["ingress", "egress"]:
                ids_data = self.get_series_resource_id_index_map(series)

                if ids_data:
                    resources = Resource.objects.filter(id__in=ids_data.keys()).values("id", "name")
                    for obj in resources:
                        series[ids_data[obj["id"]]]["target"] = 'name="{}"'.format(obj["name"])

        return OKJsonResponse(data=data)


class QueryInstantApi(generics.ListAPIView):
    @swagger_auto_schema(
        query_serializer=MetricsQueryInstantInputSLZ(),
        responses={status.HTTP_200_OK: ""},
        operation_description="查询 metrics",
        tags=["WebAPI.Metrics"],
    )
    def get(self, request, *args, **kwargs):
        slz = MetricsQueryInstantInputSLZ(data=request.query_params)
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

        step = smart_time_range.get_interval()

        # 暂时只有总数和健康率，所以总数是必需需要计算的
        metrics = MetricsInstantFactory.create_metrics(MetricsInstantEnum.REQUESTS_TOTAL)
        requests_total_result = metrics.query_instant(
            gateway_name=request.gateway.name,
            stage_id=data.get("stage_id", 0),
            stage_name=stage_name,
            resource_id=data.get("resource_id", 0),
            resource_name=resource_name,
            start=time_start,
            end=time_end,
            step=step,
        )
        if requests_total_result.get("instant") != 0 and data["metrics"] == MetricsInstantEnum.HEALTH_RATE.value:
            health_rate_result = {}

            # 获取 500 状态码 数量以求健康率
            metrics = MetricsInstantFactory.create_metrics(MetricsInstantEnum.HEALTH_RATE)
            health_rate_data = metrics.query_instant(
                gateway_name=request.gateway.name,
                stage_id=data.get("stage_id", 0),
                stage_name=stage_name,
                resource_id=data.get("resource_id", 0),
                resource_name=resource_name,
                start=time_start,
                end=time_end,
                step=step,
            )

            # 健康率 = 1 - (500 状态码数量 / 请求总数)
            health_rate = 1 - (health_rate_data["instant"] / requests_total_result["instant"])
            percent = health_rate * 100
            # 保留2位小数
            health_rate_result["instant"] = f"{percent:.2f}"
            return OKJsonResponse(data=health_rate_result)

        return OKJsonResponse(data=requests_total_result)


class QuerySummaryApi(generics.ListAPIView):
    @swagger_auto_schema(
        query_serializer=MetricsQuerySummaryInputSLZ(),
        responses={status.HTTP_200_OK: ""},
        operation_description="查询请求总量/失败请求总量",
        tags=["WebAPI.Metrics"],
    )
    def get(self, request, *args, **kwargs):
        slz = MetricsQuerySummaryInputSLZ(data=request.query_params)
        slz.is_valid(raise_exception=True)
        data = slz.validated_data

        stage_name = Stage.objects.get_name(request.gateway.id, data["stage_id"])
        if not stage_name:
            raise Http404

        queryset = MetricsSummaryFactory(
            stage_name,
            data.get("resource_id", 0),
            data.get("bk_app_code"),
            data["metrics"],
            data["time_dimension"],
            data["time_start"],
            data["time_end"],
        ).queryset()
        datapoints = [[obj["count_sum"], obj["time_period"]] for obj in queryset.iterator(chunk_size=1000)]

        return OKJsonResponse(data={"series": {"datapoints": datapoints}})


class QuerySummaryExportApi(generics.CreateAPIView):
    @swagger_auto_schema(
        decorator=swagger_auto_schema(
            operation_description="请求总量/失败请求总量导出",
            request_body=MetricsQuerySummaryInputSLZ,
            responses={status.HTTP_200_OK: ""},
            tags=["WebAPI.Metrics"],
        ),
    )
    def get(self, request, *args, **kwargs):
        slz = MetricsQuerySummaryInputSLZ(data=request.query_params)
        slz.is_valid(raise_exception=True)
        data = slz.validated_data

        stage_name = Stage.objects.get_name(request.gateway.id, data["stage_id"])
        if not stage_name:
            raise Http404

        queryset = MetricsSummaryFactory(
            stage_name,
            data.get("resource_id", 0),
            data.get("bk_app_code"),
            data["metrics"],
            data["time_dimension"],
            data["time_start"],
            data["time_end"],
        ).queryset()

        content = self._get_csv_content(queryset)
        response = DownloadableResponse(content, filename=f"bk_apigw_metrics_{self.request.gateway.name}.csv")
        # use utf-8-sig for windows
        response.charset = "utf-8-sig" if "windows" in request.headers.get("User-Agent", "").lower() else "utf-8"

        return response

    def _get_csv_content(self, data: List[Any]) -> str:
        """
        将筛选出的权限数据，整理为 csv 格式内容
        """
        headers = [
            "time_period",
            "count_sum",
        ]
        header_row = {
            "time_period": _("日期"),
            "count_sum": _("请求总数"),
        }

        content = StringIO()
        io_csv = csv.DictWriter(content, fieldnames=headers, extrasaction="ignore")
        io_csv.writerow(header_row)
        io_csv.writerows(data)

        return content.getvalue()
