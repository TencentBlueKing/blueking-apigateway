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

const path = '/gateways';

export interface IMCPServer {
  id: number
  name: string
  description: string
  is_public: boolean
  labels: string[]
  resource_names: string[]
  tools_count: number
  url: string
  status: number
  stage: {
    id: number
    name: string
  }
  tools?: IMCPServerTool[]
}

export interface IMCPServerTool {
  id: number
  name: string
  description: string
  method: string
  path: string
  verified_user_required: boolean
  verified_app_required: string[]
  resource_perm_required: string[]
  allow_apply_permission: string[]
  labels: {
    id: number
    name: string
  }[]
}

// 列表
export const getServers = (apigwId: number): Promise<{ results: IMCPServer[] }> =>
  http.get(`${path}/${apigwId}/mcp-servers/`);

// 详情
export const getServer = (apigwId: number, serverId: number): Promise<IMCPServer> =>
  http.get(`${path}/${apigwId}/mcp-servers/${serverId}/`);

// 创建
export const createServer = (apigwId: number, data: {
  name: string
  description?: string
  stage_id: number
  is_public?: boolean
  labels?: string[]
  resource_names: string[]
}) => http.post(`${path}/${apigwId}/mcp-servers/`, data);

// 部分更新
export const patchServer = (apigwId: number, serverId: number, data: {
  description?: string
  is_public?: boolean
  labels?: string[]
  resource_names?: string[]
}) => http.patch(`${path}/${apigwId}/mcp-servers/${serverId}/`, data);

// 删除
export const deleteServer = (apigwId: number, serverId: number) =>
  http.delete(`${path}/${apigwId}/mcp-servers/${serverId}/`);

// 更新 MCPServer 状态，如启用、停用
export const patchServerStatus = (apigwId: number, serverId: number, data: { status: number }) =>
  http.patch(`${path}/${apigwId}/mcp-servers/${serverId}/status/`, data);

// 工具列表
export const getServerTools = (apigwId: number, mcp_server_id: number): Promise<IMCPServerTool[]> =>
  http.get(`${path}/${apigwId}/mcp-servers/${mcp_server_id}/tools/`);

// 工具文档
export const getServerToolDoc = (apigwId: number, mcp_server_id: number, tool_name: string): Promise<{
  type: string
  content: string
  updated_time: string
}> => http.get(`${path}/${apigwId}/mcp-servers/${mcp_server_id}/tools/${tool_name}/doc/`);

// 指引文档
export const getServerGuideDoc = (apigwId: number, mcp_server_id: number): Promise<{ content: string }> =>
  http.get(`${path}/${apigwId}/mcp-servers/${mcp_server_id}/guideline/`);
