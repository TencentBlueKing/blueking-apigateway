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
* 网关下 MCP Server 指标相关 API
*  */

import http from '@/services/http';
import type { IObservabilitySearchParams } from '@/services/source/gateway/mcp-server/log';
import type {
  IMCPServerMetricInstantOutput,
  IMCPServerMetricRangeOutput,
} from '@/services/types/responses/gateways.ts';

const path = '/gateways';

/**
 *  查询 MCP Server 时序图指标
 * @param gatewayId 网关id
 * @param params 查询参数
 */
export const queryMcpMetricsRange = (gatewayId: number, params: IObservabilitySearchParams) =>
  http.get<IMCPServerMetricRangeOutput>(`${path}/${gatewayId}/mcp-servers/-/metrics/query-range/`, params);

/**
 *  查询 MCP Server 瞬时值指标
 * @param gatewayId 网关id
 * @param params 查询参数
 */
export const queryMcpMetricsInstant = (gatewayId: number, params: IObservabilitySearchParams) =>
  http.get<IMCPServerMetricInstantOutput>(`${path}/${gatewayId}/mcp-servers/-/metrics/query-instant/`, params);
