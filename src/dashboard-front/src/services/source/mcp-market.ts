import http from '../http';

const path = '/gateways';

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

export const checkMcpServersDel = (apigwId: number, data: {
  stage_id: number
  resource_version_id: number
}) =>
  http.get<{
    has_related_changes: boolean
    deleted_resource_count: number
    details: any[]
  }>(`${path}/${apigwId}/mcp-servers/-/stage-release-check/`, data);

/**
 *  获取 MCP 市场中某个 Server 的某个工具的文档
 * @param mcp_server_id  id
 * @param tool_name  工具
 */
export const getMcpServerToolDoc = (mcp_server_id: number, tool_name: string) =>
  http.get(`/mcp-marketplace/servers/${mcp_server_id}/tools/${tool_name}/doc/`);

/**
 *  已授权应用列表
 * @param apigwId 网关id
 * @param mcp_server_id
 * @param data
 */
export const getMcpPermissions = (apigwId: number, mcp_server_id: number, data: IMcpPermissions) =>
  http.get(`${path}/${apigwId}/mcp-servers/${mcp_server_id}/permissions/`, data);

/**
 *  主动授权
 * @param apigwId 网关id
 * @param mcp_server_id
 * @param data 创建参数
 */
export const authMcpPermissions = (apigwId: number, mcp_server_id: number, data: any) =>
  http.post(`${path}/${apigwId}/mcp-servers/${mcp_server_id}/permissions/`, data);

/**
 *  已授权应用删除
 * @param apigwId 网关id
 * @param mcp_server_id MCP id
 * @param id
 */
export const deleteMcpPermissions = (apigwId: number, mcp_server_id: number, id: number) =>
  http.delete(`${path}/${apigwId}/mcp-servers/${mcp_server_id}/permissions/${id}/`);

/**
 *  权限审批列表
 * @param apigwId 网关id
 * @param data
 */
export const getMcpAppPermissionApply = (apigwId: number, data: IMcpAppPermissionApply) =>
  http.get(`${path}/${apigwId}/mcp-servers/${data?.mcp_server_id}/permissions/app-permission-apply/`, data);

/**
 *  授权审批申请人列表
 * @param apigwId 网关id
 * @param mcp_server_id
 */
export const getMcpPermissionsApplicant = (apigwId: number, mcp_server_id: number) =>
  http.get(`${path}/${apigwId}/mcp-servers/${mcp_server_id}/permissions/app-permission-apply/applicant/`);

/**
 *  更新授权审批状态接口（通过 / 驳回）
 * @param apigwId 网关id
 * @param mcp_server_id
 * @param id mcp id
 * @param data 更新状态参数
 */
export const updateMcpPermissions = (apigwId: number, mcp_server_id: number, id: number, data: any) =>
  http.patch(`${path}/${apigwId}/mcp-servers/${mcp_server_id}/permissions/app-permission-apply/${id}/status/`, data);
