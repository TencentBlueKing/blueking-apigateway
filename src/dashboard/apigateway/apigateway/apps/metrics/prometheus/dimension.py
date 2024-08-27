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
from typing import ClassVar, Dict, Optional, Type

from django.conf import settings

from apigateway.apps.metrics.constants import DimensionEnum, MetricsEnum
from apigateway.common.error_codes import error_codes
from apigateway.components.prometheus import prometheus_component

from .base import BasePrometheusMetrics


class BaseDimensionMetrics(BasePrometheusMetrics):
    dimension: ClassVar[DimensionEnum]
    metrics: ClassVar[MetricsEnum]

    @abstractmethod
    def _get_query_promql(
        self, gateway_name: str, stage_id: int, stage_name: str, resource_name: Optional[str], step: str
    ) -> str:
        pass

    def query_range(
        self,
        gateway_name: str,
        stage_id: int,
        stage_name: str,
        resource_name: Optional[str],
        start: int,
        end: int,
        step: str,
    ):
        # generate query expression
        promql = self._get_query_promql(gateway_name, stage_id, stage_name, resource_name, step)

        # request prometheus http api to get metrics data
        return prometheus_component.query_range(
            bk_biz_id=getattr(settings, "BCS_CLUSTER_BK_BIZ_ID", ""),
            promql=promql,
            start=start,
            end=end,
            step=step,
        )


