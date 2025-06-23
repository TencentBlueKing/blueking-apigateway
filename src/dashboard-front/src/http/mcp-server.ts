/*
* MCP Server 相关 API
*  */

import fetch from './fetch';

// import { json2Query } from '@/common/util';

export interface IMCPServer {
  id: number,
  name: string,
  description: string,
  is_public: boolean,
  labels: string[],
  resource_names: string[],
  tools_count: number,
  url: string,
  status: number,
  stage: {
    id: number,
    name: string,
  },
  tools?: IMCPServerTool[]
}

export interface IMCPServerTool {
  id: number,
  name: string,
  description: string,
  method: string,
  path: string,
  verified_user_required: boolean,
  verified_app_required: string[],
  resource_perm_required: string[],
  allow_apply_permission: string[],
  labels: { id: number, name: string }[],
}

const { BK_DASHBOARD_URL } = window;

// 列表
export const getServers = (apigwId: number): Promise<{
  results: IMCPServer[]
}> => fetch.get(`${BK_DASHBOARD_URL}/gateways/${apigwId}/mcp-servers/`);

// 详情
export const getServer = (apigwId: number, serverId: number): Promise<IMCPServer> => fetch.get(`${BK_DASHBOARD_URL}/gateways/${apigwId}/mcp-servers/${serverId}/`);

// 创建
export const createServer = (apigwId: number, data: {
  name: string,
  description?: string,
  stage_id: number,
  is_public?: boolean,
  labels?: string[],
  resource_names: string[],
}) => fetch.post(`${BK_DASHBOARD_URL}/gateways/${apigwId}/mcp-servers/`, data);

// 部分更新
export const patchServer = (apigwId: number, serverId: number, data: {
  description?: string,
  is_public?: boolean,
  labels?: string[],
  resource_names?: string[],
}) => fetch.patch(`${BK_DASHBOARD_URL}/gateways/${apigwId}/mcp-servers/${serverId}/`, data);

// 删除
export const deleteServer = (apigwId: number, serverId: number) => fetch.delete(`${BK_DASHBOARD_URL}/gateways/${apigwId}/mcp-servers/${serverId}/`);

// 更新 MCPServer 状态，如启用、停用
export const patchServerStatus = (apigwId: number, serverId: number, data: {
  status: number,
}) => fetch.patch(`${BK_DASHBOARD_URL}/gateways/${apigwId}/mcp-servers/${serverId}/status/`, data);

// 工具列表
export const getServerTools = (apigwId: number, mcp_server_id: number): Promise<IMCPServerTool[]> => fetch.get(`${BK_DASHBOARD_URL}/gateways/${apigwId}/mcp-servers/${mcp_server_id}/tools/`);

// 工具文档
export const getServerToolDoc = (apigwId: number, mcp_server_id: number, tool_name: string): Promise<{
  type: string,
  content: string,
  updated_time: string,
}> => fetch.get(`${BK_DASHBOARD_URL}/gateways/${apigwId}/mcp-servers/${mcp_server_id}/tools/${tool_name}/doc/`);

// 指引文档
export const getServerGuideDoc = (apigwId: number, mcp_server_id: number): Promise<{
  content: string,
}> => fetch.get(`${BK_DASHBOARD_URL}/gateways/${apigwId}/mcp-servers/${mcp_server_id}/guideline/`);
