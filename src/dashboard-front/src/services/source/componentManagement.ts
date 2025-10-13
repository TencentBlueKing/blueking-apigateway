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

const path = '/esb/components/';

export interface IComponentItem {
  id: number
  timeout: number
  system_id: number
  system_name: string
  name: string
  description: string
  method: string
  path: string
  component_codename: string
  permission_level: string
  api_url: string
  doc_link: string
  updated_time: string
  is_active: boolean
  is_created: boolean
  is_official: boolean
  has_updated: boolean
  verified_user_required: boolean
}

export interface ISyncApigwItem {
  component_id: number
  component_method: string
  component_name: string
  component_path: string
  component_permission_level: string
  resource_id: number
  resource_name: string
  system_name: string
}

export interface ISyncHistoryItem {
  id: number
  created_time: string
  resource_version_name: string | null
  resource_version_title: string | null
  resource_version_display: string
  created_by: string
  status: string
  message: string
}

export interface IComponentListParams {
  limit: number
  offset: number
  path: string
  name: string
  system_name: string
}

export interface ISyncHistoryParams {
  limit: number
  offset: number
  time_start?: number
  time_end?: number
}

export function getEsbComponents(params: IComponentListParams) {
  return http.get(`${path}`, params);
}

export function addComponent(params: IComponentItem) {
  return http.post(`${path}`, params);
}

export function updateComponent(id: number, params: IComponentItem) {
  return http.put(`${path}${id}/`, params);
}

export function getComponentsDetail(id: number) {
  return http.get(`${path}${id}/`);
}

export function deleteComponentByBatch(params: { ids: string[] }) {
  return http.delete(`${path}batch/`, params);
}

export function getReleaseStatus() {
  return http.get(`${path}sync/release/status/`);
}

export function checkEsbNeedNewVersion() {
  return http.get(`${path}sync/need-new-release/`);
};

export function checkSyncComponent() {
  return http.post(`${path}sync/check/`);
}

export function getSyncReleaseData() {
  return http.post(`${path}sync/release/`);
}

/**
 *  获取 Esb 网关
 */
export function getEsbGateway() {
  return http.get(`${path}gateway/`);
}

/**
 * 获取组件同步历史列表
 * @param params
 * @returns
 */
export function getSyncHistory(params: ISyncHistoryParams) {
  return http.get(`${path}sync/release/histories/`, params);
}

/**
 * 组件同步网关及发布历史.
 * @param id
 * @returns
 */
export function getSyncVersion(id: number) {
  return http.get(`${path}sync/release/histories/${id}/`);
}

/**
 * 获取 feature flag 全局特性开关列表
 * @param data 分页参数
 * @returns
 */
export function getFeatures(params?: {
  limit: number
  offset: number
}) {
  return http.get('/settings/feature-flags/', params);
}
