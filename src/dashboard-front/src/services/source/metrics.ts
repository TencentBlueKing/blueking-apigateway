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

interface IMetricInstantParams {
  stage_id?: number // 阶段ID，可选
  resource_id?: string // 资源ID，可选
  metrics?: string // 指标，可选
  time_start?: number // 开始时间，可选
  time_end?: number // 结束时间，可选
  time_range?: string // 时间范围，可选
  limit?: number // 限制数量，可选
  offset?: number // 偏移量，可选
}

export const getGatewayMetrics = (apigwId: number, params: any) => http.get(`${path}/${apigwId}/metrics/query-range/`, params);

export const getGatewayMetricsInstant = (apigwId: number, params: IMetricInstantParams) =>
  http.get(`${path}/${apigwId}/metrics/query-instant/`, params);
