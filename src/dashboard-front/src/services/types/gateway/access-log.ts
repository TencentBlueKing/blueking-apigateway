/** /gateways/{gateway_id}/logs/ [GET] */
export interface IGatewaysLogsListQuery {
  offset?: number // 偏移量，可选
  limit?: number // 限制数量，可选
  query?: string // 查询字符串，可选
  /** 最近 N 秒（按服务器时间）；与 time_start/time_end 同时传时以起止为准 */
  time_range?: number
  /** 开始时间（Unix 秒）；须与 time_end 成对，查询为闭区间，后端不校验先后 */
  time_start?: number
  /** 结束时间（Unix 秒） */
  time_end?: number
  stage_id?: number
  resource_id?: string
  backend_name?: string
}

/** /gateways/{gateway_id}/logs/timechart/ [GET] */
export interface IGatewaysLogsTimechartReadQuery {
  /** 环境 ID */
  stage_id: number
  /** 资源 ID */
  resource_id?: number | null
  /** 后端服务名称 */
  backend_name?: string
  /** 查询条件 */
  query?: string
  /** 包含条件 */
  include?: (string)[]
  /** 排除条件 */
  exclude?: (string)[]
  /** 最近 N 秒（按服务器时间）；与 time_start/time_end 同时传时以起止为准 */
  time_range?: number
  /** 起始时间（Unix 秒）；须与 time_end 成对，查询为闭区间，后端不校验先后 */
  time_start?: number
  /** 结束时间（Unix 秒） */
  time_end?: number
  /** 偏移量 */
  offset?: number
  /** 限制条数 */
  limit?: number
}

/** /gateways/{gateway_id}/logs/export/ [GET] */
export interface IGatewaysLogsExportListQuery {
  /** 环境 ID */
  stage_id: number
  /** 资源 ID */
  resource_id?: number | string | null
  /** 后端服务名称 */
  backend_name?: string
  /** 查询条件 */
  query?: string
  /** 开始时间（Unix 秒）。必填：后端导出用起止生成文件名，只传 time_range 会报错 */
  time_start: number
  /** 结束时间（Unix 秒）。必填 */
  time_end: number
  /** 偏移量 */
  offset?: number
  /** 限制条数 */
  limit?: number
}

/** /gateways/{gateway_id}/logs/{request_id}/ [GET] */
export interface IGatewaysLogsReadQuery {
  /** 随机数 */
  bk_nonce: number
  /** 时间戳 */
  bk_timestamp: number
  /** 签名 */
  bk_signature: string
  /** 分享人 */
  shared_by: string
}

/**
 * GET /gateways/logs/query/{request_id}/
 */
export interface IRequestLogOutput {
  request_id: string | null
  timestamp: number | null
  stage: string | null
  resource_id: number | null
  resource_name: string | null
  app_code: string | null
  client_ip: string | null
  method: string | null
  http_host: string | null
  http_path: string | null
  params: string | null
  body: string | null
  backend_scheme: string | null
  backend_method: string | null
  backend_host: string | null
  backend_path: string | null
  response_body: string | null
  status: number | null
  request_duration: number | null
  backend_duration: number | null
  code_name: string | null
  error: string | null
  response_desc: string | null
}

/**
 * GET /gateways/{gateway_id}/logs/
 */
export interface ILogListOutput {
  count: number
  results: Array<{
    request_id: string | null
    timestamp: number | null
    stage: string | null
    resource_id: number | null
    resource_name: string | null
    app_code: string | null
    client_ip: string | null
    method: string | null
    http_host: string | null
    http_path: string | null
    params: string | null
    body: string | null
    backend_scheme: string | null
    backend_method: string | null
    backend_host: string | null
    backend_path: string | null
    response_body: string | null
    status: number | null
    request_duration: number | null
    backend_duration: number | null
    code_name: string | null
    error: string | null
    response_desc: string | null
  }>
  fields: Array<{
    field: string
    is_filter: true
    label: string
  }> | null
  has_next: boolean
  has_previous: boolean
}

/**
 * GET /gateways/{gateway_id}/logs/timechart/
 */
export interface ITimeChartOutput {
  series: number[]
  timeline: number[]
}

/**
 * GET /gateways/{gateway_id}/logs/{request_id}/
 */
export interface IRequestLogDetailOutput {
  fields: Array<{
    field: string
    is_filter: true
    label: string
  }>
  results: Array<{
    request_id: string | null
    timestamp: number | null
    stage: string | null
    resource_id: number | null
    resource_name: string | null
    app_code: string | null
    client_ip: string | null
    method: string | null
    http_host: string | null
    http_path: string | null
    params: string | null
    body: string | null
    backend_scheme: string | null
    backend_method: string | null
    backend_host: string | null
    backend_path: string | null
    response_body: string | null
    status: number | null
    request_duration: number | null
    backend_duration: number | null
    code_name: string | null
    error: string | null
    response_desc: string | null
  }>
}

/**
 * GET /gateways/{gateway_id}/logs/{request_id}/link/
 */
export interface ILogLinkOutput {
  link: string
}
