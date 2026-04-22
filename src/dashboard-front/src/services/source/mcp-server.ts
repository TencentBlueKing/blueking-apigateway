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

import http from '../http';
import type { ICountAndResults } from '@/services/types/utils.ts';
import type {
  IMCPServerCategoryOutput,
  IMCPServerConfigListOutput,
  IMCPServerFilterOptionsOutput,
  IMCPServerGuidelineOutput,
  IMCPServerListOutput,
  IMCPServerRemotePromptsOutput,
  IMCPServerRetrieveOutput,
  IMCPServerToolDocOutput,
  IMCPServerToolOutput,
  IMCPServerUserCustomDocOutput,
} from '@/services/types/responses/gateways.ts';
import type {
  IGatewaysMcpServersCategoriesListQuery,
  IGatewaysMcpServersFilterOptionsListQuery,
  IGatewaysMcpServersListQuery,
  IGatewaysMcpServersRemotePromptsListQuery,
  IGatewaysMcpServersToolsListQuery,
} from '@/services/types/query/gateways.ts';
import type {
  IMCPServerCreateInputSLZ,
  IMCPServerRemotePromptsBatchInputSLZ,
  IMCPServerUserCustomDocInputSLZ,
} from '@/services/types/body/post/gateways.ts';
import type {
  IMCPServerUpdateInputSLZ,
  IMCPServerUpdateStatusInputSLZ,
} from '@/services/types/body/patch/gateways.ts';

const path = '/gateways';

// MCPServer列表
export interface IMCPServer {
  id: number
  name: string
  title?: string
  description: string
  is_public: boolean
  labels: (string | null)[]
  resource_names: string[]
  tool_names?: string[]
  tools_count: number
  url: string
  status: number
  protocol_type?: string
  stage: {
    id: number
    name: string
  }
  updated_time?: string
  created_time?: string
  categories?: string | string[]
  is_official?: boolean
  is_featured?: boolean
  prompts_count?: number
  oauth2_public_client_enabled?: boolean
  app_permission_risk?: any
  tools?: IMCPServerTool[]
  prompts?: IMCPServerPrompt[] | string
  order_by?: string
  [key: string]: any
}

// MCPServer工具
export interface IMCPServerTool {
  id: number
  name: string
  tool_name?: string
  description: string
  method: string
  path: string
  isOverflow?: boolean
  verified_user_required: boolean
  verified_app_required: boolean | string[]
  resource_perm_required: boolean | string[]
  allow_apply_permission: boolean | string[]
  labels: string | {
    id: number
    name: string
  }[]
}

// MCPServerPrompt
export interface IMCPServerPrompt {
  id: string
  name: string
  code: string
  content: string
  space_name: string
  space_code: string
  updated_by: string
  updated_time: string
  is_public: boolean
  is_no_perm?: boolean
  isOverflow?: boolean
  labels: string[]
}

// MCP列表搜索框
export interface IMCPServerFilterOptions {
  labels?: string[]
  stages?: {
    id: number
    name: string
  }[]
  categories?: {
    id: number
    name: string
    display_name: string
  }[]
}

// MCP分类
export interface IMCPServerCategory {
  name: string
  display_name: string
  description: string
  id: number
  sort_order: number
}

// MCP配置
export interface IMCPAIConfig {
  name: string
  display_name: string
  content: string
  install_url: string
}

//  McpServer创建/编辑基础表单信息
export interface IMCPFormData {
  name: string
  title: string
  description: string
  stage_id: number | null
  is_public: boolean
  oauth2_public_client_enabled: boolean
  raw_response_enabled: boolean
  labels: string[]
  categories: string[]
  protocol_type: string
  url?: string
}

// 列表
export const getServers = (apigwId: number, data: IGatewaysMcpServersListQuery) =>
  http.get<ICountAndResults<IMCPServerListOutput>>(`${path}/${apigwId}/mcp-servers/`, data);

// 详情
export const getServer = (apigwId: number, serverId: number) =>
  http.get<IMCPServerRetrieveOutput>(`${path}/${apigwId}/mcp-servers/${serverId}/`);

// 创建
export const createServer = (apigwId: number, data: IMCPServerCreateInputSLZ) =>
  http.post(`${path}/${apigwId}/mcp-servers/`, data);

// 部分更新
export const patchServer = (
  apigwId: number,
  serverId: number,
  data: IMCPServerUpdateInputSLZ,
) => http.patch(`${path}/${apigwId}/mcp-servers/${serverId}/`, data);

// 删除
export const deleteServer = (apigwId: number, serverId: number) =>
  http.delete(`${path}/${apigwId}/mcp-servers/${serverId}/`);

