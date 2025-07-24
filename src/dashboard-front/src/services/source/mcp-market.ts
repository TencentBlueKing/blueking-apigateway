import http from '../http';

const path = '/gateways';

export interface IMarketplace {
  limit: number
  offset: number
  keyword?: string
}

export interface IStageReleaseCheckMcp {
  stage_id: number
  resource_version_id: number
}

export interface IMcpPermissions {
  bk_app_code: string
  grant_type: string
}

export interface IMcpAppPermissionApply {
  bk_app_code: string
  state: string
  applied_by: string
  mcp_server_id: number
}

export interface IMarketplaceItem {
  id: number
  name: string
  description: string
  is_public: boolean
  labels: string[]
  resource_names: string[]
  status: number
  tools_count: number
  url: string
  stage: {
    id: number
    name: string
  }
  gateway: {
    id: number
    name: string
    is_official: boolean
  }
}

export interface ITool {
  id: number
  name: string
  description: string
  method: string
  path: string
  verified_user_required: boolean
  verified_app_required: boolean
  resource_perm_required: boolean
  allow_apply_permission: boolean
  labels: {
    id: number
    name: string
  }[]
}

export interface IMarketplaceDetails extends IMarketplaceItem {
  guideline: string
  tools: ITool[]
  maintainers: string[]
}

/**
 *  获取网关的 MCPServer 列表
 */
export const getMcpMarketplace = (data: IMarketplace) => http.get('/mcp-marketplace/servers/', data);

/**
 *  获取 MCP 市场中某个 Server 的详情
 * @param mcp_server_id  id
 */
export const getMcpServerDetails = (mcp_server_id: string) => http.get(`/mcp-marketplace/servers/${mcp_server_id}/`);

/**
 *  获取 MCP 市场中某个 Server 的某个工具的文档
 * @param mcp_server_id  id
 * @param tool_name  工具
 */
export const getMcpServerToolDoc = (mcp_server_id: number, tool_name: string) => http.get(`/mcp-marketplace/servers/${mcp_server_id}/tools/${tool_name}/doc/`);

/**
 *  环境发布前检查对应环境 MCP Server 是否存在资源变更
 * @param apigwId 网关id
 */
export const getStageReleaseCheckMcp = (apigwId: number, data: IStageReleaseCheckMcp) => http.get(`${path}/${apigwId}/mcp-servers/-/stage-release-check/`, data);

/**
 *  已授权应用列表
 * @param apigwId 网关id
 */
export const getMcpPermissions = (apigwId: number, mcp_server_id: number, data: IMcpPermissions) => http.get(`${path}/${apigwId}/mcp-servers/${mcp_server_id}/permissions/`, data);

/**
 *  主动授权
 * @param apigwId 网关id
 * @param data 创建参数
 */
export const authMcpPermissions = (apigwId: number, mcp_server_id: number, data: any) => http.post(`${path}/${apigwId}/mcp-servers/${mcp_server_id}/permissions/`, data);

/**
 *  已授权应用删除
 * @param apigwId 网关id
 * @param mcp_server_id MCP id
 */
export const deleteMcpPermissions = (apigwId: number, mcp_server_id: number, id: number) => http.delete(`${path}/${apigwId}/mcp-servers/${mcp_server_id}/permissions/${id}/`);

/**
 *  权限审批列表
 * @param apigwId 网关id
 */
export const getMcpAppPermissionApply = (apigwId: number, data: IMcpAppPermissionApply) => http.get(`${path}/${apigwId}/mcp-servers/${data?.mcp_server_id}/permissions/app-permission-apply/`, data);

/**
 *  授权审批申请人列表
 * @param apigwId 网关id
 */
export const getMcpPermissionsApplicant = (apigwId: number, mcp_server_id: number) => http.get(`${path}/${apigwId}/mcp-servers/${mcp_server_id}/permissions/app-permission-apply/applicant/`);

/**
 *  更新授权审批状态接口（通过 / 驳回）
 * @param apigwId 网关id
 * @param id mcp id
 * @param data 更新状态参数
 */
export const updateMcpPermissions = (apigwId: number, mcp_server_id: number, id: number, data: any) => http.patch(`${path}/${apigwId}/mcp-servers/${mcp_server_id}/permissions/app-permission-apply/${id}/status/`, data);

/**
 *  环境发布前检查对应环境 MCP Server 是否存在资源变更
 * @param apigwId 网关id
 */
export const checkMcpServersDel = (apigwId: number, data: {
  stage_id: number
  resource_version_id: number
}) =>
  http.get<{
    has_related_changes: boolean
    deleted_resource_count: number
    details: any[]
  }>(`${path}/${apigwId}/mcp-servers/-/stage-release-check/`, data);
