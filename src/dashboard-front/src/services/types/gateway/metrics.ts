/** /gateways/{gateway_id}/metrics/query-instant/ [GET] */
export interface IGatewaysMetricsQueryInstantListQuery {
  /** Number of results to return per page. */
  limit?: number
  /** The initial index from which to return the results. */
  offset?: number
  /** 环境 id */
  stage_id: number
  /** 后端服务名称 */
  backend_name?: string
  /** 资源 id */
  resource_id?: number | null
  /** metric 类型 */
  metrics: 'requests_total' | 'health_rate'
  /** 最近 N 秒（按服务器时间）；与 time_start/time_end 同时传时以起止为准 */
  time_range?: number
  /** 开始时间（Unix 秒）；须与 time_end 成对，或改传 time_range；后端不校验先后 */
  time_start?: number
  /** 结束时间（Unix 秒） */
  time_end?: number
}

/** /gateways/{gateway_id}/metrics/query-range/ [GET] */
export interface IGatewaysMetricsQueryRangeListQuery {
  /** Number of results to return per page. */
  limit?: number
  /** The initial index from which to return the results. */
  offset?: number
  /** 环境 id */
  stage_id: number
  /** 后端服务名称 */
  backend_name?: string
  /** 资源 id */
  resource_id?: number | null
  /** metric 类型 */
  metrics: 'requests' | 'non_20x_status' | 'app_requests' | 'resource_requests' | 'response_time_90th' | 'response_time_50th' | 'response_time_95th' | 'response_time_99th' | 'ingress' | 'egress' | 'llm_latency_avg' | 'llm_latency_95th' | 'llm_token_usage' | 'llm_token_95th' | 'llm_active_connections'
  /** 最近 N 秒（按服务器时间）；与 time_start/time_end 同时传时以起止为准 */
  time_range?: number
  /** 开始时间（Unix 秒）；须与 time_end 成对，或改传 time_range；后端不校验先后 */
  time_start?: number
  /** 结束时间（Unix 秒） */
  time_end?: number
  /** 精度；不传或 auto 时后端按时间跨度推导 */
  step?: 'auto' | '1m' | '5m' | '10m' | '30m' | '1h' | '3h' | '12h'
}

/** /gateways/{gateway_id}/metrics/query-summary/ [GET] */
export interface IGatewaysMetricsQuerySummaryListQuery {
  /** Number of results to return per page. */
  limit?: number
  /** The initial index from which to return the results. */
  offset?: number
  /** 环境 id */
  stage_id: number
  /** 资源 id */
  resource_id?: number | null
  /** app code */
  bk_app_code?: string
  /** metric 类型 */
  metrics: 'requests_total' | 'requests_failed_total'
  /** 时间维度 */
  time_dimension: 'day' | 'week' | 'month'
  /**
   * 开始时间（Unix 秒）。必填。
   * 数据为按 UTC 自然日统计的日桶，按桶起点过滤：start_time ∈ [time_start, time_end]；
   * time_start 不得早于服务器时间的 6 个月前
   */
  time_start: number
  /** 结束时间（Unix 秒）。必填 */
  time_end: number
}

/** /gateways/{gateway_id}/metrics/query-summary/caller/ [GET] */
export interface IGatewaysMetricsQuerySummaryCallerListQuery {
  /** Number of results to return per page. */
  limit?: number
  /** The initial index from which to return the results. */
  offset?: number
  /** 环境 id */
  stage_id: number
  /** 开始时间（Unix 秒）。必填；日桶过滤与半年限制同 query-summary */
  time_start: number
  /** 结束时间（Unix 秒）。必填 */
  time_end: number
}

/** /gateways/{gateway_id}/metrics/query-summary/export/ [GET] */
export interface IGatewaysMetricsQuerySummaryExportListQuery {
  /** 环境 id；不传则导出全部环境 */
  stage_id?: number | null
  /** 资源 id */
  resource_id?: number | null
  /** app code */
  bk_app_code?: string
  /** 开始时间（Unix 秒）。必填；日桶过滤与半年限制同 query-summary */
  time_start: number
  /** 结束时间（Unix 秒）。必填 */
  time_end: number
}

/**
 * GET /gateways/{gateway_id}/metrics/query-instant/
 */
export interface IMetricInstantOutput {
  instant: number
}

/**
 * GET /gateways/{gateway_id}/metrics/query-range/
 */
export interface IMetricRangeOutput {
  metrics: unknown[]
  series: unknown[]
}

/**
 * GET /gateways/{gateway_id}/metrics/query-summary/
 */
export interface IMetricSummaryOutput {
  count: number
}

/**
 * GET /gateways/{gateway_id}/metrics/query-summary/caller/
 */
export interface IMetricSummaryCallerOutput {
  count: number
}
