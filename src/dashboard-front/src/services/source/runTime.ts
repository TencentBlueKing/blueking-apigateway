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

const path = '/esb/status/systems/';

export interface ITimeChartParams {
  system: string
  type?: string
  start?: number
  end?: number
  appCode?: string
  requestUrl?: string
  componentName?: string
}

export interface ITimeChartResponse {
  system: string
  type?: string
  start?: number
  end?: number
  appCode?: string
  requestUrl?: string
  componentName?: string
}

/**
 *  查询 runner
 * @param timeRange 查询运行时间
 */
export function getApigwRuntime({ timeRange }: any) {
  return http.get(`${path}summary/?time_since=${timeRange}`);
}

/**
 *  查询 time-line
 * @param
 */
export function getApigwTimeline() {
  return http.get(`${path}events/timeline/`);
}

export function getApigwSystemSummary({ system, start, end }: ITimeChartParams) {
  return http.get(`${path}${system}/summary/?time_since=custom&mts_start=${start}&mts_end=${end}`);
}

export function getApigwChartDetail({ system, start, end }: ITimeChartParams) {
  return http.get(`${path}${system}/date-histogram/?time_interval=1m&mts_start=${start}&mts_end=${end}`);
}

export function getApigwRuntimeRequest({ type, system, start, end }: ITimeChartParams) {
  return http.get(`${path}${system}/details/group-by/?time_since=custom&mts_start=${start}&mts_end=${end}&group_by=${type}&order=availability_asc`);
}

export function getApigwErrorRequest({ system, appCode, requestUrl, componentName, start, end }: ITimeChartParams) {
  return http.get(`${path}${system}/errors/?url=${requestUrl}&app_code=${appCode}&component_name=${componentName}&mts_start=${start}&mts_end=${end}&size=200`);
}
