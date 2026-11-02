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

import http from '@/services/http';
import type { ICountAndResults } from '@/services/types/utils.ts';
import type {
  IMCPServerCategoryOutput,
  IMCPServerConfigListOutput,
  IMCPServerFilterOptionsOutput,
  IMCPServerGuidelineOutput,
  IMCPServerListOutput,
  IMCPServerRemotePromptsOutput,
  IMCPServerRetrieveOutput,
  IMCPServerStageReleaseCheckOutput,
  IMCPServerToolDocOutput,
  IMCPServerToolOutput,
  IMCPServerUserCustomDocOutput,
} from '@/services/types/responses/gateways.ts';
import type {
  IGatewaysMcpServersCategoriesListQuery,
  IGatewaysMcpServersFilterOptionsListQuery,
  IGatewaysMcpServersListQuery,
  IGatewaysMcpServersRemotePromptsListQuery,
  IGatewaysMcpServersStageReleaseCheckReadQuery,
  IGatewaysMcpServersToolsListQuery,
} from '@/services/types/query/gateways.ts';
import type {
  IMCPServerCreateInputSLZ,
  IMCPServerRemotePromptsBatchInputSLZ,
  IMCPServerUserCustomDocInputSLZ,
} from '@/services/types/body/post/gateways.ts';
import type { IMCPServerUpdateStatusInputSLZ } from '@/services/types/body/patch/gateways.ts';
import type { IMcpBatchConfigQuery } from '@/services/types/query/mcp-marketplace.ts';
import type { IMcpClientConfig } from '@/services/types/responses/mcp-marketplace.ts';
import type { IMCPAIConfig } from '@/types/mcp-server';

const path = '/gateways';

// 列表
export const getServers = (gatewayId: number, data: IGatewaysMcpServersListQuery) =>
  http.get<ICountAndResults<IMCPServerListOutput>>(`${path}/${gatewayId}/mcp-servers/`, data);

// 详情
export const getServer = (gatewayId: number, serverId: number) =>
  http.get<IMCPServerRetrieveOutput>(`${path}/${gatewayId}/mcp-servers/${serverId}/`);

// 创建
export const createServer = (gatewayId: number, data: Partial<IMCPServerCreateInputSLZ>) =>
  http.post(`${path}/${gatewayId}/mcp-servers/`, data);

// 部分更新
export const patchServer = (
  gatewayId: number,
  serverId: number,
  data: Partial<IMCPServerCreateInputSLZ>,
) => http.patch(`${path}/${gatewayId}/mcp-servers/${serverId}/`, data);

// 删除
export const deleteServer = (gatewayId: number, serverId: number) =>
  http.delete(`${path}/${gatewayId}/mcp-servers/${serverId}/`);

// 更新 MCPServer 状态，如启用、停用
export const patchServerStatus = (
  gatewayId: number,
  serverId: number,
  data: IMCPServerUpdateStatusInputSLZ,
) => http.patch(`${path}/${gatewayId}/mcp-servers/${serverId}/status/`, data);

// 工具列表
export const getServerTools = (
  gatewayId: number,
  mcp_server_id: number,
  query: IGatewaysMcpServersToolsListQuery = {},
) =>
  http.get<IMCPServerToolOutput[]>(`${path}/${gatewayId}/mcp-servers/${mcp_server_id}/tools/`, query);

// 工具文档
export const getServerToolDoc = (gatewayId: number, mcp_server_id: number, tool_name: string) =>
  http.get<IMCPServerToolDocOutput>(`${path}/${gatewayId}/mcp-servers/${mcp_server_id}/tools/${tool_name}/doc/`);

// 指引文档
export const getServerGuideDoc = (gatewayId: number, mcp_server_id: number) =>
  http.get<IMCPServerGuidelineOutput>(`${path}/${gatewayId}/mcp-servers/${mcp_server_id}/guideline/`);

/**
 * 获取 MCPServer 用户自定义文档
 * @param {Number} gatewayId 网关id
 * @param {Number} mcp_server_id mcpServer id
 */
export const getCustomServerGuideDoc = (gatewayId: number, mcp_server_id: number) =>
  http.get<IMCPServerUserCustomDocOutput>(`${path}/${gatewayId}/mcp-servers/${mcp_server_id}/user-custom-doc/`);