// 更新 MCPServer 状态，如启用、停用
export const patchServerStatus = (
  apigwId: number,
  serverId: number,
  data: IMCPServerUpdateStatusInputSLZ,
) => http.patch(`${path}/${apigwId}/mcp-servers/${serverId}/status/`, data);

// 工具列表
export const getServerTools = (apigwId: number, mcp_server_id: number, query: IGatewaysMcpServersToolsListQuery = {}) =>
  http.get<IMCPServerToolOutput[]>(`${path}/${apigwId}/mcp-servers/${mcp_server_id}/tools/`, query);

// 工具文档
export const getServerToolDoc = (apigwId: number, mcp_server_id: number, tool_name: string) =>
  http.get<IMCPServerToolDocOutput>(`${path}/${apigwId}/mcp-servers/${mcp_server_id}/tools/${tool_name}/doc/`);

// 指引文档
export const getServerGuideDoc = (apigwId: number, mcp_server_id: number) =>
  http.get<IMCPServerGuidelineOutput>(`${path}/${apigwId}/mcp-servers/${mcp_server_id}/guideline/`);

/**
 * 获取 MCPServer 用户自定义文档
 * @param {Number} apigwId 网关id
 * @param {Number} mcp_server_id mcpServer id
 */
export const getCustomServerGuideDoc = (apigwId: number, mcp_server_id: number) =>
  http.get<IMCPServerUserCustomDocOutput>(`${path}/${apigwId}/mcp-servers/${mcp_server_id}/user-custom-doc/`);

/**
 * 新建 MCPServer 用户自定义文档
 * @param {Number} apigwId 网关id
 * @param {Number} mcp_server_id mcpServer id
 * @param {String} data.content 自定义指引内容
 */
export const addCustomServerGuideDoc = (
  apigwId: number,
  mcp_server_id: number,
  data: IMCPServerUserCustomDocInputSLZ,
) => http.post(`${path}/${apigwId}/mcp-servers/${mcp_server_id}/user-custom-doc/`, data);

/**
 * 更新 MCPServer 用户自定义文档
 * @param {Number} apigwId 网关id
 * @param {Number} mcp_server_id mcpServer id
 * @param {String} data.content 自定义指引内容
 */
export const updateCustomServerGuideDoc = (
  apigwId: number,
  mcp_server_id: number,
  data: IMCPServerUserCustomDocInputSLZ,
) =>
  http.put(`${path}/${apigwId}/mcp-servers/${mcp_server_id}/user-custom-doc/`, data);

/**
 * 删除 MCPServer 用户自定义文档
 * @param {Number} apigwId 网关id
 * @param {Number} mcp_server_id mcpServer id
 */
export const deleteCustomServerGuideDoc = (apigwId: number, mcp_server_id: number) =>
  http.delete(`${path}/${apigwId}/mcp-servers/${mcp_server_id}/user-custom-doc/`);

/**
 * 获取 MCPServer 已关联的 Prompts 配置
 * @param {Number} apigwId 网关id
 */
export const getServerPrompts = (apigwId: number, query: IGatewaysMcpServersRemotePromptsListQuery = {}) =>
  http.get<IMCPServerRemotePromptsOutput>(`${path}/${apigwId}/mcp-servers/-/remote-prompts/`, query);

/**
 * 根据 PromptID 列表批量获取第三方平台 Prompts 内容
 * @param apigwId 网关id
 * @param {Number[]} data.ids 当前PromptID组
 */
export const getServerPromptsDetail = (apigwId: number, data: IMCPServerRemotePromptsBatchInputSLZ) =>
  http.post<IMCPServerPrompt>(`${path}/${apigwId}/mcp-servers/-/remote-prompts/batch/`, data);

/**
 * 获取 MCPServer 搜索过滤选项（环境、标签、分类）
 * @param apigwId 网关id
 */
export const getMcpServerFilterOptions = (apigwId: number, query: IGatewaysMcpServersFilterOptionsListQuery = {}) =>
  http.get<IMCPServerFilterOptionsOutput>(`${path}/${apigwId}/mcp-servers/-/filter-options/`, query);

/**
 * 获取可用的 MCPServer 分类列表（排除官方和精选）
 * @param apigwId 网关id
 */
export const getMcpCategoryList = (apigwId: number, query: IGatewaysMcpServersCategoriesListQuery = {}) =>
  http.get<IMCPServerCategoryOutput[]>(`${path}/${apigwId}/mcp-servers/-/categories/`, query);

/**
 * 获取 MCPServer 的配置列表（支持 Cursor、CodeBuddy、Claude、AIDev 等工具的配置）
 * @param apigwId 网关id
 */
export const getMcpAIConfigList = (apigwId: number, mcp_server_id: number): Promise<{ configs: IMCPAIConfig[] }> =>
  http.get<IMCPServerConfigListOutput>(`${path}/${apigwId}/mcp-servers/${mcp_server_id}/configs/`);
