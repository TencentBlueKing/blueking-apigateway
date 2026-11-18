/** /gateways/{gateway_id}/tests/histories/ [GET] */
export interface IGatewaysTestsHistoriesListQuery {
  /** Number of results to return per page. */
  limit?: number
  /** The initial index from which to return the results. */
  offset?: number
  /** 资源名称（模糊匹配） */
  resource_name?: string
  /**
   * 开始时间（Unix 秒）。后端直接按整数解析，非整数会导致服务端报错；
   * 只有起止都传才过滤，闭区间 created_time ∈ [time_start, time_end]
   */
  time_start?: number
  /** 结束时间（Unix 秒） */
  time_end?: number
}

// POST /gateways/{gateway_id}/tests/
export interface IAPITestInputSLZ {
  stage_id: number
  resource_id: number
  method: string
  subpath?: string
  headers: Record<string, string>
  path_params: Record<string, string>
  query_params: Record<string, string>
  body?: string
  use_test_app: boolean
  use_user_from_cookies?: boolean
  authorization?: IAPITestAuthorization | null
}

export interface IAPITestAuthorization {
  bk_app_code?: string
  bk_app_secret?: string
  bk_ticket?: string
  bk_token?: string
}

/**
 * POST /gateways/{gateway_id}/tests/
 */
export interface IAPITestOutput {
  status_code: number
  proxy_time: number
  size: number
  body: string
  headers: {
    [key: string]: string | null
  }
}

/**
 * GET /gateways/{gateway_id}/tests/histories/
 */
export interface IAPIDebugHistoriesListOutput {
  id: number
  created_time: string | null
  gateway_id: number
  resource_name: string
  request: any
  response: any
}

/**
 * GET /gateways/{gateway_id}/tests/histories/{id}/
 */
export interface IAPIDebugHistoriesRetrieveOutput {
  id: number
  created_time: string | null
  gateway_id: number
  resource_name: string
  request: any
  response: any
}