/**
 * 新建 MCPServer 用户自定义文档
 * @param {Number} gatewayId 网关id
 * @param {Number} mcp_server_id mcpServer id
 * @param {String} data.content 自定义指引内容
 */
export const addCustomServerGuideDoc = (
  gatewayId: number,
  mcp_server_id: number,
  data: IMCPServerUserCustomDocInputSLZ,
) => http.post(`${path}/${gatewayId}/mcp-servers/${mcp_server_id}/user-custom-doc/`, data);

/**
 * 更新 MCPServer 用户自定义文档
 * @param {Number} gatewayId 网关id
 * @param {Number} mcp_server_id mcpServer id
 * @param {String} data.content 自定义指引内容
 */
export const updateCustomServerGuideDoc = (
  gatewayId: number,
  mcp_server_id: number,
  data: IMCPServerUserCustomDocInputSLZ,
) =>
  http.put(`${path}/${gatewayId}/mcp-servers/${mcp_server_id}/user-custom-doc/`, data);

/**
 * 删除 MCPServer 用户自定义文档
 * @param {Number} gatewayId 网关id
 * @param {Number} mcp_server_id mcpServer id
 */
export const deleteCustomServerGuideDoc = (gatewayId: number, mcp_server_id: number) =>
  http.delete(`${path}/${gatewayId}/mcp-servers/${mcp_server_id}/user-custom-doc/`);

/**
 * 获取 MCPServer 已关联的 Prompts 配置
 * @param {Number} gatewayId 网关id
 */
export const getServerPrompts = (gatewayId: number, query: IGatewaysMcpServersRemotePromptsListQuery = {}) =>
  http.get<IMCPServerRemotePromptsOutput>(`${path}/${gatewayId}/mcp-servers/-/remote-prompts/`, query);

/**
 * 根据 PromptID 列表批量获取第三方平台 Prompts 内容
 * @param gatewayId 网关id
 * @param {Number[]} data.ids 当前PromptID组
 */
export const getServerPromptsDetail = (gatewayId: number, data: IMCPServerRemotePromptsBatchInputSLZ) =>
  http.post<IMCPServerRemotePromptsOutput>(`${path}/${gatewayId}/mcp-servers/-/remote-prompts/batch/`, data);

/**
 * 获取 MCPServer 搜索过滤选项（环境、标签、分类）
 * @param gatewayId 网关id
 */
export const getMcpServerFilterOptions = (gatewayId: number, query: IGatewaysMcpServersFilterOptionsListQuery = {}) =>
  http.get<IMCPServerFilterOptionsOutput>(`${path}/${gatewayId}/mcp-servers/-/filter-options/`, query);

/**
 * 获取可用的 MCPServer 分类列表（排除官方和精选）
 * @param gatewayId 网关id
 */
export const getMcpCategoryList = (gatewayId: number, query: IGatewaysMcpServersCategoriesListQuery = {}) =>
  http.get<IMCPServerCategoryOutput[]>(`${path}/${gatewayId}/mcp-servers/-/categories/`, query);

/**
 * 获取 MCPServer 的配置列表（支持 Cursor、CodeBuddy、Claude、AIDev 等工具的配置）
 * @param gatewayId 网关id
 */
export const getMcpServerConfigs = (gatewayId: number, mcp_server_id: number): Promise<{ configs: IMCPAIConfig[] }> =>
  http.get<IMCPServerConfigListOutput>(`${path}/${gatewayId}/mcp-servers/${mcp_server_id}/configs/`);

/**
 * 批量获取 MCPServer 配置（支持指定客户端类型：cursor, codebuddy, claude, vscode 等）
 * @param {Number} gatewayId 网关id
 * @param {String} data.client_type 客户端类型
 * @param {Number[]} data.mcp_server_ids  McpServerID组
 */
export const getMcpServerBatchConfigs = (
  gatewayId: number,
  data: IMcpBatchConfigQuery,
): Promise<IMcpClientConfig> =>
  http.post(`${path}/${gatewayId}/mcp-servers/-/batch-configs/`, data);

/**
 *  环境发布前检查对应环境 MCP Server 是否存在资源变更
 * @param gatewayId 网关id
 * @param data 查询参数
 */
export const checkMcpServerStageRelease = (gatewayId: number, data: IGatewaysMcpServersStageReleaseCheckReadQuery) =>
  http.get<IMCPServerStageReleaseCheckOutput>(`${path}/${gatewayId}/mcp-servers/-/stage-release-check/`, data);
