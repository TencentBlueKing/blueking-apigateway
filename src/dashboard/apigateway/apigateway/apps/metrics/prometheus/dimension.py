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
from abc import abstractmethod
from typing import Any, ClassVar, Dict, Optional, Type

from django.conf import settings
from django.db.models import Sum
from django.db.models.functions import TruncDate, TruncMonth, TruncWeek
from django.utils import timezone

from apigateway.apps.metrics.constants import (
    MetricsInstantEnum,
    MetricsRangeEnum,
    MetricsSummaryEnum,
    MetricsSummaryTimeDimensionEnum,
)
from apigateway.apps.metrics.models import StatisticsAppRequestByDay, StatisticsGatewayRequestByDay
from apigateway.common.error_codes import error_codes
from apigateway.components.prometheus import prometheus_component

from .base import BasePrometheusMetrics


class BaseMetrics(BasePrometheusMetrics):
    metrics: ClassVar[str]

    @abstractmethod
    def _get_query_promql(
        self,
        gateway_name: str,
        stage_name: str,
        step: str,
        stage_id: Optional[int],
        resource_id: Optional[int],
        resource_name: Optional[str],
    ) -> str:
        pass

    def query_range(
        self,
        gateway_name: str,
        stage_name: str,
        start: int,
        end: int,
        step: str,
        stage_id: Optional[int],
        resource_id: Optional[int],
        resource_name: Optional[str],
    ):
        # generate query expression
        promql = self._get_query_promql(gateway_name, stage_name, step, stage_id, resource_id, resource_name)

        # request prometheus http api to get metrics data
        return prometheus_component.query_range(
            bk_biz_id=getattr(settings, "BCS_CLUSTER_BK_BIZ_ID", ""),
            promql=promql,
            start=start,
            end=end,
            step=step,
        )

    def query_instant(
        self,
        gateway_name: str,
        stage_name: str,
        start: int,
        end: int,
        step: str,
        stage_id: Optional[int],
        resource_id: Optional[int],
        resource_name: Optional[str],
    ):
        # generate query expression
        promql = self._get_query_promql(gateway_name, stage_name, step, stage_id, resource_id, resource_name)
        result: Dict[str, Any] = {}
        data = prometheus_component.query_range(
            bk_biz_id=getattr(settings, "BCS_CLUSTER_BK_BIZ_ID", ""),
            promql=promql,
            start=start,
            end=end,
            step=step,
        )
        # 计算这段时间内的差值
        result_number = get_data_differ_number(data)
        result["instant"] = result_number

        return result


# 计算数据里的 datapoints 里的 最后一位的值 和 第一位的 差值 以获取时间段内的数量
def get_data_differ_number(data: dict) -> int:
    # 检查传入的数据是否为None或不是字典
    if data is None or not isinstance(data, dict):
        return 0

    if "data" in data:
        data = data["data"]

    # 检查'data'键和'series'列表的存在性和非空性
    # 返回的没有没有数据的情况是这样的 {"result": true, "code": 200, "message": "OK", "data": {"metrics": [], "series": []}}
    if isinstance(data, dict) and "series" in data and isinstance(data["series"], list) and len(data["series"]) > 0:
        # 获取'datapoints'列表
        datapoints = data["series"][0].get("datapoints", [])

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
            last_number = datapoints[-2][0] if last_value is None else last_value

            # 返回计算的差值，并确保结果是整数
            total = int(last_number) - int(first_number)
            return 0 if total < 0 else total

    # 如果没有有效数据，返回0
    return 0


class RequestsMetrics(BaseMetrics):
    metrics = MetricsRangeEnum.REQUESTS

    def _get_query_promql(
        self,
        gateway_name: str,
        stage_name: str,
        step: str,
        stage_id: Optional[int],
        resource_id: Optional[int],
        resource_name: Optional[str],
    ) -> str:
        labels = self._get_labels_expression(
            [
                *self.default_labels,
                ("api_name", "=", gateway_name),
                ("stage_name", "=", stage_name),
                ("resource_name", "=", resource_name),
            ]
        )
        return f"sum(increase({self.metric_name_prefix}apigateway_api_requests_total{{" f"{labels}" f"}}[{step}]))"


class Non20XStatusMetrics(BaseMetrics):
    metrics = MetricsRangeEnum.NON_20X_STATUS

    def _get_query_promql(
        self,
        gateway_name: str,
        stage_name: str,
        step: str,
        stage_id: Optional[int],
        resource_id: Optional[int],
        resource_name: Optional[str],
    ) -> str:
        labels = self._get_labels_expression(
            [
                *self.default_labels,
                ("api_name", "=", gateway_name),
                ("stage_name", "=", stage_name),
                ("resource_name", "=", resource_name),
                ("status", "=~", "3..|4..|5.."),
            ]
        )
        return (
            f"topk(10, sum(increase({self.metric_name_prefix}apigateway_api_requests_total{{"
            f"{labels}"
            f"}}[{step}])) by (status))"
        )


