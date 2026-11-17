/** /gateways/{gateway_id}/audits/logs/ [GET] */
export interface IGatewaysAuditsLogsListQuery {
  /** Number of results to return per page. */
  limit?: number
  /** The initial index from which to return the results. */
  offset?: number
  /** 开始时间（Unix 秒），op_time >= time_start；两端各自生效 */
  time_start?: number | null
  /** 结束时间（Unix 秒），op_time <= time_end；两端各自生效 */
  time_end?: number | null
  /** 关键字 (模糊) */
  keyword?: string
  /** 操作对象 */
  op_object_type?: 'gateway' | 'stage' | 'backend' | 'stage_backend' | 'resource' | 'resource_version' | 'release' | 'gateway_label' | 'plugin' | 'resource_doc' | 'mcp_server' | 'permission'
  /** 操作类型 */
  op_type?: 'create' | 'delete' | 'modify' | 'query'
  /** 实例 */
  op_object?: string
  op_status?: string
  order_by?: string
  /** 操作人 */
  username?: string
}

/**
 * GET /gateways/{gateway_id}/audits/logs/
 */
export interface IAuditEventLogOutput {
  event_id: string
  system: string
  username: string
  op_time: string
  op_type: string
  op_status: string
  op_object_type: string
  op_object_id: string | null
  op_object: string | null
  data_before: string | null
  data_after: string | null
  comment: string | null
}