class RequestsMetrics(BaseDimensionMetrics):
    dimension = DimensionEnum.ALL
    metrics = MetricsEnum.REQUESTS

    def _get_query_promql(
        self, gateway_name: str, stage_id: int, stage_name: str, resource_name: Optional[str], step: str
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


class RequestNumberMetrics(BaseDimensionMetrics):
    dimension = DimensionEnum.ALL
    metrics = MetricsEnum.REQUEST_NUMBER

    def _get_query_promql(
        self, gateway_name: str, stage_id: int, stage_name: str, resource_name: Optional[str], step: str
    ) -> str:
        labels = self._get_labels_expression(
            [
                *self.default_labels,
                ("api_name", "=", gateway_name),
                ("stage_name", "=", stage_name),
                ("resource_name", "=", resource_name),
            ]
        )
        return f"count(increase({self.metric_name_prefix}apigateway_api_requests_total{{" f"{labels}" f"}}[{step}]))"


class BaseResponseTimePercentileMetrics(BaseDimensionMetrics):
    quantile = 1.0

    def _get_query_promql(
        self, gateway_name: str, stage_id: int, stage_name: str, resource_name: Optional[str], step: str
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
            f"}}[{step}])) by (le, api_name))"
        )


class ResponseTime90thMetrics(BaseResponseTimePercentileMetrics):
    dimension = DimensionEnum.ALL
    metrics = MetricsEnum.RESPONSE_TIME_90TH
    quantile = 0.90


class ResponseTime80thMetrics(BaseResponseTimePercentileMetrics):
    dimension = DimensionEnum.ALL
    metrics = MetricsEnum.RESPONSE_TIME_80TH
    quantile = 0.80


class ResponseTime50thMetrics(BaseResponseTimePercentileMetrics):
    dimension = DimensionEnum.ALL
    metrics = MetricsEnum.RESPONSE_TIME_50TH
    quantile = 0.50


class ResourceRequestsMetrics(BaseDimensionMetrics):
    dimension = DimensionEnum.RESOURCE
    metrics = MetricsEnum.REQUESTS

    def _get_query_promql(
        self, gateway_name: str, stage_id: int, stage_name: str, resource_name: Optional[str], step: str
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
            f"}}[{step}])) by (api_name, resource_name, matched_uri))"
        )


class AppRequestsMetrics(BaseDimensionMetrics):
    dimension = DimensionEnum.APP
    metrics = MetricsEnum.REQUESTS

    def _get_query_promql(
        self, gateway_name: str, stage_id: int, stage_name: str, resource_name: Optional[str], step: str
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
            f"}}[{step}])) by (api_name, app_code))"
        )


class Non200StatusRequestsMetrics(BaseDimensionMetrics):
    dimension = DimensionEnum.RESOURCE_NON200_STATUS
    metrics = MetricsEnum.REQUESTS

    def _get_query_promql(
        self, gateway_name: str, stage_id: int, stage_name: str, resource_name: Optional[str], step: str
    ) -> str:
        labels = self._get_labels_expression(
            [
                *self.default_labels,
                ("api_name", "=", gateway_name),
                ("stage_name", "=", stage_name),
                ("resource_name", "=", resource_name),
                ("status", "!=", "200"),
            ]
        )
        return (
            f"topk(10, sum(increase({self.metric_name_prefix}apigateway_api_requests_total{{"
            f"{labels}"
            f"}}[{step}])) by (api_name, resource_name, matched_uri, status))"
        )


class IngressRequestsSpaceMetrics(BaseDimensionMetrics):
    dimension = DimensionEnum.ALL
    metrics = MetricsEnum.INGRESS_SPACE

    def _get_query_promql(
        self, gateway_name: str, stage_id: int, stage_name: str, resource_name: Optional[str], step: str
    ) -> str:
        labels = self._get_labels_expression(
            [
                *self.default_labels,
                ("type", "=", "egress"),
                # 环境参数 prod 待修改
                ("service", "=", gateway_name + "." + stage_name + ".stage-" + str(stage_id)),
            ]
        )
        return (
            f"topk(10, sum(increase({self.metric_name_prefix}apigateway_bandwidth{{"
            f"{labels}"
            f"}}[{step}])) by (route))"
        )


class EgressRequestsSpaceMetrics(BaseDimensionMetrics):
    dimension = DimensionEnum.ALL
    metrics = MetricsEnum.INGRESS_SPACE

    def _get_query_promql(
        self, gateway_name: str, stage_id: int, stage_name: str, resource_name: Optional[str], step: str
    ) -> str:
        labels = self._get_labels_expression(
            [
                *self.default_labels,
                ("type", "=", "egress"),
                # 环境参数 prod 待修改
                ("service", "=", gateway_name + "." + stage_name + ".stage-" + str(stage_id)),
            ]
        )
        # 底下的 apigateway_bandwidth 待自测验证是否能通
        return (
            f"topk(10, sum(increase({self.metric_name_prefix}apigateway_bandwidth{{"
            f"{labels}"
            f"}}[{step}])) by (route))"
        )


class DimensionMetricsFactory:
    # map: dimension -> metrics -> dimension_metrics_class
    _registry: Dict[DimensionEnum, Dict[MetricsEnum, Type[BaseDimensionMetrics]]] = {}

    @classmethod
    def create_dimension_metrics(cls, dimension: DimensionEnum, metrics: MetricsEnum) -> BaseDimensionMetrics:
        _class = cls._registry.get(dimension, {}).get(metrics)
        if not _class:
            raise error_codes.INVALID_ARGUMENT.format(
                f"unsupported dimension={dimension.value}, metrics={metrics.value}"
            )
        return _class()

    @classmethod
    def register(cls, dimension_metrics_class: Type[BaseDimensionMetrics]):
        _class = dimension_metrics_class
        cls._registry.setdefault(_class.dimension, {})
        cls._registry[_class.dimension][_class.metrics] = dimension_metrics_class


DimensionMetricsFactory.register(RequestNumberMetrics)
DimensionMetricsFactory.register(RequestsMetrics)
DimensionMetricsFactory.register(Non200StatusRequestsMetrics)
DimensionMetricsFactory.register(AppRequestsMetrics)
DimensionMetricsFactory.register(ResourceRequestsMetrics)
DimensionMetricsFactory.register(ResponseTime50thMetrics)
DimensionMetricsFactory.register(ResponseTime80thMetrics)
DimensionMetricsFactory.register(ResponseTime90thMetrics)
DimensionMetricsFactory.register(IngressRequestsSpaceMetrics)
DimensionMetricsFactory.register(EgressRequestsSpaceMetrics)
