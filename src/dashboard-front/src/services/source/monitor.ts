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

export interface IAlarmStrategy {
  id: number
  name: string
  alarm_type: string
  alarm_subtype: string
  updated_time?: string
  effective_stages: string[]
  gateway_labels?: number[]
  config?: {
    detect_config?: {
      count: number
      duration: number
      method: string
    }
    converge_config?: { duration: number }
    notice_config?: {
      notice_way: string[]
      notice_role: string[]
      notice_extra_receiver: string[]
    }
  }
  enabled?: boolean
}

export interface IStrategyListParams {
  offset: number
  limit: number
  keyword: string
}

export interface IRecordListParams {
  offset: number
  limit: number
  alarm_strategy_id: number
  status: string
  time_start?: number
  time_end?: number
}

export interface IAlarmRecord {
  id: number
  alarm_id: string
  status: string
  message: string
  created_time: string
  comment: string
  alarm_strategy_names: string[]
}

/**
 *  获取告警策略列表
 * @param apigwId 网关id
 * @param params 查询参数
 */
export function getStrategyList(apigwId: number, params: IStrategyListParams) {
  return http.get(`/gateways/${apigwId}/monitors/alarm/strategies/`, params);
}

/**
 *  获取单个告警策略详情
 * @param apigwId 网关id
 * @param id 告警策略id
 */
export function getStrategyDetail(apigwId: number, id: number) {
  return http.get(`/gateways/${apigwId}/monitors/alarm/strategies/${id}`);
}

/**
 *  创建告警策略
 * @param apigwId 网关id
 * @param params 创建参数
 */
export function createStrategy(apigwId: number, params: IAlarmStrategy) {
  return http.post(`/gateways/${apigwId}/monitors/alarm/strategies/`, params);
}

/**
 *  更新告警策略
 * @param apigwId 网关id
 * @param id 告警策略id
 * @param params 更新参数
 */
export function updateStrategy(apigwId: number, id: number, params: IAlarmStrategy) {
  return http.put(`/gateways/${apigwId}/monitors/alarm/strategies/${id}`, params);
}

/**
 *  删除单个告警策略
 * @param apigwId 网关id
 * @param id 告警策略id
 */
export function deleteStrategy(apigwId: number, id: number) {
  return http.delete(`/gateways/${apigwId}/monitors/alarm/strategies/${id}`);
}

/**
 *  更新告警策略状态
 * @param apigwId 网关id
 * @param id 告警策略id
 * @param params 更新状态参数
 */
export function updateStrategyStatus(apigwId: number, id: number, params: { enabled: boolean }) {
  return http.patch(`/gateways/${apigwId}/monitors/alarm/strategies/${id}/status/`, params);
}

/**
 *  获取告警记录列表
 * @param apigwId 网关id
 * @param params 查询参数
 */
export function getRecordList(apigwId: number, params: IRecordListParams) {
  return http.get(`/gateways/${apigwId}/monitors/alarm/records/`, params);
}

/**
 *  获取某条告警记录详情
 * @param apigwId 网关id
 * @param id 告警记录id
 */
export function getRecordDetail(apigwId: number, id: number) {
  return http.get(`/gateways/${apigwId}/monitors/alarm/records/${id}/`);
}
