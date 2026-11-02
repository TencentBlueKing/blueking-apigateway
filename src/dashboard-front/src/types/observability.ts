/*
 * TencentBlueKing is pleased to support the open source community by making
 * 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
 * Copyright (C) Tencent. All rights reserved.
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

/*
* MCP Server 可观测相关类型（指标图表、日志与调用链）
*  */

import type { IChartSeries } from '@/types/metrics';

// MCP Server 瞬时值；健康率接口返回保留两位小数的字符串，如 "100.00"
interface IMcpInstantValue {
  instant?: number | string
}

// MCP Server 统计数据
export interface IStatisticsType {
  requests_total?: IMcpInstantValue // 总请求数
  non_2xx_total?: IMcpInstantValue // 非 2XX 请求数
  health_rate?: IMcpInstantValue // 健康率
}

// MCP Server 图表数据
export interface IChartDataType {
  requests_total?: IChartSeries // 总请求数图表系列
  requests?: IChartSeries // 请求图表系列
  requests_2xx?: IChartSeries // 20x状态图表系列
  non_2xx_status?: IChartSeries // 非20x状态图表系列
  app_requests?: IChartSeries // 应用请求图表系列
  tool_requests?: IChartSeries // 资源请求图表系列
  method_requests?: IChartSeries // MCP Server请求图表系列
  request_body_size?: IChartSeries // 请求体积图表系列(avg bytes)
  response_body_size?: IChartSeries // 响应体积图表系列(avg bytes)
  response_time?: IChartSeries // 响应时间图表系列
  response_time_50th?: IChartSeries // 响应时间50百分位图表系列
  response_time_95th?: IChartSeries // 响应时间95百分位图表系列
  response_time_99th?: IChartSeries // 响应时间99百分位图表系列
}

// MCP Server 图表加载状态
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
  upstream?: string
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

// trace瀑布图详情组装数据
export type ITraceDetail = IGatewayLog & IHttpSpanDetail & IMcpSpanDetail & ITraceLog;
