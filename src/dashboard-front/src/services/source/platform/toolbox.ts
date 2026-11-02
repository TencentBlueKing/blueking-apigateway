/*
 * TencentBlueKing is pleased to support the open source community by making
 * 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
 * Copyright (C) Tencent. All rights reserved.
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
* 平台工具箱相关 API（按请求 ID 查询，无需网关权限）
*  */

import http from '@/services/http';
import type {
  IMCPServerChainLogListOutput,
  IMCPServerLogChainOutput,
  IMCPServerLogQuerySummaryOutput,
  IRequestLogOutput,
} from '@/services/types/responses/gateways.ts';

const path = '/gateways';

/**
 *  根据 request_id 查询网关流水日志
 * @param requestId 请求id
 */
export const queryAccessLogByRequestId = (requestId: string) =>
  http.get<IRequestLogOutput>(`${path}/logs/query/${requestId}/`);

/**
 *  根据 request_id 或 x_request_id 查询 MCP Server 日志（含上下游网关日志）
 * @param requestId 请求id 或全链路请求id
 */
export const queryMcpLogByRequestId = (requestId: string) =>
  http.get<IMCPServerChainLogListOutput>(`${path}/mcp-server-logs/query/${requestId}/`);

/**
 *  根据 request_id 或 x_request_id 查询 MCP Server 调用链汇总信息
 * @param requestId 请求id 或全链路请求id
 */
export const queryMcpLogSummary = (requestId: string) =>
  http.get<IMCPServerLogQuerySummaryOutput>(`${path}/mcp-server-logs/query/${requestId}/summary/`);

/**
 *  根据 request_id 或 x_request_id 查询 MCP Server 调用链路详情
 * @param requestId 请求id 或全链路请求id
 */
export const queryMcpLogChain = (requestId: string) =>
  http.get<IMCPServerLogChainOutput>(`${path}/mcp-server-logs/query/${requestId}/chain/`);
