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
from abc import ABC, abstractmethod
from typing import Dict, Optional, Text

from django.conf import settings

from apigateway.common.error_codes import error_codes

from .constants import JOB_NAME, DimensionEnum, MetricsEnum


class BasePrometheusMetrics(ABC):
    job_name = JOB_NAME
    default_labels = getattr(settings, "PROMETHEUS_DEFAULT_LABELS", [])
    metric_name_prefix = getattr(settings, "PROMETHEUS_METRIC_NAME_PREFIX", "")

    def _get_labels_expression(self, labels):
        return ", ".join(
            [f'{label}{expression}"{value}"' for label, expression, value in labels if value not in [None, ""]]
        )


class BaseDimensionMetrics(BasePrometheusMetrics):
    @abstractmethod
    def get_query_expression(self, gateway_id: int, stage_name: str, resource_id: Optional[int], step: str) -> str:
        pass


class DimensionMetricsManager:
    # map: dimension -> metrics -> dimension_metrics_class
    _registry: Dict[Text, Dict[Text, BaseDimensionMetrics]] = {}

    @classmethod
    def create_dimension_metrics(cls, dimension, metrics):
        _class = cls._registry.get(dimension, {}).get(metrics)
        if not _class:
            raise error_codes.INVALID_ARGS.format(f"unsupported grant_dimension={dimension}, metrics={metrics}")
        return _class()

    @classmethod
    def register(cls, dimension_metrics_class):
        _class = dimension_metrics_class
        cls._registry.setdefault(_class.dimension, {})
        cls._registry[_class.dimension][_class.metrics] = dimension_metrics_class


class RequestsMetrics(BaseDimensionMetrics):
    dimension = DimensionEnum.ALL.value
    metrics = MetricsEnum.REQUESTS.value

    def get_query_expression(self, gateway_id: int, stage_name: str, resource_id: Optional[int], step: str) -> str:
        labels = self._get_labels_expression(
            [
                *self.default_labels,
                ("job", "=", self.job_name),
                ("api", "=", gateway_id),
                ("stage", "=", stage_name),
                ("resource", "=", resource_id),
            ]
        )
        return f"sum(increase({self.metric_name_prefix}apigateway_api_requests_total{{" f"{labels}" f"}}[{step}]))"


DimensionMetricsManager.register(RequestsMetrics)


class FailedRequestsMetrics(BaseDimensionMetrics):
    dimension = DimensionEnum.ALL.value
    metrics = MetricsEnum.FAILED_REQUESTS.value

    def get_query_expression(self, gateway_id: int, stage_name: str, resource_id: Optional[int], step: str) -> str:
        labels = self._get_labels_expression(
            [
                *self.default_labels,
                ("job", "=", self.job_name),
                ("api", "=", gateway_id),
                ("stage", "=", stage_name),
                ("resource", "=", resource_id),
                ("proxy_error", "=", "1"),
            ]
        )
        return f"sum(increase({self.metric_name_prefix}apigateway_api_requests_total{{" f"{labels}" f"}}[{step}]))"


DimensionMetricsManager.register(FailedRequestsMetrics)


class BaseResponseTimePercentileMetrics(BaseDimensionMetrics):
    quantile = 1.0

    def get_query_expression(self, gateway_id: int, stage_name: str, resource_id: Optional[int], step: str) -> str:
        labels = self._get_labels_expression(
            [
                *self.default_labels,
                ("job", "=", self.job_name),
                ("api", "=", gateway_id),
                ("stage", "=", stage_name),
                ("resource", "=", resource_id),
            ]
        )
        return (
            f"histogram_quantile({self.quantile}, "
            f"sum(rate({self.metric_name_prefix}apigateway_api_request_duration_milliseconds_bucket{{"
            f"{labels}"
            f"}}[{step}])) by (le, api))"
        )


class ResponseTime95thMetrics(BaseResponseTimePercentileMetrics):
    dimension = DimensionEnum.ALL.value
    metrics = MetricsEnum.RESPONSE_TIME_95TH.value
    quantile = 0.95


DimensionMetricsManager.register(ResponseTime95thMetrics)


