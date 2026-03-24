# -*- coding: utf-8 -*-
#
# TencentBlueKing is pleased to support the open source community by making
# 蓝鲸智云 - API 网关 (BlueKing - APIGateway) available.
# Copyright (C) 2025 Tencent. All rights reserved.
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
from typing import ClassVar, Dict, Optional, Type

from django.conf import settings

from apigateway.apps.mcp_server.metrics_constants import (
    MCPServerMetricsInstantEnum,
    MCPServerMetricsRangeEnum,
)
from apigateway.common.error_codes import error_codes
from apigateway.components.bkmonitor import query_range

from .base import BasePrometheusMetrics
from .dimension import get_data_differ_number


class BaseMCPServerMetrics(BasePrometheusMetrics):
    """Base class for MCP Server Prometheus metrics queries.

    Uses mcp-proxy's metric names (with configurable prefix, default "bk_apigateway_"):
    - {prefix}mcp_proxy_mcp_requests_total (counter)
    - {prefix}mcp_proxy_mcp_request_duration_milliseconds (histogram)
    - {prefix}mcp_proxy_mcp_tool_calls_total (counter)
    - {prefix}mcp_proxy_mcp_sessions_active (gauge)
    - {prefix}mcp_proxy_mcp_errors_total (counter)
    """

    metrics: ClassVar[str]

    def _get_mcp_labels_expression(
        self,
        gateway_name: str,
        mcp_server_name: Optional[str] = None,
        app_code: Optional[str] = None,
        extra_labels: Optional[list] = None,
    ) -> str:
        labels = [
            *self.default_labels,
            ("gateway_name", "=", gateway_name),
        ]
        if mcp_server_name:
            labels.append(("mcp_server_name", "=", mcp_server_name))
        if app_code:
            labels.append(("app_code", "=", app_code))
        if extra_labels:
            labels.extend(extra_labels)
        return self._get_labels_expression(labels)

    def query_range(
        self,
        gateway_name: str,
        mcp_server_name: Optional[str],
        app_code: Optional[str],
        start: int,
        end: int,
        step: str,
    ):
        promql = self._get_query_promql(gateway_name, mcp_server_name, app_code, step)
        return query_range(
            bk_biz_id=getattr(settings, "BCS_CLUSTER_BK_BIZ_ID", ""),
            promql=promql,
            start=start,
            end=end,
            step=step,
        )

    def query_instant(
        self,
        gateway_name: str,
        mcp_server_name: Optional[str],
        app_code: Optional[str],
        start: int,
        end: int,
        step: str,
    ):
        promql = self._get_query_promql(gateway_name, mcp_server_name, app_code, step)
        data = query_range(
            bk_biz_id=getattr(settings, "BCS_CLUSTER_BK_BIZ_ID", ""),
            promql=promql,
            start=start,
            end=end,
            step=step,
        )
        result_number = get_data_differ_number(data)
        return {"instant": result_number}

    def _get_query_promql(
        self,
        gateway_name: str,
        mcp_server_name: Optional[str],
        app_code: Optional[str],
        step: str,
    ) -> str:
        raise NotImplementedError


# ==================== Range Metrics ====================


class MCPServerRequestsMetrics(BaseMCPServerMetrics):
    """Total MCP requests trend (sum across all methods)"""

    metrics = MCPServerMetricsRangeEnum.REQUESTS

    def _get_query_promql(self, gateway_name, mcp_server_name, app_code, step):
        labels = self._get_mcp_labels_expression(gateway_name, mcp_server_name, app_code)
        return f"sum(increase({self.metric_name_prefix}mcp_proxy_mcp_requests_total{{{labels}}}[{step}]))"


class MCPServerRequests2XXMetrics(BaseMCPServerMetrics):
    """2XX status requests trend"""

    metrics = MCPServerMetricsRangeEnum.REQUESTS_2XX

    def _get_query_promql(self, gateway_name, mcp_server_name, app_code, step):
        labels = self._get_mcp_labels_expression(
            gateway_name,
            mcp_server_name,
            app_code,
            extra_labels=[("error", "=", "0")],
        )
        return f"sum(increase({self.metric_name_prefix}mcp_proxy_mcp_requests_total{{{labels}}}[{step}]))"


class MCPServerNon2XXStatusMetrics(BaseMCPServerMetrics):
    """Non-2XX status requests trend, grouped by error_code"""

    metrics = MCPServerMetricsRangeEnum.NON_2XX_STATUS

    def _get_query_promql(self, gateway_name, mcp_server_name, app_code, step):
        labels = self._get_mcp_labels_expression(
            gateway_name,
            mcp_server_name,
            app_code,
            extra_labels=[("error", "=", "1")],
        )
        return (
            f"topk(10, sum(increase({self.metric_name_prefix}mcp_proxy_mcp_requests_total"
            f"{{{labels}}}[{step}])) by (error_code))"
        )


class MCPServerAppRequestsMetrics(BaseMCPServerMetrics):
    """Requests grouped by app_code"""

    metrics = MCPServerMetricsRangeEnum.APP_REQUESTS

    def _get_query_promql(self, gateway_name, mcp_server_name, app_code, step):
        labels = self._get_mcp_labels_expression(gateway_name, mcp_server_name, app_code)
        return (
            f"topk(10, sum(increase({self.metric_name_prefix}mcp_proxy_mcp_requests_total"
            f"{{{labels}}}[{step}])) by (app_code))"
        )


