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
import http from '@/services/http';
import type {
  IAlarmRecordListOutput,
  IAlarmStrategyListOutput,
  IAlarmStrategyRetrieveOutput,
} from '@/services/types/responses/gateways.ts';
import type { ICountAndResults } from '@/services/types/utils.ts';
import type {
  IGatewaysMonitorsAlarmRecordsListQuery,
  IGatewaysMonitorsAlarmStrategiesListQuery,
} from '@/services/types/query/gateways.ts';
import type { IAlarmStrategyInputSLZ } from '@/services/types/body/post/gateways.ts';
import type { IAlarmStrategyUpdateStatusInputSLZ } from '@/services/types/body/patch/gateways.ts';

const path = '/gateways';

/**
 *  获取告警策略列表
 * @param gatewayId 网关id
 * @param params 查询参数
 */
export const getStrategyList = (gatewayId: number, params: IGatewaysMonitorsAlarmStrategiesListQuery = {}) =>
  http.get<ICountAndResults<IAlarmStrategyListOutput>>(`${path}/${gatewayId}/monitors/alarm/strategies/`, params);

/**
 *  获取单个告警策略详情
 * @param gatewayId 网关id
 * @param id 告警策略id
 */
export const getStrategyDetail = (gatewayId: number, id: number) =>
  http.get<IAlarmStrategyRetrieveOutput>(`${path}/${gatewayId}/monitors/alarm/strategies/${id}/`);

/**
 *  创建告警策略
 * @param gatewayId 网关id
 * @param params 创建参数
 */
export const createStrategy = (gatewayId: number, params: IAlarmStrategyInputSLZ) =>
  http.post(`${path}/${gatewayId}/monitors/alarm/strategies/`, params);

/**
 *  更新告警策略
 * @param gatewayId 网关id
 * @param id 告警策略id
 * @param params 更新参数
 */
export const updateStrategy = (gatewayId: number, id: number, params: IAlarmStrategyInputSLZ) =>
  http.put(`${path}/${gatewayId}/monitors/alarm/strategies/${id}/`, params);

/**
 *  删除单个告警策略
 * @param gatewayId 网关id
 * @param id 告警策略id
 */
export const deleteStrategy = (gatewayId: number, id: number) =>
  http.delete(`${path}/${gatewayId}/monitors/alarm/strategies/${id}/`);

/**
 *  更新告警策略状态（启用 / 停用）
 * @param gatewayId 网关id
 * @param id 告警策略id
 * @param params 更新状态参数
 */
export const patchStrategyStatus = (gatewayId: number, id: number, params: IAlarmStrategyUpdateStatusInputSLZ) =>
  http.patch(`${path}/${gatewayId}/monitors/alarm/strategies/${id}/status/`, params);

/**
 *  获取告警记录列表
 * @param gatewayId 网关id
 * @param params 查询参数
 */
export const getRecordList = (gatewayId: number, params: IGatewaysMonitorsAlarmRecordsListQuery = {}) =>
  http.get<IAlarmRecordListOutput>(`${path}/${gatewayId}/monitors/alarm/records/`, params);
