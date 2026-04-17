/*
 * TencentBlueKing is pleased to support the open source community by making
 * 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
 * Copyright (C) 2026 Tencent. All rights reserved.
 * Licensed under the MIT License (the "License"); you may not use this file except
 * in compliance with the License. You may obtain a copy of the License at
 *
 *     http://opensource.org/licenses/MIT
 *
 * Unless required by applicable law or agreed to in writing, software distributed under
 * the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND,
 * either express or implied. See the License for the specific language governing permissions and
 * limitations under the License.
 *
 * We undertake not to change the open source license (MIT license) applicable
 * to the current version of the project delivered to anyone in the future.
 */

import http from '../http';
import type { IPagination } from '@/types/common';

const path = '/gateways';

// 定义图表系列类型
type IChartsSires = {
  metrics?: Array<unknown> // 指标数组
  series?: Array<ISeriesItemType> // 系列项数组
};

// 定义瞬时类型
type InstantType = { instant?: number };

// echart配置项
type ILegendItem = {
  color: string
  name: string
  selected: string
};

// 定义统计数据类型
export interface IStatisticsType {
  requests_total?: InstantType // 总请求数
  non_2xx_total?: InstantType // 非 2XX 请求数
  health_rate?: InstantType // 健康率
}

export interface ISeriesItemType {
  alias: string // 别名
  datapoints: Array<Array<number>> // 数据点数组
  dimensions: Record<string, any> // 维度
  metric_field: string // 指标字段
  target: string // 目标
  unit: string // 单位
}

// 查询条件泛型
export interface IObservabilityBasicForm {
  time_start?: number
  time_end?: number
  time_range?: number
  app_code?: string
  request_id?: string
  status?: string
  query?: string
  metrics?: string
  step?: string
  mcp_server_name?: string
}

// 日志详情响应数据泛型
export interface IFlowLogTable {
  tool_name: string
  prompt_name?: string
  bk_username: string
  latency: string
  x_request_id: string
  session_id: string
  params: string
  client_id: string
  mcp_method: string
  mcp_server_name: string
  response: string
  client_ip: string
  request_id: string
  app_code: string
  gateway_name: string
  status: string
  error: string
  request_body_size: number
  response_body_size: number
  timestamp: number
}

// 定义图表数据类型
export interface IChartDataType {
  requests_total?: IChartsSires // 总请求数图表系列
  requests?: IChartsSires // 请求图表系列
  requests_2xx?: IChartsSires // 20x状态图表系列
  non_2xx_status?: IChartsSires // 非20x状态图表系列
  app_requests?: IChartsSires // 应用请求图表系列
  tool_requests?: IChartsSires // 资源请求图表系列
  method_requests?: IChartsSires // MCP Server请求图表系列
  request_body_size?: IChartsSires // 请求体积图表系列(avg bytes)
  response_body_size?: IChartsSires // 响应体积图表系列(avg bytes)
  response_time?: IChartsSires // 响应时间图表系列
  response_time_50th?: IChartsSires // 响应时间50百分位图表系列
  response_time_95th?: IChartsSires // 响应时间95百分位图表系列
  response_time_99th?: IChartsSires // 响应时间99百分位图表系列
}

// 定义图表数据加载状态类型
export interface IChartDataLoading {
  requests_total?: boolean // 总请求数加载状态
  requests?: boolean // 请求加载状态
  health_rate?: boolean // 健康率载状态
  requests_2xx?: boolean // 20x状态加载状态
  non_2xx_status?: boolean // 非20x状态加载状态
  non_2xx_total?: boolean // 20*总请求数
  app_requests?: boolean // 应用请求加载状态
  tool_requests?: boolean // 资源请求加载状态
  method_requests?: boolean // MCP Server 请求数趋势
  request_body_size?: boolean // 请求体积趋势(avg bytes)
  response_body_size?: boolean // 响应体积趋势(avg bytes)
  response_time_50th?: boolean // 响应时间50百分位加载状态
  response_time_95th?: boolean // 响应时间95百分位加载状态
  response_time_99th?: boolean // 响应时间99百分位加载状态
}

