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

export interface IEventTemplate {
  description: string
  name: string
  step: number
}

export interface IEvent {
  id: number
  release_history_id: number
  name: string
  step: number
  status: 'doing' | 'success' | 'failure'
  created_time: string
  detail?: Record<string, any> | null
}

export interface ILogResponse {
  events: IEvent[]
  events_template: IEventTemplate[]
  status: string
}

export const createRelease = (apigwId: number, params: any) =>
  http.post(`${path}/${apigwId}/releases/`, params);

export const getReleaseEvents = (apigwId: number, historyId: number) =>
  http.get<ILogResponse>(`${path}/${apigwId}/releases/histories/${historyId}/events/`);

export const getReleaseHistories = (apigwId: number, params: any) => http.get(`${path}/${apigwId}/releases/histories/`, params);
