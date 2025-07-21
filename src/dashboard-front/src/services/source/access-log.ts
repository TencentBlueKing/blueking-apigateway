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

export interface SearchParamsInterface {
  stage_id?: number // 阶段ID，可选
  resource_id?: string | number // 资源ID，可以是字符串或数字，可选
  time_start?: string | number // 开始时间，可以是字符串或数字，可选
  time_end?: string | number // 结束时间，可以是字符串或数字，可选
  query?: string // 查询字符串，可选
}

export interface ChartInterface {
  offset?: number // 偏移量，可选
  limit?: number // 限制数量，可选
  query?: string // 查询字符串，可选
  time_range?: number // 时间范围，可选
  time_start?: string | number // 开始时间，可以是字符串或数字，可选
  time_end?: string | number // 结束时间，可以是字符串或数字，可选
}

export interface LogDetailInterface {
  offset?: number // 偏移量，可选
  limit?: number // 限制数量，可选
  bk_nonce: string // 随机数，用于安全验证
  bk_signature: string // 签名，用于安全验证
  bk_timestamp: string // 时间戳，用于安全验证
  shared_by: string // 共享者信息
}

/**
 *  获取流程日志列表
 * @param gatewayId 网关id
 */
export const fetchApigwAccessLogList = (gatewayId: number, params: ChartInterface, extraStr?: string) => http.get(`${path}/${gatewayId}/logs/?${json2Query(params)}${extraStr}`);

/**
 *  获取流程日志chart
 * @param gatewayId 网关id
 */
export const fetchApigwAccessLogChart = (gatewayId: number, params: ChartInterface, extraStr?: string) => http.get(`${path}/${gatewayId}/logs/timechart/?${json2Query(params)}${extraStr}`);

/**
 *  获取流程日志link
 * @param gatewayId 网关id
 */
export const fetchApigwAccessLogShareLink = (gatewayId: number, params: { request_id: string }) => http.get(`${path}/${gatewayId}/logs/${params.request_id}/link/`);

/**
 *  获取流程日志详情
 * @param gatewayId 网关id
 */
export const fetchApigwAccessLogDetail = (gatewayId: number, requestId: string, params: LogDetailInterface) => http.get(`${path}/${gatewayId}/logs/${requestId}/?${json2Query(params)}`);

/**
 *  根据 request_id 查询日志
 */
export const getLogsInfo = (requestId: string) => http.get(`${path}/logs/query/${requestId}/`);

/**
 *  获取stage数据
 * @param gatewayId 网关id
 */
export const fetchApigwStages = (gatewayId: number, params: any) => http.get(`${path}/${gatewayId}/stages/?${json2Query(params)}`);