class AppRequestsMetrics(BaseMetrics):
    metrics = MetricsRangeEnum.APP_REQUESTS

    def _get_query_promql(
        self,
        gateway_name: str,
        stage_name: str,
        step: str,
        stage_id: Optional[int],
        resource_id: Optional[int],
        resource_name: Optional[str],
    ) -> str:
        labels = self._get_labels_expression(
            [
                *self.default_labels,
                ("api_name", "=", gateway_name),
                ("stage_name", "=", stage_name),
                ("resource_name", "=", resource_name),
            ]
        )
        return (
            f"topk(10, sum(increase({self.metric_name_prefix}apigateway_app_requests_total{{"
            f"{labels}"
            f"}}[{step}])) by (app_code))"
        )


class ResourceRequestsMetrics(BaseMetrics):
    metrics = MetricsRangeEnum.RESOURCE_REQUESTS

    def _get_query_promql(
        self,
        gateway_name: str,
        stage_name: str,
        step: str,
        stage_id: Optional[int],
        resource_id: Optional[int],
        resource_name: Optional[str],
    ) -> str:
        labels = self._get_labels_expression(
            [
                *self.default_labels,
                ("api_name", "=", gateway_name),
                ("stage_name", "=", stage_name),
                ("resource_name", "=", resource_name),
            ]
        )
        return (
            f"topk(10, sum(increase({self.metric_name_prefix}apigateway_api_requests_total{{"
            f"{labels}"
            f"}}[{step}])) by (resource_name))"
        )


class ResponseTime90thMetrics(BaseMetrics):
    metrics = MetricsRangeEnum.RESPONSE_TIME_90TH
    quantile = 0.9

    def _get_query_promql(
        self,
        gateway_name: str,
        stage_name: str,
        step: str,
        stage_id: Optional[int],
        resource_id: Optional[int],
        resource_name: Optional[str],
    ) -> str:
        labels = self._get_labels_expression(
            [
                *self.default_labels,
                ("api_name", "=", gateway_name),
                ("stage_name", "=", stage_name),
                ("resource_name", "=", resource_name),
            ]
        )
        return (
            f"histogram_quantile({self.quantile}, "
            f"sum(rate({self.metric_name_prefix}apigateway_api_request_duration_milliseconds_bucket{{"
            f"{labels}"
            f"}}[{step}])) by (le, resource_name))"
        )


class IngressMetrics(BaseMetrics):
    metrics = MetricsRangeEnum.INGRESS

    def _get_query_promql(
        self,
        gateway_name: str,
        stage_name: str,
        step: str,
        stage_id: Optional[int],
        resource_id: Optional[int],
        resource_name: Optional[str],
    ) -> str:
        # 因为route的参数结果不能使用self._get_labels_expression方法去去除空参数
        label_list = [
            *self.default_labels,
            ("type", "=", "ingress"),
            # service 的参数规则： 网关名称.环境名称.stage-环境ID
            ("service", "=", f"{gateway_name}.{stage_name}.stage-{stage_id}"),
        ]
        if resource_id:
            # route 的参数规则： 网关名称.环境名称.资源ID
            label_list.append(("route", "=", f"{gateway_name}.{stage_name}.{resource_id}"))
        labels = self._get_labels_expression(label_list)
        return (
            # 指标：bkmonitor:bk_apigateway_bandwidth
            f"topk(10, sum(increase({self.metric_name_prefix}bandwidth{{" f"{labels}" f"}}[{step}])) by (route))"
        )


class EgressMetrics(BaseMetrics):
    metrics = MetricsRangeEnum.EGRESS

    def _get_query_promql(
        self,
        gateway_name: str,
        stage_name: str,
        step: str,
        stage_id: Optional[int],
        resource_id: Optional[int],
        resource_name: Optional[str],
    ) -> str:
        # 因为route的参数结果不能使用self._get_labels_expression方法去去除空参数
        label_list = [
            *self.default_labels,
            ("type", "=", "egress"),
            # service 的参数规则： 网关名称.环境名称.stage-环境ID
            ("service", "=", f"{gateway_name}.{stage_name}.stage-{stage_id}"),
        ]
        if resource_id:
            # route 的参数规则： 网关名称.环境名称.资源ID
            label_list.append(("route", "=", f"{gateway_name}.{stage_name}.{resource_id}"))
        labels = self._get_labels_expression(label_list)

        return (
            # 指标：bkmonitor:bk_apigateway_bandwidth
            f"topk(10, sum(increase({self.metric_name_prefix}bandwidth{{" f"{labels}" f"}}[{step}])) by (route))"
        )


class RequestsTotalMetrics(BaseMetrics):
    metrics = MetricsInstantEnum.REQUESTS_TOTAL

    def _get_query_promql(
        self,
        gateway_name: str,
        stage_name: str,
        step: str,
        stage_id: Optional[int],
        resource_id: Optional[int],
        resource_name: Optional[str],
    ) -> str:
        labels = self._get_labels_expression(
            [
                *self.default_labels,
                ("api_name", "=", gateway_name),
                ("stage_name", "=", stage_name),
                ("resource_name", "=", resource_name),
            ]
        )
        return f"sum({self.metric_name_prefix}apigateway_api_requests_total{{{labels}}})"