class MCPServerToolRequestsMetrics(BaseMCPServerMetrics):
    """Requests grouped by tool_name (MCP tools/call)"""

    metrics = MCPServerMetricsRangeEnum.TOOL_REQUESTS

    def _get_query_promql(self, gateway_name, mcp_server_name, app_code, step):
        labels = self._get_mcp_labels_expression(gateway_name, mcp_server_name, app_code)
        return (
            f"topk(10, sum(increase({self.metric_name_prefix}mcp_proxy_mcp_tool_calls_total"
            f"{{{labels}}}[{step}])) by (tool_name))"
        )


class MCPServerResponseTime95thMetrics(BaseMCPServerMetrics):
    """P95 response time distribution"""

    metrics = MCPServerMetricsRangeEnum.RESPONSE_TIME_95TH

    def _get_query_promql(self, gateway_name, mcp_server_name, app_code, step):
        labels = self._get_mcp_labels_expression(gateway_name, mcp_server_name, app_code)
        return (
            f"histogram_quantile(0.95, "
            f"sum(rate({self.metric_name_prefix}mcp_proxy_mcp_request_duration_milliseconds_bucket"
            f"{{{labels}}}[{step}])) by (le, method))"
        )


class MCPServerMethodRequestsMetrics(BaseMCPServerMetrics):
    """Requests grouped by MCP method (initialize, tools/call, tools/list, etc.)"""

    metrics = MCPServerMetricsRangeEnum.METHOD_REQUESTS

    def _get_query_promql(self, gateway_name, mcp_server_name, app_code, step):
        labels = self._get_mcp_labels_expression(gateway_name, mcp_server_name, app_code)
        return (
            f"topk(10, sum(increase({self.metric_name_prefix}mcp_proxy_mcp_requests_total"
            f"{{{labels}}}[{step}])) by (method))"
        )


# ==================== Instant Metrics ====================


class MCPServerRequestsTotalMetrics(BaseMCPServerMetrics):
    """Total request count (instant value)"""

    metrics = MCPServerMetricsInstantEnum.REQUESTS_TOTAL

    def _get_query_promql(self, gateway_name, mcp_server_name, app_code, step):
        labels = self._get_mcp_labels_expression(gateway_name, mcp_server_name, app_code)
        return f"sum({self.metric_name_prefix}mcp_proxy_mcp_requests_total{{{labels}}})"


class MCPServerNon2XXTotalMetrics(BaseMCPServerMetrics):
    """Non-2XX total request count (instant value)"""

    metrics = MCPServerMetricsInstantEnum.NON_2XX_TOTAL

    def _get_query_promql(self, gateway_name, mcp_server_name, app_code, step):
        labels = self._get_mcp_labels_expression(
            gateway_name,
            mcp_server_name,
            app_code,
            extra_labels=[("error", "=", "1")],
        )
        return f"sum({self.metric_name_prefix}mcp_proxy_mcp_requests_total{{{labels}}})"


# ==================== Factories ====================


class MCPServerMetricsRangeFactory:
    _registry: Dict[MCPServerMetricsRangeEnum, Type[BaseMCPServerMetrics]] = {}

    @classmethod
    def create_metrics(cls, metrics: MCPServerMetricsRangeEnum) -> BaseMCPServerMetrics:
        _class = cls._registry.get(metrics)
        if not _class:
            raise error_codes.INVALID_ARGUMENT.format(f"unsupported mcp server metrics={metrics.value}")
        return _class()

    @classmethod
    def register(cls, metrics_class: Type[BaseMCPServerMetrics]):
        if not hasattr(metrics_class, "metrics"):
            raise ValueError("metrics_class must have a 'metrics' ClassVar")
        cls._registry[metrics_class.metrics] = metrics_class


class MCPServerMetricsInstantFactory:
    _registry: Dict[MCPServerMetricsInstantEnum, Type[BaseMCPServerMetrics]] = {}

    @classmethod
    def create_metrics(cls, metrics: MCPServerMetricsInstantEnum) -> BaseMCPServerMetrics:
        _class = cls._registry.get(metrics)
        if not _class:
            raise error_codes.INVALID_ARGUMENT.format(f"unsupported mcp server metrics={metrics.value}")
        return _class()

    @classmethod
    def register(cls, metrics_class: Type[BaseMCPServerMetrics]):
        if not hasattr(metrics_class, "metrics"):
            raise ValueError("metrics_class must have a 'metrics' ClassVar")
        cls._registry[metrics_class.metrics] = metrics_class


# Register all metric classes
MCPServerMetricsRangeFactory.register(MCPServerRequestsMetrics)
MCPServerMetricsRangeFactory.register(MCPServerRequests2XXMetrics)
MCPServerMetricsRangeFactory.register(MCPServerNon2XXStatusMetrics)
MCPServerMetricsRangeFactory.register(MCPServerAppRequestsMetrics)
MCPServerMetricsRangeFactory.register(MCPServerToolRequestsMetrics)
MCPServerMetricsRangeFactory.register(MCPServerResponseTime95thMetrics)
MCPServerMetricsRangeFactory.register(MCPServerMethodRequestsMetrics)

MCPServerMetricsInstantFactory.register(MCPServerRequestsTotalMetrics)
MCPServerMetricsInstantFactory.register(MCPServerNon2XXTotalMetrics)
