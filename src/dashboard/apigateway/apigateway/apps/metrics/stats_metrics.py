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

from django.conf import settings

from apigateway.apps.metrics.dimension_metrics import BasePrometheusMetrics
from apigateway.components.prometheus import prometheus_component


class BaseStatisticsMetrics(BasePrometheusMetrics):
    @abstractmethod
    def _get_query_promql(self, step: str):
        pass

    def query(self, time_: int, step: str):
        return prometheus_component.query(
            bk_biz_id=getattr(settings, "BCS_CLUSTER_BK_BIZ_ID", ""),
            promql=self._get_query_promql(step),
            time_=time_,
        )


class StatisticsAPIRequestMetrics(BaseStatisticsMetrics):
    def _get_query_promql(self, step):
        labels = self._get_labels_expression(
            [
                *self.default_labels,
            ]
        )
        return (
            f"sum(increase({self.metric_name_prefix}apigateway_api_requests_total{{"
            f"{labels}"
            f"}}[{step}])) by (api_name, stage_name, resource_name, proxy_error)"
        )


class StatisticsAPIRequestDurationMetrics(BaseStatisticsMetrics):
    def _get_query_promql(self, step):
        labels = self._get_labels_expression(
            [
                *self.default_labels,
            ]
        )
        return (
            f"sum(increase({self.metric_name_prefix}apigateway_api_request_duration_milliseconds_sum{{"
            f"{labels}"
            f"}}[{step}])) by (api_name, stage_name, resource_name)"
        )


class StatisticsAppRequestMetrics(BaseStatisticsMetrics):
    """
    根据网关、环境、资源，统计应用请求量
    """

    def _get_query_promql(self, step):
        labels = self._get_labels_expression(
            [
                *self.default_labels,
            ]
        )
        return (
            f"sum(increase({self.metric_name_prefix}apigateway_app_requests_total{{"
            f"{labels}"
            f"}}[{step}])) by (app_code, api_name, stage_name, resource_name)"
        )


class StatisticsAppRequestByResourceMetrics(BaseStatisticsMetrics):
    """
    根据网关、资源，统计应用请求量
    """

    def _get_query_promql(self, step):
        labels = self._get_labels_expression(
            [
                *self.default_labels,
            ]
        )
        return (
            f"sum(increase({self.metric_name_prefix}apigateway_app_requests_total{{"
            f"{labels}"
            f"}}[{step}])) by (app_code, api_name, resource_name)"
        )
