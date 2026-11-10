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
* 网关下 MCP Server 日志与调用链相关 API
*  */

import http, { withExtraQuery } from '@/services/http';
import type { IPagination } from '@/types/common';
import type {
  IMCPServerChainLogListOutput,
  IMCPServerLogChainOutput,
  IMCPServerLogListOutput,
  IMCPServerLogTimeChartOutput,
} from '@/services/types/responses/gateways.ts';

const path = '/gateways';

// 查询条件泛型
export interface IObservabilityBasicForm {
  time_start?: number
  time_end?: number
  time_range?: number
  app_code?: string
  request_id?: string
  status?: string
  query?: string
  metrics?: string
  step?: string
  mcp_server_name?: string
}

// 流水日志和仪表盘数据图层请求参数泛型
export type IObservabilitySearchParams = IObservabilityBasicForm & IPagination;

/**
 *  查询 MCP Server 日志时间分布图
 * @param gatewayId 网关id
 * @param params 搜索参数
 * @param extraStr 额外检索串（include/exclude）
 */
export const getMcpLogTimechart = (gatewayId: number, params: IObservabilityBasicForm, extraStr?: string) =>
  http.get<IMCPServerLogTimeChartOutput>(withExtraQuery(`${path}/${gatewayId}/mcp-servers/-/logs/timechart/`, extraStr), params);

/**
 *  查询 MCP Server 日志列表
 * @param gatewayId 网关id
 * @param params 搜索参数
 * @param extraStr 额外检索串（include/exclude）
 */
export const getMcpLogList = (gatewayId: number, params: IObservabilitySearchParams, extraStr?: string) =>
  http.get<IMCPServerLogListOutput>(withExtraQuery(`${path}/${gatewayId}/mcp-servers/-/logs/`, extraStr), params);

/**
 *  根据 request_id 获取 MCP Server 日志详情（调用链扁平化后的日志列表）
 * @param gatewayId 网关id
 * @param requestId 请求id
 * @param params 搜索参数
 */
export const getMcpLogDetail = (gatewayId: number, requestId: string, params: IObservabilitySearchParams) =>
  http.get<IMCPServerChainLogListOutput>(`${path}/${gatewayId}/mcp-servers/-/logs/${requestId}/`, params);

/**
 *  根据 request_id 查询 MCP Server 调用链路（瀑布图数据）
 * @param gatewayId 网关id
 * @param requestId 请求id
 */
export const getMcpLogChain = (gatewayId: number, requestId: string) =>
  http.get<IMCPServerLogChainOutput>(`${path}/${gatewayId}/mcp-servers/-/logs/${requestId}/chain/`);

/**
 *  导出 MCP Server 日志
 * @param gatewayId 网关id
 * @param params 导出参数
 * @param extraStr 额外检索串（include/exclude）
 */
export const exportMcpLogs = (gatewayId: number, params: IObservabilitySearchParams, extraStr?: string) =>
  http.get<unknown>(
    withExtraQuery(`${path}/${gatewayId}/mcp-servers/-/logs/export/`, extraStr),
    params,
    { responseType: 'blob' },
  );
