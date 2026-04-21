/*
 * TencentBlueKing is pleased to support the open source community by making
 * 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
 * Copyright (C) 2025 Tencent. All rights reserved.
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

import http from '../http';
import type {
  IMCPServerCategoryOutput,
  IMCPServerConfigItemOutput,
  IMCPServerConfigListOutput,
  IMCPServerListOutput,
  IMCPServerToolDocOutput,
  IMCPServerToolOutput,
} from '@/services/types/responses/mcp-marketplace.ts';
import type { ICountAndResults } from '@/services/types/utils.ts';
import type {
  IMCPServerAppPermissionApplyApplicantOutput,
  IMCPServerAppPermissionApplyListOutput,
  IMCPServerAppPermissionListOutput,
  IMCPServerStageReleaseCheckOutput,
} from '@/services/types/responses/gateways.ts';
import type {
  IMCPMarketplaceCategoriesGetQuery,
  IMCPMarketplaceServersGetQuery,
} from '@/services/types/query/mcp-marketplace.ts';
import type {
  IGatewaysMcpServersAppPermissionApplyListQuery,
  IGatewaysMcpServersPermissionsAppPermissionApplyApplicantListQuery,
  IGatewaysMcpServersPermissionsListQuery,
  IGatewaysMcpServersStageReleaseCheckReadQuery,
} from '@/services/types/query/gateways.ts';
import type { IMCPServerAppPermissionCreateInputSLZ } from '@/services/types/body/post/gateways.ts';
import type { IMCPServerAppPermissionApplyUpdateInputSLZ } from '@/services/types/body/patch/gateways.ts';

const path = '/gateways';

export interface IMarketplaceItem {
  id: number
  name: string
  description: string
  is_public: boolean
  is_official: boolean
  is_featured: boolean
  labels: string[]
  resource_names: string[]
  tool_names: string[]
  status: number
  tools_count: number
  prompts_count: number
  url: string
  protocol_type: string
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

export interface IPrompts {
  id: number
  name: string
  code: string
  content: string
  updated_time: string
  updated_by: string
  labels: string[]
  space_code: string
  space_name: string
  is_public: boolean
}

export interface IMarketplaceDetails extends IMarketplaceItem {
  guideline: string
  oauth2_public_client_enabled: boolean
  raw_response_enabled: boolean
  tools: ITool[]
  prompts?: IPrompts[]
  maintainers: string[]
}

export interface IMCPMarketCategory {
  name: string
  display_name: string
  description: string
  id: number
  sort_order: number
  mcp_server_count: number
}

// MCP配置
export interface IMarketplaceConfig {
  name: string
  display_name: string
  content: string
  install_url: string
}

/**
 *  获取网关的 MCPServer 列表
 */
export const getMcpMarketplace = (data: IMCPMarketplaceServersGetQuery) =>
  http.get<ICountAndResults<IMCPServerListOutput>>('/mcp-marketplace/servers/', data);

/**
 *  获取 MCP 市场中某个 Server 的详情
 * @param mcp_server_id  id
 */
export const getMcpServerDetails = (mcp_server_id: string) =>
  http.get<IMCPServerToolOutput>(`/mcp-marketplace/servers/${mcp_server_id}/`);

/**
 *  环境发布前检查对应环境 MCP Server 是否存在资源变更
 * @param apigwId 网关id
 */
export const checkMcpServersDel = (apigwId: number, data: IGatewaysMcpServersStageReleaseCheckReadQuery) =>
  http.get<IMCPServerStageReleaseCheckOutput>(`${path}/${apigwId}/mcp-servers/-/stage-release-check/`, data);

/**
 *  获取 MCP 市场中某个 Server 的某个工具的文档
 * @param mcp_server_id  id
 * @param tool_name  工具
 */
export const getMcpServerToolDoc = (mcp_server_id: number, tool_name: string) =>
  http.get<IMCPServerToolDocOutput>(`/mcp-marketplace/servers/${mcp_server_id}/tools/${tool_name}/doc/`);

/**
 *  已授权应用列表
 * @param apigwId 网关id
 * @param mcp_server_id
 * @param data
 */
export const getMcpPermissions = (
  apigwId: number,
  mcp_server_id: number,
  data: IGatewaysMcpServersPermissionsListQuery = {},
) =>
  http.get<ICountAndResults<IMCPServerAppPermissionListOutput>>(`${path}/${apigwId}/mcp-servers/${mcp_server_id}/permissions/`, data);

/**
 *  主动授权
 * @param apigwId 网关id
 * @param mcp_server_id
 * @param data 创建参数
 */
export const authMcpPermissions = (
  apigwId: number,
  mcp_server_id: number,
  data: IMCPServerAppPermissionCreateInputSLZ,
) =>
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
export const getMcpAppPermissionApply = (apigwId: number, data: IGatewaysMcpServersAppPermissionApplyListQuery) =>
  http.get<ICountAndResults<IMCPServerAppPermissionApplyListOutput>>(`${path}/${apigwId}/mcp-servers/-/app-permission-apply/`, data);

/**
 *  授权审批申请人列表
 * @param apigwId 网关id
 * @param mcp_server_id
 */
export const getMcpPermissionsApplicant = (
  apigwId: number,
  mcp_server_id: number,
  query: IGatewaysMcpServersPermissionsAppPermissionApplyApplicantListQuery,
) =>
  http.get<IMCPServerAppPermissionApplyApplicantOutput>(`${path}/${apigwId}/mcp-servers/${mcp_server_id}/permissions/app-permission-apply/applicant/`, query);

/**
 *  更新授权审批状态接口（通过 / 驳回）
 * @param apigwId 网关id
 * @param mcp_server_id
 * @param id mcp id
 * @param data 更新状态参数
 */
export const updateMcpPermissions = (
  apigwId: number,
  mcp_server_id: number,
  id: number,
  data: IMCPServerAppPermissionApplyUpdateInputSLZ,
) =>
  http.patch(`${path}/${apigwId}/mcp-servers/${mcp_server_id}/permissions/app-permission-apply/${id}/status/`, data);

/**
 *  获取 MCP 市场分类列表
 */
export const getMcpMarketplaceCategories = (data: IMCPMarketplaceCategoriesGetQuery) =>
  http.get<IMCPServerCategoryOutput[]>('/mcp-marketplace/categories/', data);

/**
 *获取 MCP 市场中某个 Server 的配置列表（支持 Cursor、CodeBuddy、Claude、AIDev 等工具的配置）
 */
export const getMcpAIConfigList = (mcp_server_id: number) =>
  http.get<IMCPServerConfigListOutput>(`/mcp-marketplace/servers/${mcp_server_id}/configs/`);
