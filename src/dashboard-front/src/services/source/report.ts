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
import { blobDownLoad } from '@/utils';

const path = '/gateways';

// 搜索参数类型接口
export interface ISearchParamsType {
  stage_id?: number // 阶段ID，可选
  resource_id?: string // 资源ID，可选
  bk_app_code?: string // 蓝鲸应用代码，可选
  metrics?: string // 指标，可选
  time_dimension?: string // 时间维度，可选
  time_start?: number // 起始时间，可选
  time_end?: number // 结束时间，可选
  limit?: number // 限制条数，可选
  offset?: number // 偏移量，可选
}

// 系列项类型接口
export interface ISeriesItemType {
  alias: string // 别名
  datapoints: Array<Array<number>> // 数据点数组
  dimensions: object // 维度对象
  metric_field: string // 指标字段
  target: string // 目标
  unit: string // 单位
}

// 图表数据加载状态接口
export interface IChartDataLoading {
  requests_total?: boolean // 总请求数加载状态，可选
  requests_failed_total?: boolean // 失败请求数加载状态，可选
}

/**
 *  日志导出
 * @param apigwId 网关id
 * @param data 导出参数
 */
export const exportLogs = async (apigwId: number, data: any, extraStr?: string) => {
  const res = await http.get(`${path}/${apigwId}/logs/export/?${extraStr}`, data, { responseType: 'blob' });
  return blobDownLoad(res);
};

/**
 *  查询请求总量/失败总量接口
 * @param apigwId 网关id
 */
export const getReportSummary = (apigwId: number, params: any) => http.get(`${path}/${apigwId}/metrics/query-summary/`, params);

/**
 *  请求总量/失败请求总量导出接口
 * @param apigwId 网关id
 * @param data 导出参数
 */
export const exportReportSummary = async (apigwId: number, data: any) => {
  const res = await http.get(`${path}/${apigwId}/metrics/query-summary/export/`, data, { responseType: 'blob' });
  return blobDownLoad(res);
};

/**
 *  查询调用方接口
 * @param apigwId 网关id
 */
export const getCallers = (apigwId: number, params: any) => http.get(`${path}/${apigwId}/metrics/query-summary/caller/`, params);
