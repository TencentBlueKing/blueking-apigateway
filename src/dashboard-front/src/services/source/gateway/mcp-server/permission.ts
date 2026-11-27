/*
 * TencentBlueKing is pleased to support the open source community by making
 * 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
 * Copyright (C) 2026 Tencent. All rights reserved.
 * Licensed under the MIT License (the "License"); you may not use this file except
 * in compliance with the License. You may obtain a copy of the License at
 *
 *     http://opensource.org/licenses/MIT
 *
 * Unless required by applicable law or agreed to in writing, software distributed under
 * the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND,
 * either express or implied. See the License for the specific language governing permissions and
 * limitations under the License.
 *
 * We undertake not to change the open source license (MIT license) applicable
 * to the current version of the project delivered to anyone in the future.
 */

/*
* 网关下 MCP Server 应用权限相关 API（授权、审批、导出）
*  */

import http from '@/services/http';
import type { ICountAndResults } from '@/services/types/utils.ts';
import type {
  IGatewaysMcpServersAppPermissionApplyListQuery,
  IGatewaysMcpServersPermissionsAppPermissionApplyApplicantListQuery,
  IGatewaysMcpServersPermissionsListQuery,
  IMCPServerAppPermissionAppCodeListOutput,
  IMCPServerAppPermissionApplyApplicantOutput,
  IMCPServerAppPermissionApplyListOutput,
  IMCPServerAppPermissionApplyPendingCountOutput,
  IMCPServerAppPermissionApplyUpdateInputSLZ,
  IMCPServerAppPermissionCreateInputSLZ,
  IMCPServerAppPermissionExportInput,
  IMCPServerAppPermissionListOutput,
} from '@/services/types/gateway/mcp-server/permission.ts';

const path = '/gateways';

/**
 *  已授权应用列表
 * @param gatewayId 网关id
 * @param data 查询参数
 */
export const getMcpAppPermissionList = (
  gatewayId: number,
  data: IGatewaysMcpServersPermissionsListQuery = {},
) =>
  http.get<ICountAndResults<IMCPServerAppPermissionListOutput>>(`${path}/${gatewayId}/mcp-servers/-/permissions/app-permissions/`, data);

/**
 *  导出网关下 MCPServer 应用权限列表
 * @param gatewayId 网关id
 * @param data 导出参数
 */
export const exportMcpAppPermissions = (
  gatewayId: number,
  data: IMCPServerAppPermissionExportInput,
) =>
  http.post<void>(`${path}/${gatewayId}/mcp-servers/-/permissions/app-permissions/-/export/`, data, {
    responseType: 'blob',
    catchError: true,
  });

/**
 *  主动授权
 * @param gatewayId 网关id
 * @param mcp_server_id MCP Server id
 * @param data 授权参数
 */
export const grantMcpAppPermission = (
  gatewayId: number,
  mcp_server_id: number,
  data: IMCPServerAppPermissionCreateInputSLZ,
) =>
  http.post<void>(`${path}/${gatewayId}/mcp-servers/${mcp_server_id}/permissions/`, data);

/**
 *  删除已授权应用
 * @param gatewayId 网关id
 * @param mcp_server_id MCP Server id
 * @param id 应用权限id
 */
export const deleteMcpAppPermission = (gatewayId: number, mcp_server_id: number, id: number) =>
  http.delete<void>(`${path}/${gatewayId}/mcp-servers/${mcp_server_id}/permissions/${id}/`);

/**
 *  权限审批列表
 * @param gatewayId 网关id
 * @param data 查询参数
 */
export const getMcpAppPermissionApplyList = (gatewayId: number, data: IGatewaysMcpServersAppPermissionApplyListQuery) =>
  http.get<ICountAndResults<IMCPServerAppPermissionApplyListOutput>>(`${path}/${gatewayId}/mcp-servers/-/permissions/app-permission-apply/`, data);

/**
 *  待审批的应用权限申请数量（用于左侧菜单红点提示）
 * @param gatewayId 网关id
 */
export const getMcpAppPermissionApplyPendingCount = (gatewayId: number) =>
  http.get<IMCPServerAppPermissionApplyPendingCountOutput>(`${path}/${gatewayId}/mcp-servers/-/permissions/app-permission-apply/-/pending-count/`);

/**
 *  授权审批申请人列表
 * @param gatewayId 网关id
 * @param mcp_server_id MCP Server id
 * @param query 查询参数
 */
export const getMcpAppPermissionApplicants = (
  gatewayId: number,
  mcp_server_id: number | string,
  query: IGatewaysMcpServersPermissionsAppPermissionApplyApplicantListQuery,
) =>
  http.get<IMCPServerAppPermissionApplyApplicantOutput>(`${path}/${gatewayId}/mcp-servers/${mcp_server_id}/permissions/app-permission-apply/applicant/`, query);

/**
 *  更新授权审批状态（通过 / 驳回）
 * @param gatewayId 网关id
 * @param mcp_server_id MCP Server id
 * @param id 权限申请单id
 * @param data 更新状态参数
 */
export const patchMcpAppPermissionApplyStatus = (
  gatewayId: number,
  mcp_server_id: number,
  id: number,
  data: IMCPServerAppPermissionApplyUpdateInputSLZ,
) =>
  http.patch<void>(`${path}/${gatewayId}/mcp-servers/${mcp_server_id}/permissions/app-permission-apply/${id}/status/`, data);

/**
 *  查询有 MCPServer 调用权限的 bk_app_code 列表（网关级别）
 * @param gatewayId 网关id
 */
export const getMcpAppPermissionAppCodes = (gatewayId: number) =>
  http.get<IMCPServerAppPermissionAppCodeListOutput>(`${path}/${gatewayId}/mcp-servers/-/permissions/app-permission-app-codes/`);
