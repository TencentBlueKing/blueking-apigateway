import type { IMCPServerTimeQuery } from '@/services/types/gateway/mcp-server/observability.ts';

// GET /gateways/{gateway_id}/mcp-servers/-/metrics/query-instant/
export interface IMCPServerMetricsInstantQuery extends IMCPServerTimeQuery {
  mcp_server_name?: string
  app_code?: string
  metrics: string
}

// GET /gateways/{gateway_id}/mcp-servers/-/metrics/query-range/
export interface IMCPServerMetricsRangeQuery extends IMCPServerMetricsInstantQuery {
  step?: string
}

/**
 * GET /gateways/{gateway_id}/mcp-servers/-/metrics/query-range/
 */
export interface IMCPServerMetricRangeOutput {
  metrics: unknown[]
  series: Array<{
    alias: string
    datapoints: Array<Array<number>>
    dimensions: Record<string, any>
    dimensions_translation?: Record<string, any>
    metric_field: string
    target: string
    unit: string
  }>
}

/**
 * GET /gateways/{gateway_id}/mcp-servers/-/metrics/query-instant/
 * 健康率（health_rate）返回保留两位小数的字符串，如 "100.00"
 */
export interface IMCPServerMetricInstantOutput {
  instant: number | string
}
