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

from apigateway.apps.metrics.constants import MetricsNumberEnum, MetricsRangeEnum
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


class Non200StatusMetrics(BaseMetrics):
    metrics = MetricsRangeEnum.NON_200_STATUS

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
            ]
        )
        return (
            f"topk(10, sum(increase({self.metric_name_prefix}apigateway_app_requests_total{{"
            f"{labels}"
            f"}}[{step}])) by (api_name, app_code))"
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
            f"}}[{step}])) by (resource_name, matched_uri))"
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
    metrics = MetricsNumberEnum.REQUESTS_TOTAL

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
    metrics = MetricsNumberEnum.HEALTH_RATE

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


class MetricsNumberFactory:
    # map: metrics -> metrics_class
    _registry: Dict[MetricsNumberEnum, Type[BaseMetrics]] = {}

    @classmethod
    def create_metrics(cls, metrics: MetricsNumberEnum) -> BaseMetrics:
        _class = cls._registry.get(metrics)
        if not _class:
            raise error_codes.INVALID_ARGUMENT.format(f"unsupported metrics={metrics.value}")
        return _class()

    @classmethod
    def register(cls, metrics_class: Type[BaseMetrics]):
        if not hasattr(metrics_class, "metrics") or not isinstance(metrics_class.metrics, MetricsNumberEnum):
            raise ValueError("metrics_class must have a 'metrics' ClassVar of type MetricsNumberEnum")
        cls._registry[metrics_class.metrics] = metrics_class


MetricsRangeFactory.register(RequestsMetrics)
MetricsRangeFactory.register(Non200StatusMetrics)
MetricsRangeFactory.register(AppRequestsMetrics)
MetricsRangeFactory.register(ResourceRequestsMetrics)
MetricsRangeFactory.register(ResponseTime90thMetrics)
MetricsRangeFactory.register(IngressMetrics)
MetricsRangeFactory.register(EgressMetrics)

MetricsNumberFactory.register(RequestsTotalMetrics)
MetricsNumberFactory.register(HealthRateMetrics)
