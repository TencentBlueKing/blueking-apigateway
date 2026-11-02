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
* MCP 市场相关 API
*  */

import http from '@/services/http';
import type {
  IMCPServerCategoryOutput,
  IMCPServerConfigListOutput,
  IMCPServerListOutput,
  IMCPServerRetrieveOutput,
  IMCPServerToolDocOutput,
  IMarketplacePermissionApplyOutput,
  IMcpClientConfig,
} from '@/services/types/responses/mcp-marketplace.ts';
import type { ICountAndResults } from '@/services/types/utils.ts';
import type {
  IMCPMarketplaceCategoriesGetQuery,
  IMCPMarketplaceServersGetQuery,
  IMcpBatchConfigQuery,
} from '@/services/types/query/mcp-marketplace.ts';

const path = '/mcp-marketplace';

/** MCP 市场权限申请请求体 */
export interface IMarketplacePermissionApplyInput {
  bk_app_code: string
  reason: string
}

/**
 *  获取 MCP 市场的 MCPServer 列表
 */
export const getMcpMarketplace = (data: IMCPMarketplaceServersGetQuery) =>
  http.get<ICountAndResults<IMCPServerListOutput>>(`${path}/servers/`, data);

/**
 *  获取 MCP 市场中某个 Server 的详情
 * @param mcp_server_id  id
 */
export const getMcpServerDetails = (mcp_server_id: string) =>
  http.get<IMCPServerRetrieveOutput>(`${path}/servers/${mcp_server_id}/`);

/**
 *  获取 MCP 市场中某个 Server 的某个工具的文档
 * @param mcp_server_id  id
 * @param tool_name  工具
 */
export const getMcpServerToolDoc = (mcp_server_id: number, tool_name: string) =>
  http.get<IMCPServerToolDocOutput>(`${path}/servers/${mcp_server_id}/tools/${tool_name}/doc/`);

/**
 *  获取 MCP 市场分类列表
 */
export const getMcpMarketplaceCategories = (data: IMCPMarketplaceCategoriesGetQuery) =>
  http.get<IMCPServerCategoryOutput[]>(`${path}/categories/`, data);

/**
 * 获取 MCP 市场中某个 Server 的配置列表（支持 Cursor、CodeBuddy、Claude、AIDev 等工具的配置）
 * @param mcp_server_id  id
 */
export const getMarketplaceServerConfigs = (mcp_server_id: number) =>
  http.get<IMCPServerConfigListOutput>(`${path}/servers/${mcp_server_id}/configs/`);

/**
 * MCP 市场批量获取 MCPServer 配置（支持指定客户端类型：cursor, codebuddy, claude, vscode 等）
 * @param {String} data.client_type 客户端类型
 * @param {Number[]} data.mcp_server_ids  McpServerID组
 */
export const getMarketplaceBatchConfigs = (data: IMcpBatchConfigQuery): Promise<IMcpClientConfig> =>
  http.post(`${path}/batch-configs/`, data);

/**
 *  发起 MCPServer 权限申请
 * @param mcp_server_id MCP Server id
 * @param data 申请参数
 */
export const marketplacePermissionApply = (
  mcp_server_id: number,
  data: IMarketplacePermissionApplyInput,
) =>
  http.post<IMarketplacePermissionApplyOutput>(`${path}/servers/${mcp_server_id}/app-permission-apply/`, data);
