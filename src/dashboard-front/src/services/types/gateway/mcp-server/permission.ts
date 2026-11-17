/** /gateways/{gateway_id}/mcp-servers/-/app-permission-apply/ [GET] */
export interface IGatewaysMcpServersAppPermissionApplyListQuery {
  /** Number of results to return per page. */
  limit?: number
  /** The initial index from which to return the results. */
  offset?: number
  /** MCPServer ID，不传则查询所有 */
  mcp_server_id?: number
  /** 蓝鲸应用 ID */
  bk_app_code?: string
  /** 申请人 */
  applied_by?: string
  /** 审批处理状态 */
  state?: 'processed' | 'unprocessed' | 'appPerm'
}

/** /gateways/{gateway_id}/mcp-servers/{mcp_server_id}/permissions/ [GET] */
export interface IGatewaysMcpServersPermissionsListQuery {
  /** Number of results to return per page. */
  limit?: number
  /** The initial index from which to return the results. */
  offset?: number
  /** 蓝鲸应用 ID */
  bk_app_code?: string
  /** 授权类型 */
  grant_type?: 'grant' | 'apply' | ''
  /** MCP Server */
  mcp_server_id?: number
  // 排序
  order_by?: string
}

/** /gateways/{gateway_id}/mcp-servers/{mcp_server_id}/permissions/app-permission-apply/applicant/ [GET] */
export interface IGatewaysMcpServersPermissionsAppPermissionApplyApplicantListQuery {
  state?: 'processed' | 'unprocessed'
}

// PATCH /gateways/{gateway_id}/mcp-servers/{mcp_server_id}/permissions/app-permission-apply/{id}/status/ - 更新授权审批状态，通过/驳回
export interface IMCPServerAppPermissionApplyUpdateInputSLZ {
  status: '' | 'approved' | 'rejected' // 审批状态
  comment?: string
}

// POST /gateways/{gateway_id}/mcp-servers/{mcp_server_id}/permissions/ - 主动授权应用
export interface IMCPServerAppPermissionCreateInputSLZ {
  bk_app_code: string
}

// POST /gateways/{gateway_id}/mcp-servers/-/permissions/app-permissions/-/export/
export interface IMCPServerAppPermissionExportInput {
  bk_app_code?: string
  mcp_server_id?: number | string
  grant_type?: 'grant' | 'apply' | ''
  order_by?: 'effective_time' | '-effective_time' | ''
  export_type: 'all' | 'filtered' | 'selected'
  selected_ids?: number[]
}

/**
 * GET /gateways/{gateway_id}/mcp-servers/-/app-permission-apply/
 */
export interface IMCPServerAppPermissionApplyListOutput {
  id: number
  bk_app_code: string
  applied_by: string
  applied_time: string
  created_time?: string
  handled_by?: string
  handled_time?: string
  status: string
  itsm_ticket_id: string
  itsm_ticket_url: string
  mcp_server: {
    id: number
    name: string
    title: string
  }
}

/**
 * GET /gateways/{gateway_id}/mcp-servers/{mcp_server_id}/permissions/
 */
export interface IMCPServerAppPermissionListOutput {
  id: number
  bk_app_code: string
  expires: string
  grant_type: string
  mcp_server: {
    id: number
    name: string
    title: string
  }
}

/**
 * GET /gateways/{gateway_id}/mcp-servers/{mcp_server_id}/permissions/app-permission-apply/applicant/
 */
export interface IMCPServerAppPermissionApplyApplicantOutput {
  applicants: string[]
}

/**
 * GET /gateways/{gateway_id}/mcp-servers/-/permissions/app-permission-app-codes/
 */
export interface IMCPServerAppPermissionAppCodeListOutput {
  bk_app_codes: string[]
}

/**
 * GET /gateways/{gateway_id}/mcp-servers/-/permissions/app-permission-apply/-/pending-count/
 */
export interface IMCPServerAppPermissionApplyPendingCountOutput {
  count: number
}
