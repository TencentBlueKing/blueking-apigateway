import type { IMCPServerTimeQuery } from '@/services/types/gateway/mcp-server/observability.ts';

// MCP Server 日志列表、时间分布和导出
export interface IMCPServerLogQuery extends IMCPServerTimeQuery {
  mcp_server_name?: string
  mcp_method?: string
  tool_name?: string
  prompt_name?: string
  app_code?: string
  request_id?: string
  x_request_id?: string
  session_id?: string
  status?: string
  query?: string
  limit?: number
  offset?: number
}

/**
 * GET /gateways/{gateway_id}/mcp-servers/-/logs/timechart/
 */
export interface IMCPServerLogTimeChartOutput {
  series: number[]
  timeline: number[]
}

/**
 * MCP Server 日志
 */
export interface IMCPServerLogOutput {
  request_id?: string | null
  x_request_id?: string | null
  timestamp?: number | null
  gateway_id?: number | null
  gateway_name?: string | null
  mcp_server_id?: number | null
  mcp_server_name?: string | null
  mcp_method?: string | null
  tool_name?: string | null
  prompt_name?: string | null
  app_code?: string | null
  bk_username?: string | null
  client_ip?: string | null
  client_id?: string | null
  session_id?: string | null
  params?: string | null
  response?: string | null
  request_body_size?: number | null
  response_body_size?: number | null
  latency?: string | null
  trace_id?: string | null
  status?: string | null
  error?: string | null
}

/**
 * MCP Server 日志列表中可展开 / 可筛选的字段
 */
export interface IMCPServerLogField {
  label: string
  field: string
  is_filter: boolean
}

/**
 * GET /gateways/{gateway_id}/mcp-servers/-/logs/
 */
export interface IMCPServerLogListOutput {
  count: number
  has_next: boolean
  has_previous: boolean
  results: IMCPServerLogOutput[]
  fields: IMCPServerLogField[]
}

/**
 * 调用链扁平化后的单条日志：span 的基础字段加上 span 详情中的动态字段；
 * 上下游网关日志的 layer 分别为 gateway_upstream、gateway_downstream
 */
export interface IMCPServerChainLogItem {
  layer: string
  service?: string
  operation?: string
  latency?: string | null
  latency_ms?: number | null
  status?: number | string | null
  [key: string]: any
}

/**
 * GET /gateways/{gateway_id}/mcp-servers/-/logs/{request_id}/
 * GET /gateways/mcp-server-logs/query/{request_id}/
 */
export interface IMCPServerChainLogListOutput {
  count: number
  has_next: boolean
  has_previous: boolean
  results: IMCPServerChainLogItem[]
  fields: IMCPServerLogField[]
}

/**
 * MCP Server 调用链中的上下游网关日志
 */
export interface IMCPServerGatewayLogOutput {
  layer: string
  service: string
  timestamp?: number | null
  request_id?: string | null
  x_request_id?: string | null
  method?: string | null
  http_host?: string | null
  http_path?: string | null
  status?: number | null
  request_duration?: number | null
  backend_duration?: number | null
  stage?: string | null
  resource_name?: string | null
  backend_host?: string | null
  backend_path?: string | null
  backend_method?: string | null
  backend_scheme?: string | null
  app_code?: string | null
  client_ip?: string | null
  error?: string | null
  code_name?: string | null
}

/**
 * MCP Server 调用链路 Span
 */
export interface IMCPServerLogSpanOutput {
  span_id: string
  parent_span_id: string | null
  layer: string
  service: string
  upstream: string | null
  operation: string
  latency: string | null
  latency_ms: number | null
  start_offset_ms: number
  status: number | null
  detail: Record<string, any>
  children: IMCPServerLogSpanOutput[]
}

/**
 * GET /gateways/{gateway_id}/mcp-servers/-/logs/{request_id}/chain/
 * GET /gateways/mcp-server-logs/query/{request_id}/chain/
 */
export interface IMCPServerLogChainOutput {
  request_id: string
  x_request_id: string
  timestamp: number | null
  total_latency_ms: number
  span_count: number
  service_count: number
  status: string
  latency_distribution: Record<string, any>[]
  spans: IMCPServerLogSpanOutput[]
  upstream_gateway_log: IMCPServerGatewayLogOutput | null
  downstream_gateway_log: IMCPServerGatewayLogOutput | null
}

/**
 * GET /gateways/mcp-server-logs/query/{request_id}/summary/
 */
export interface IMCPServerLogQuerySummaryOutput {
  request_id: string
  x_request_id: string
  timestamp: number | null
  total_latency_ms: number
  service_count: number
  span_count: number
  status: string
  gateway_id: number | null
  gateway_name: string
  mcp_server_id: number | null
  mcp_server_name: string
  mcp_method: string
  tool_name: string
  app_code: string
  client_ip: string
  error: string
  latency_distribution: Record<string, any>[]
}
