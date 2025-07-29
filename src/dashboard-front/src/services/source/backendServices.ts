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

interface IBackendServicesConfig {
  name: string
  description: string
  configs: {
    timeout: number
    loadbalance: string
    hosts: {
      scheme: string
      host: string
      weight: number
    }[]
    stage_id: number
  }[]
}

export function getBackendServiceList(apigwId: number, params?: {
  limit?: number
  offset?: number
  name?: string
  type?: string
}) {
  return http.get<{
    count: number
    results: any[]
  }>(`/gateways/${apigwId}/backends/`, params);
}

/**
 * 获取后端服务详情
 * @param apigwId 网关id
 * @param id 后端服务id
 */
export function getBackendServiceDetail(apigwId: number, id: number) {
  return http.get(`/gateways/${apigwId}/backends/${id}/`);
}

/**
 * 创建后端服务
 * @param apigwId 网关id
 * @param params 新建参数
 */
export function createBackendService(apigwId: number, params: IBackendServicesConfig) {
  return http.post(`/gateways/${apigwId}/backends/`, params);
}

/**
 * 更新后端服务
 * @param apigwId 网关id
 * @param params 更新参数
 * @param id 后端服务id
 */
export function updateBackendService(apigwId: number, id: number, params: IBackendServicesConfig) {
  return http.put(`/gateways/${apigwId}/backends/${id}/`, params);
}

/**
 * 删除后端服务
 * @param apigwId 网关id
 * @param id 后端服务id
 */
export function deleteBackendService(apigwId: number, id: number) {
  return http.delete(`/gateways/${apigwId}/backends/${id}/`);
}