class ResponseTime90thMetrics(BaseResponseTimePercentileMetrics):
    dimension = DimensionEnum.ALL.value
    metrics = MetricsEnum.RESPONSE_TIME_90TH.value
    quantile = 0.90


DimensionMetricsManager.register(ResponseTime90thMetrics)


class ResponseTime80thMetrics(BaseResponseTimePercentileMetrics):
    dimension = DimensionEnum.ALL.value
    metrics = MetricsEnum.RESPONSE_TIME_80TH.value
    quantile = 0.80


DimensionMetricsManager.register(ResponseTime80thMetrics)


class ResponseTime50thMetrics(BaseResponseTimePercentileMetrics):
    dimension = DimensionEnum.ALL.value
    metrics = MetricsEnum.RESPONSE_TIME_50TH.value
    quantile = 0.50


DimensionMetricsManager.register(ResponseTime50thMetrics)


class ResourceRequestsMetrics(BaseDimensionMetrics):
    dimension = DimensionEnum.RESOURCE.value
    metrics = MetricsEnum.REQUESTS.value

    def get_query_expression(self, gateway_id: int, stage_name: str, resource_id: Optional[int], step: str) -> str:
        labels = self._get_labels_expression(
            [
                *self.default_labels,
                ("job", "=", self.job_name),
                ("api", "=", gateway_id),
                ("stage", "=", stage_name),
                ("resource", "=", resource_id),
            ]
        )
        return (
            f"topk(10, sum(increase({self.metric_name_prefix}apigateway_api_requests_total{{"
            f"{labels}"
            f"}}[{step}])) by (api, resource, path))"
        )


DimensionMetricsManager.register(ResourceRequestsMetrics)


class ResourceFailedRequestsMetrics(BaseDimensionMetrics):
    dimension = DimensionEnum.RESOURCE.value
    metrics = MetricsEnum.FAILED_REQUESTS.value

    def get_query_expression(self, gateway_id: int, stage_name: str, resource_id: Optional[int], step: str) -> str:
        labels = self._get_labels_expression(
            [
                *self.default_labels,
                ("job", "=", self.job_name),
                ("api", "=", gateway_id),
                ("stage", "=", stage_name),
                ("resource", "=", resource_id),
                ("proxy_error", "=", "1"),
            ]
        )
        return (
            f"topk(10, sum(increase({self.metric_name_prefix}apigateway_api_requests_total{{"
            f"{labels}"
            f"}}[{step}])) by (api, resource, path))"
        )


DimensionMetricsManager.register(ResourceFailedRequestsMetrics)


class AppRequestsMetrics(BaseDimensionMetrics):
    dimension = DimensionEnum.APP.value
    metrics = MetricsEnum.REQUESTS.value

    def get_query_expression(self, gateway_id: int, stage_name: str, resource_id: Optional[int], step: str) -> str:
        labels = self._get_labels_expression(
            [
                *self.default_labels,
                ("job", "=", self.job_name),
                ("api", "=", gateway_id),
                ("stage", "=", stage_name),
                ("resource", "=", resource_id),
            ]
        )
        return (
            f"topk(10, sum(increase({self.metric_name_prefix}apigateway_app_requests_total{{"
            f"{labels}"
            f"}}[{step}])) by (api, app_code))"
        )


DimensionMetricsManager.register(AppRequestsMetrics)


class ResourceNon200StatusRequestsMetrics(BaseDimensionMetrics):
    dimension = DimensionEnum.RESOURCE_NON200_STATUS.value
    metrics = MetricsEnum.REQUESTS.value

    def get_query_expression(self, gateway_id: int, stage_name: str, resource_id: Optional[int], step: str) -> str:
        labels = self._get_labels_expression(
            [
                *self.default_labels,
                ("job", "=", self.job_name),
                ("api", "=", gateway_id),
                ("stage", "=", stage_name),
                ("status", "!=", "200"),
                ("resource", "=", resource_id),
            ]
        )
        return (
            f"topk(10, sum(increase({self.metric_name_prefix}apigateway_api_requests_total{{"
            f"{labels}"
            f"}}[{step}])) by (api, resource, path, status))"
        )


DimensionMetricsManager.register(ResourceNon200StatusRequestsMetrics)
