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
import http, { withExtraQuery } from '@/services/http';
import type {
  ILogLinkOutput,
  ILogListOutput,
  IRequestLogDetailOutput,
  ITimeChartOutput,
} from '@/services/types/responses/gateways.ts';
import type {
  IGatewaysLogsExportListQuery,
  IGatewaysLogsListQuery,
  IGatewaysLogsReadQuery,
  IGatewaysLogsTimechartReadQuery,
} from '@/services/types/query/gateways.ts';

const path = '/gateways';

/**
 *  获取流水日志列表
 * @param gatewayId 网关id
 * @param params 查询参数
 * @param extraStr 额外检索串（include/exclude）
 */
export const getAccessLogList = (gatewayId: number, params: IGatewaysLogsListQuery = {}, extraStr?: string) =>
  http.get<ILogListOutput>(withExtraQuery(`${path}/${gatewayId}/logs/`, extraStr), params);

/**
 *  获取流水日志时间分布图
 * @param gatewayId 网关id
 * @param params 查询参数
 * @param extraStr 额外检索串（include/exclude）
 */
export const getAccessLogTimechart = (
  gatewayId: number,
  params: IGatewaysLogsTimechartReadQuery,
  extraStr?: string,
) =>
  http.get<ITimeChartOutput>(withExtraQuery(`${path}/${gatewayId}/logs/timechart/`, extraStr), params);

/**
 *  获取流水日志分享链接
 * @param gatewayId 网关id
 * @param params.request_id 请求id
 */
export const getAccessLogShareLink = (gatewayId: number, params: { request_id: string }) =>
  http.get<ILogLinkOutput>(`${path}/${gatewayId}/logs/${params.request_id}/link/`);

/**
 *  获取流水日志详情
 * @param gatewayId 网关id
 * @param requestId 请求id
 * @param params 查询参数
 */
export const getAccessLogDetail = (gatewayId: number, requestId: string, params: IGatewaysLogsReadQuery) =>
  http.get<IRequestLogDetailOutput>(`${path}/${gatewayId}/logs/${requestId}/`, params);

/**
 *  流水日志导出
 * @param gatewayId 网关id
 * @param data 导出参数
 * @param extraStr 额外检索串（include/exclude）
 */
export const exportAccessLogs = (gatewayId: number, data: IGatewaysLogsExportListQuery, extraStr?: string) =>
  http.get<unknown>(withExtraQuery(`${path}/${gatewayId}/logs/export/`, extraStr), data, { responseType: 'blob' });
