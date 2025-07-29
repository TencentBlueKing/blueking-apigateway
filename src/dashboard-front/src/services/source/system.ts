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

const system = '/esb/systems/';

export interface ISystemConfig {
  name: string
  description: string
  comment: string
  doc_category_id: string
  timeout: number
  maintainers: string[]
}

export interface ISystemItem {
  comment: string
  component_count: number
  description: string
  description_en: string
  doc_category_id: number
  doc_category_name: string
  id: number
  is_official: boolean
  maintainers: string[]
  name: string
  timeout: number
}

/**
 *  获取系统管理列表
 */
export function getSystems() {
  return http.get(`${system}`);
}

/**
 *  获取系统管理详情
 */
export function getSystemDetail(systemId: number) {
  return http.get(`${system}${systemId}/`);
}

/**
 *  新增系统管理
 */
export function addSystem(params: ISystemConfig) {
  return http.post(`${system}`, params);
}

/**
 *  更新系统管理
 */
export function updateSystem(systemId: number, params: ISystemConfig) {
  return http.put(`${system}${systemId}/`, params);
}

/**
 *  删除系统管理
 */
export function deleteSystem(systemId: number) {
  return http.delete(`${system}${systemId}/`);
}
