/** /gateways/{gateway_id}/releases/histories/ [GET] */
export interface IGatewaysReleasesHistoriesListQuery {
  /** Number of results to return per page. */
  limit?: number
  /** The initial index from which to return the results. */
  offset?: number
  /** 查询参数关键字 */
  keyword?: string
  /** 环境 id */
  stage_id?: number | null
  /** 创建者 */
  created_by?: string
  /** 开始时间（Unix 秒）；只有起止都传才过滤，闭区间 created_time ∈ [time_start, time_end] */
  time_start?: number | null
  /** 结束时间（Unix 秒） */
  time_end?: number | null
}

/** /gateways/{gateway_id}/releases/stages/{stage_id}/resources/ [GET] */
export interface IGatewaysReleasesStagesResourcesListQuery {
  /** Number of results to return per page. */
  limit?: number
  /** The initial index from which to return the results. */
  offset?: number
}

// POST /gateways/{gateway_id}/releases/ - 版本发布接口
export interface IReleaseInputSLZ {
  stage_id: number
  resource_version_id: number
  comment?: string
}

/**
 * POST /gateways/{gateway_id}/releases/
 */
export interface IReleaseHistoryOutput {
  id: number
  stage: {
    id: number
    name: string
  }
  resource_version_display: string
  created_time: string
  created_by: string
  source: string
  duration: number
  status: string
  data_plane: IReleaseHistoryEventRetrieveOutput['data_plane']
}

/**
 * GET /gateways/{gateway_id}/releases/histories/
 */
export interface IReleaseHistoryListOutput {
  id: number
  stage: {
    id: number
    name: string
  }
  resource_version_display: string
  created_time: string
  created_by: string
  source: string
  duration: number
  status: string
  data_plane: IReleaseHistoryOutput['data_plane']
}

/**
 * GET /gateways/{gateway_id}/releases/histories/{history_id}/events/
 */
export interface IReleaseHistoryEventRetrieveOutput {
  id: number
  stage: {
    id: number
    name: string
  }
  resource_version_display: string
  created_time: string
  created_by: string
  source: string
  duration: number
  status: string
  events: {
    id: number
    release_history_id: number
    name: string
    step: number
    status: string
    created_time: string
    detail: {
      [key: string]: string | null
    }
  }[]
  events_template: Array<{
    description: string
    name: string
    step: number
  }>
  data_plane: {
    description: string
    id: number
    name: string
  } | null
}

/**
 * GET /gateways/{gateway_id}/releases/stages/{stage_id}/resources/
 */
export interface IResourceListOutput {
  id: number
  name: string | null
  description: string | null
  method: string
  path: string
  created_time: string | null
  updated_time: string | null
  backend: string
  labels: string
  docs: string
  has_updated: string
  plugin_count: string
  auth_config: string
}

/**
 * GET /gateways/{gateway_id}/releases/stages/{stage_id}/resources/{resource_id}/schema/
 */
export interface IReleaseResourceSchemaOutput {
  resource_id: number
  body_schema: any
  body_example: any
  parameter_schema: any
  response_schema: any
}
