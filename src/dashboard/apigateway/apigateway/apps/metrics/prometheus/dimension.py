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

from apigateway.apps.metrics.constants import MetricsEnum
from apigateway.common.error_codes import error_codes
from apigateway.components.prometheus import prometheus_component

from .base import BasePrometheusMetrics


class BaseMetrics(BasePrometheusMetrics):
    metrics: ClassVar[MetricsEnum]

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


class RequestsMetrics(BaseMetrics):
    metrics = MetricsEnum.REQUESTS

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


class RequestsTotalMetrics(BaseMetrics):
    metrics = MetricsEnum.REQUESTS_TOTAL

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
        return f"count({self.metric_name_prefix}apigateway_api_requests_total{{" f"{labels}" f"}}[{step}])"


class Non200StatusMetrics(BaseMetrics):
    metrics = MetricsEnum.NON_200_STATUS

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
                ("status", "!=", "200"),
            ]
        )
        return (
            f"topk(10, sum(increase({self.metric_name_prefix}apigateway_api_requests_total{{"
            f"{labels}"
            f"}}[{step}])) by (api_name, status))"
        )


class AppRequestsMetrics(BaseMetrics):
    metrics = MetricsEnum.APP_REQUESTS

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
            f"}}[{step}])) by (api_name, app_code))"
        )


class ResourceRequestsMetrics(BaseMetrics):
    metrics = MetricsEnum.RESOURCE_REQUESTS

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
            f"}}[{step}])) by (api_name, resource_name, matched_uri))"
        )


class BaseResponseTimePercentileMetrics(BaseMetrics):
    quantile = 1.0

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
            f"}}[{step}])) by (le, api_name))"
        )


class ResponseTime50thMetrics(BaseResponseTimePercentileMetrics):
    metrics = MetricsEnum.RESPONSE_TIME_50TH
    quantile = 0.50


class ResponseTime80thMetrics(BaseResponseTimePercentileMetrics):
    metrics = MetricsEnum.RESPONSE_TIME_80TH
    quantile = 0.80


class ResponseTime90thMetrics(BaseResponseTimePercentileMetrics):
    metrics = MetricsEnum.RESPONSE_TIME_90TH
    quantile = 0.90


class IngressMetrics(BaseMetrics):
    metrics = MetricsEnum.INGRESS

    def _get_query_promql(
        self,
        gateway_name: str,
        stage_name: str,
        step: str,
        stage_id: Optional[int],
        resource_id: Optional[int],
        resource_name: Optional[str],
    ) -> str:
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
            f"sum(increase({self.metric_name_prefix}bandwidth{{" f"{labels}" f"}}[{step}])) by (route)"
        )


class EgressMetrics(BaseMetrics):
    metrics = MetricsEnum.EGRESS

    def _get_query_promql(
        self,
        gateway_name: str,
        stage_name: str,
        step: str,
        stage_id: Optional[int],
        resource_id: Optional[int],
        resource_name: Optional[str],
    ) -> str:
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
            f"sum(increase({self.metric_name_prefix}bandwidth{{" f"{labels}" f"}}[{step}])) by (route)"
        )


class MetricsFactory:
    # map: metrics -> metrics_class
    _registry: Dict[MetricsEnum, Type[BaseMetrics]] = {}

    @classmethod
    def create_metrics(cls, metrics: MetricsEnum) -> BaseMetrics:
        _class = cls._registry.get(metrics)
        if not _class:
            raise error_codes.INVALID_ARGUMENT.format(f"unsupported metrics={metrics.value}")
        return _class()

    @classmethod
    def register(cls, metrics_class: Type[BaseMetrics]):
        if not hasattr(metrics_class, "metrics") or not isinstance(metrics_class.metrics, MetricsEnum):
            raise ValueError("metrics_class must have a 'metrics' ClassVar of type MetricsEnum")
        cls._registry[metrics_class.metrics] = metrics_class


MetricsFactory.register(RequestsMetrics)
MetricsFactory.register(RequestsTotalMetrics)
MetricsFactory.register(Non200StatusMetrics)
MetricsFactory.register(AppRequestsMetrics)
MetricsFactory.register(ResourceRequestsMetrics)
MetricsFactory.register(ResponseTime50thMetrics)
MetricsFactory.register(ResponseTime80thMetrics)
MetricsFactory.register(ResponseTime90thMetrics)
MetricsFactory.register(IngressMetrics)
MetricsFactory.register(EgressMetrics)