# 计算健康率
class HealthRateMetrics(BaseMetrics):
    metrics = MetricsInstantEnum.HEALTH_RATE

    def _get_query_promql(
        self,
        gateway_name: str,
        stage_name: str,
        step: str,
        stage_id: Optional[int],
        resource_id: Optional[int],
        resource_name: Optional[str],
    ) -> str:
        labels = self._get_labels_expression(
            [
                *self.default_labels,
                ("api_name", "=", gateway_name),
                ("stage_name", "=", stage_name),
                ("resource_name", "=", resource_name),
                ("status", "=~", "5.."),
                # ("proxy_error", "=", "1"),
            ]
        )
        return f"sum({self.metric_name_prefix}apigateway_api_requests_total{{{labels}}})"


class MetricsRangeFactory:
    # map: metrics -> metrics_class
    _registry: Dict[MetricsRangeEnum, Type[BaseMetrics]] = {}

    @classmethod
    def create_metrics(cls, metrics: MetricsRangeEnum) -> BaseMetrics:
        _class = cls._registry.get(metrics)
        if not _class:
            raise error_codes.INVALID_ARGUMENT.format(f"unsupported metrics={metrics.value}")
        return _class()

    @classmethod
    def register(cls, metrics_class: Type[BaseMetrics]):
        if not hasattr(metrics_class, "metrics") or not isinstance(metrics_class.metrics, MetricsRangeEnum):
            raise ValueError("metrics_class must have a 'metrics' ClassVar of type MetricsRangeEnum")
        cls._registry[metrics_class.metrics] = metrics_class


class MetricsInstantFactory:
    # map: metrics -> metrics_class
    _registry: Dict[MetricsInstantEnum, Type[BaseMetrics]] = {}

    @classmethod
    def create_metrics(cls, metrics: MetricsInstantEnum) -> BaseMetrics:
        _class = cls._registry.get(metrics)
        if not _class:
            raise error_codes.INVALID_ARGUMENT.format(f"unsupported metrics={metrics.value}")
        return _class()

    @classmethod
    def register(cls, metrics_class: Type[BaseMetrics]):
        if not hasattr(metrics_class, "metrics") or not isinstance(metrics_class.metrics, MetricsInstantEnum):
            raise ValueError("metrics_class must have a 'metrics' ClassVar of type MetricsInstantEnum")
        cls._registry[metrics_class.metrics] = metrics_class


class MetricsSummaryFactory:
    TRUNC_FUNC_MAP = {
        MetricsSummaryTimeDimensionEnum.DAY.value: TruncDate,
        MetricsSummaryTimeDimensionEnum.WEEK.value: TruncWeek,
        MetricsSummaryTimeDimensionEnum.MONTH.value: TruncMonth,
    }

    COUNT_FIELD_MAP = {
        MetricsSummaryEnum.REQUESTS_TOTAL.value: "total_count",
        MetricsSummaryEnum.REQUESTS_FAILED_TOTAL.value: "failed_count",
    }

    def __init__(
        self,
        stage_name: str,
        resource_id: Optional[int],
        bk_app_code: Optional[str],
        metrics: str,
        time_dimension: str,
        time_start: int,
        time_end: int,
    ):
        self.stage_name = stage_name
        self.resource_id = resource_id
        self.bk_app_code = bk_app_code
        self.metrics = metrics
        self.time_dimension = time_dimension
        self.time_start = time_start
        self.time_end = time_end

    def _build_query_params(self):
        query_params = {
            "stage_name": self.stage_name,
            "start_time__gte": timezone.datetime.fromtimestamp(self.time_start),
            "end_time__lte": timezone.datetime.fromtimestamp(self.time_end),
        }

        if self.bk_app_code:
            query_params["bk_app_code"] = self.bk_app_code
        if self.resource_id:
            query_params["resource_id"] = self.resource_id

        return query_params

    def queryset(self):
        # 查询参数
        query_params = self._build_query_params()
        # 时间维度
        trunc_func = self.TRUNC_FUNC_MAP.get(self.time_dimension, TruncDate)
        # 统计字段
        count_field = self.COUNT_FIELD_MAP.get(self.metrics, "total_count")
        # 查询 model
        model = StatisticsAppRequestByDay if self.bk_app_code else StatisticsGatewayRequestByDay

        return (
            model.objects.filter(**query_params)
            .annotate(time_period=trunc_func("end_time"))
            .values("time_period")
            .annotate(count_sum=Sum(count_field))
            .order_by("time_period")
        )


MetricsRangeFactory.register(RequestsMetrics)
MetricsRangeFactory.register(Non20XStatusMetrics)
MetricsRangeFactory.register(AppRequestsMetrics)
MetricsRangeFactory.register(ResourceRequestsMetrics)
MetricsRangeFactory.register(ResponseTime90thMetrics)
MetricsRangeFactory.register(IngressMetrics)
MetricsRangeFactory.register(EgressMetrics)

MetricsInstantFactory.register(RequestsTotalMetrics)
MetricsInstantFactory.register(HealthRateMetrics)
