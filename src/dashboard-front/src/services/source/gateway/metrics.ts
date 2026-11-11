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
* 网关指标相关 API（仪表盘时序 / 瞬时指标、统计报表汇总）
*  */

import http from '@/services/http';
import type {
  IMetricInstantOutput,
  IMetricRangeOutput,
  IMetricSummaryCallerOutput,
  IMetricSummaryOutput,
} from '@/services/types/responses/gateways.ts';
import type {
  IGatewaysMetricsQueryInstantListQuery,
  IGatewaysMetricsQueryRangeListQuery,
  IGatewaysMetricsQuerySummaryCallerListQuery,
  IGatewaysMetricsQuerySummaryExportListQuery,
  IGatewaysMetricsQuerySummaryListQuery,
} from '@/services/types/query/gateways.ts';

const path = '/gateways';

/**
 *  查询时序指标
 * @param gatewayId 网关id
 * @param params 查询参数
 */
export const queryMetricsRange = (gatewayId: number, params: IGatewaysMetricsQueryRangeListQuery) =>
  http.get<IMetricRangeOutput>(`${path}/${gatewayId}/metrics/query-range/`, params, { catchError: true });

/**
 *  查询瞬时指标（如请求总数、健康率）
 * @param gatewayId 网关id
 * @param params 查询参数
 */
export const queryMetricsInstant = (gatewayId: number, params: IGatewaysMetricsQueryInstantListQuery) =>
  http.get<IMetricInstantOutput>(`${path}/${gatewayId}/metrics/query-instant/`, params);

/**
 *  查询请求总量 / 失败总量
 * @param gatewayId 网关id
 * @param params 查询参数
 */
export const getMetricsSummary = (gatewayId: number, params: IGatewaysMetricsQuerySummaryListQuery) =>
  http.get<IMetricSummaryOutput>(`${path}/${gatewayId}/metrics/query-summary/`, params);

/**
 *  资源应用统计导出
 * @param gatewayId 网关id
 * @param data 导出参数
 */
export const exportMetricsSummary = (gatewayId: number, data: IGatewaysMetricsQuerySummaryExportListQuery) =>
  http.get<unknown>(`${path}/${gatewayId}/metrics/query-summary/export/`, data, { responseType: 'blob' });

/**
 *  查询调用方列表
 * @param gatewayId 网关id
 * @param params 查询参数
 */
export const getMetricsSummaryCallers = (gatewayId: number, params: IGatewaysMetricsQuerySummaryCallerListQuery) =>
  http.get<IMetricSummaryCallerOutput>(`${path}/${gatewayId}/metrics/query-summary/caller/`, params);