// 图表option配置项
export interface IChartLegend {
  requests_total?: ILegendItem
  requests?: ILegendItem
  requests_2xx?: ILegendItem
  non_2xx_status?: ILegendItem
  health_rate?: ILegendItem
  app_requests?: ILegendItem
  tool_requests?: ILegendItem
  method_requests?: ILegendItem
  request_body_size?: ILegendItem
  response_body_size?: ILegendItem
  response_time_50th?: ILegendItem
  response_time_95th?: ILegendItem
  response_time_99th?: ILegendItem
};

// 流水日志和仪表盘数据图层请求参数泛型
export type IObservabilitySearchParams = IObservabilityBasicForm & IPagination;

// 网关日志（上下行通用）
export interface IGatewayLog {
  layer: string
  service: string
  request_id: string
  method: string
  http_host: string
  http_path: string
  status: number
  request_duration: number
  backend_duration: number
  stage: string
  resource_name: string
  backend_host: string
  backend_path: string
  backend_method: string
  backend_scheme: string
  app_code: string
  client_ip: string
  error: string
  code_name: string
}

// 链路 span 主结构
export interface ISpan {
  is_expand: boolean
  depth: number
  hasChildren: boolean
  span_id: string
  parent_span_id: string | null
  layer: string
  service: string
  operation: string
  upstream: string
  latency: string
  latency_ms: number
  start_offset_ms: number
  status: number | null
  detail: ITraceDetail
  children: ISpan[]
  [key: string]: any
}

//  耗时分布
export interface ILatencyDistribution {
  latency_ms: number
  layer: string
  operation: string
  percentage: number
  service: string
  start_offset_ms: number
}

// 根接口
export interface ITraceLog {
  app_code?: string
  client_ip?: string
  error?: string
  tool_name?: string
  mcp_method?: string
  mcp_server_name?: string
  request_id: string
  x_request_id: string
  status?: string
  timestamp?: number
  span_count?: number
  service_count?: number
  total_latency_ms: number
  traceName?: number | string
  startTime?: number
  endTime?: number
  duration?: number
  services: {
    name: string
    numberOfSpans: number
  }[]
  spans: ISpan[]
  logList: ITraceDetail[]
  upstream_gateway_log: IGatewayLog | null
  downstream_gateway_log: IGatewayLog | null
  latency_distribution?: ILatencyDistribution[]
}

// HTTP 层 span 详情
export interface IHttpSpanDetail {
  method: string
  path: string
  status: number
  client_ip: string
  app_code: string
  gateway_name: string
  mcp_server_name: string
  request_id: string
  x_request_id: string
}

// MCP 层 span 详情
export interface IMcpSpanDetail {
  mcp_method: string
  tool_name: string
  prompt_name: string | null
  upstream?: string
  operation: string
  tool: string
  params: string
  response: string
  request_body_size: number
  response_body_size: number
  app_code: string
  bk_username: string
  client_ip: string
  client_id: string
  session_id: string
  request_id: string
  x_request_id: string
  trace_id: string | null
  error: string | null
}

export interface ISearchParamsType {
  [key: string]: string | number | boolean | null | undefined
}

export interface IDataPoint {
  0: number | null
  1: number
}

// trace瀑布图详情组装数据
export type ITraceDetail = IGatewayLog & IHttpSpanDetail & IMcpSpanDetail & ITraceLog;

/**
 *  查询 MCP Server 日志时间分布图
 * @param gatewayId 网关id
 * @param params  搜索参数
 * @param extraStr 检索项
 */
export const fetchObservabilityLogChart = (gatewayId: number, params: IObservabilityBasicForm, extraStr?: string) => {
  const queryStr = extraStr ? `?${extraStr}` : '';
  return http.get(`${path}/${gatewayId}/mcp-servers/-/logs/timechart/${queryStr}`, params);
};

/**
 *  查询 MCP Server 日志列表
 * @param gatewayId 网关id
 * @param {IObservabilitySearchParams} params  搜索参数
 * @param extraStr 检索项
 */
