/** /gateways/{gateway_id}/permissions/app-permission-apply/ [GET] */
export interface IGatewaysPermissionsAppPermissionApplyListQuery {
  /** Number of results to return per page. */
  limit?: number
  /** The initial index from which to return the results. */
  offset?: number
  bk_app_code?: string
  applied_by?: string
  grant_dimension?: string
}

/** /gateways/{gateway_id}/permissions/app-permission-records/ [GET] */
export interface IGatewaysPermissionsAppPermissionRecordsListQuery {
  /** Number of results to return per page. */
  limit?: number
  /** The initial index from which to return the results. */
  offset?: number
  /** 蓝鲸应用 ID */
  bk_app_code?: string
  /** 授权维度 */
  grant_dimension?: 'api' | 'resource'
  /** 开始时间（Unix 秒），handled_time >= time_start；两端各自生效 */
  time_start?: number
  /** 结束时间（Unix 秒），handled_time < time_end（半开区间，不含结束时刻本身）；两端各自生效 */
  time_end?: number
}

/** /gateways/{gateway_id}/permissions/app-permissions/ [GET] */
export interface IGatewaysPermissionsAppPermissionsListQuery {
  /** Number of results to return per page. */
  limit?: number
  /** The initial index from which to return the results. */
  offset?: number
  /** 应用 ID */
  bk_app_code?: string
  /** 查询关键字 */
  keyword?: string
  /** 请求路径 */
  resource_path?: string
  grant_type?: 'initialize' | 'apply' | 'renew' | 'auto_renew' | 'sync'
  /** 资源id */
  resource_id?: number
  /** 排序 */
  order_by?: 'bk_app_code' | '-bk_app_code' | 'expires' | '-expires'
  /** 授权维度 */
  grant_dimension?: 'api' | 'resource'
  /** 申请人 */
  applied_by?: string
}

/** /gateways/{gateway_id}/permissions/app-permissions/bk-app-codes/ [GET] */
export interface IGatewaysPermissionsAppPermissionsBkAppCodesListQuery {
  /** Number of results to return per page. */
  limit?: number
  /** The initial index from which to return the results. */
  offset?: number
}

// DELETE /gateways/{gateway_id}/permissions/app-{gateway,resource}-permissions/delete/
export interface IAppPermissionDeleteQuery {
  /** 服务层将数组序列化为逗号分隔的查询参数。 */
  ids: number[]
}

// DELETE /gateways/{gateway_id}/permissions/app-permissions/batch/
export interface IAppPermissionBatchDeleteInput {
  resource_dimension_ids?: number[]
  gateway_dimension_ids?: number[]
}

// POST /gateways/{gateway_id}/permissions/app-gateway-permissions/ - 网关权限主动授权
export interface IAppPermissionInputSLZ {
  bk_app_code: string
  expire_days: number | null
  resource_ids: number[] | null
}

// POST /gateways/{gateway_id}/permissions/app-permission-apply/approval/ - 审批操作
export interface IAppPermissionApplyApprovalInputSLZ {
  ids: number[]
  part_resource_ids?: Record<string, number[]>
  status: string
  comment: string
}

// POST /gateways/{gateway_id}/permissions/app-permissions/export/ - 网关权限导出
export interface IAppPermissionExportInputSLZ {
  bk_app_code?: string
  resource_id?: number
  keyword?: string
  resource_path?: string
  grant_type?: string
  grant_dimension?: string
  order_by?: string
  export_type: string
  gateway_permission_ids?: number[]
  resource_permission_ids?: number[]
}

// POST /gateways/{gateway_id}/permissions/app-permissions/renew/ - 批量续期
export interface IAppPermissionRenewInputSLZ {
  gateway_dimension_ids?: number[]
  resource_dimension_ids?: number[]
  expire_days: number
}

/**
 * GET /gateways/{gateway_id}/permissions/app-permission-apply/
 */
export interface IAppPermissionApplyListOutput {
  id: number
  bk_app_code: string
  resource_ids: number[]
  status: string
  reason: string
  expire_days: number
  grant_dimension: string
  itsm_ticket_id?: string
  itsm_ticket_url?: string
  created_time: string | null
  expire_days_display: string
  grant_dimension_display: string
  applied_by: string
}

export interface IAppPermissionHandledResource {
  id?: number
  name: string
  method?: string
  path?: string
  apply_status: string
}

/**
 * GET /gateways/{gateway_id}/permissions/app-permission-records/
 */
export interface IAppPermissionRecordListOutput {
  id: number
  bk_app_code: string
  applied_by: string
  applied_time: string
  handled_by: string
  handled_time: string | null
  status: string
  grant_dimension: string
  comment: string
  reason: string
  expire_days: number
  gateway_name?: string
  resource_ids: number[]
  handled_resources: IAppPermissionHandledResource[]
  expire_days_display: string
  grant_dimension_display: string
  itsm_ticket_id?: string
  itsm_ticket_url?: string
}

/**
 * GET /gateways/{gateway_id}/permissions/app-permissions/
 */
export interface IAppPermissionListOutput {
  id: number
  bk_app_code: string
  resource_id: number
  resource_name: string
  resource_path: string
  resource_method: string
  expires: string
  grant_dimension: string
  grant_type: string
  renewable: boolean
  handled_by?: string
}