export const fetchObservabilityLogList = (
  gatewayId: number,
  params: IObservabilitySearchParams,
  extraStr?: string,
) => {
  const queryStr = extraStr ? `?${extraStr}` : '';
  return http.get(`${path}/${gatewayId}/mcp-servers/-/logs/${queryStr}`, params);
};

/**
 *  根据 request_id 或 x_request_id 查询 MCP Server 日志（工具箱，无需网关权限）
 * @param requestId 请求id
 */
export const fetchObservabilityLogInfo = (requestId: string) => {
  return http.get(`${path}/mcp-server-logs/query/${requestId}/`);
};

/**
 *  根据 request_id 或 x_request_id 查询 MCP Server 调用链汇总信息（工具箱，无需网关权限）
 * @param requestId 请求id
 */
export const fetchObservabilityLogSummary = (requestId: string) => {
  return http.get(`${path}/mcp-server-logs/query/${requestId}/summary/`);
};

/**
 * 根据 request_id 或 x_request_id 查询 MCP Server 调用链路详情（工具箱，无需网关权限）
 * @param gatewayId 网关id
 * @param requestId 请求id
 */
export const fetchObservabilityTraceChain = (requestId: string) => {
  return http.get(`${path}/mcp-server-logs/query/${requestId}/chain/`);
};

/**
 *  根据 request_id 获取 MCP Server 日志详情
 * @param gatewayId 网关id
 * @param requestId 请求id
 * @param {IObservabilitySearchParams} params  搜索参数
 */
export const fetchObservabilityLogInfoByGateway = (
  gatewayId: number,
  requestId: string,
  params: IObservabilitySearchParams,
) => {
  return http.get(`${path}/${gatewayId}/mcp-servers/-/logs/${requestId}/`, params);
};

/**
 *  根据 request_id 查询 MCP Server 调用链路（瀑布图数据）
 * @param gatewayId 网关id
 * @param requestId 请求id
 */
export const fetchObservabilityTraceChainByGateway = (
  gatewayId: number,
  requestId: string,
) => {
  return http.get(`${path}/${gatewayId}/mcp-servers/-/logs/${requestId}/chain/`);
};

/**
 *  根据 x_request_id 查询全链路关联日志
 * @param gatewayId 网关id
 * @param xRequestId 全链路请求 ID
 */
export const fetchObservabilityTraceLog = (
  gatewayId: number,
  xRequestId: string,
) => {
  return http.get(`${path}/${gatewayId}/mcp-servers/-/logs/trace/${xRequestId}/`);
};

/**
 *  导出 MCP Server 日志
 * @param gatewayId 网关id
 * @param {IObservabilityBasicForm} params 导出参数
 * @param extraStr 检索项
 */
export const fetchExportFlowLog = (gatewayId: number, params: IObservabilityBasicForm, extraStr?: string) => {
  const queryStr = extraStr ? `?${extraStr}` : '';
  return http.get(`${path}/${gatewayId}/mcp-servers/-/logs/export/${queryStr}`, params, { responseType: 'blob' });
};

/**
 *  查询有MCPServer调用权限的 bk_app_code 列表（网关级别）
 * @param gatewayId 网关id
 * @param params  搜索参数
 */
export const fetchObservabilityAppCode = (gatewayId: number) => {
  return http.get(`${path}/${gatewayId}/mcp-servers/-/app-permission-app-codes/`);
};

/**
 *  查询 MCP Server 时序图 metrics
 * @param gatewayId 网关id
 * @param {IObservabilitySearchParams} params 查询参数
 * @param extraStr 检索项
 */
export const fetchMetricsQueryRange = (
  gatewayId: number,
  params: IObservabilitySearchParams,
) => {
  return http.get(`${path}/${gatewayId}/mcp-servers/-/metrics/query-range/`, params);
};

/**
 *  查询 MCP Server 瞬时值 metrics
 * @param gatewayId 网关id
 * @param {IObservabilitySearchParams} params 查询参数
 * @param extraStr 检索项
 */
export const fetchMetricsQueryInstant = (
  gatewayId: number,
  params: IObservabilitySearchParams,
) => {
  return http.get(`${path}/${gatewayId}/mcp-servers/-/metrics/query-instant/`, params);
};
