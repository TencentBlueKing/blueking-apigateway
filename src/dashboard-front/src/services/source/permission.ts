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

export interface IBatchUpdateParams {
  resource_dimension_ids: number[]
  gateway_dimension_ids: number[]
  expire_days: 0 | 180 | 360
}

// 导出参数interface
export interface IExportParams {
  [key: string | number]: unknown
  export_type: string
  bk_app_code?: string
  keyword?: string
  grant_type?: string
  dimension?: string
  resource_name?: string
  resource_ids?: number
  resource_permission_ids?: number[]
  gateway_permission_ids?: number[]
}

// 搜索参数
export interface IFilterParams {
  [key: string | number]: unknown
  bk_app_code?: string
  keyword?: string
  resource_id?: number
  grant_dimension?: string
}

export interface IAuthData {
  bk_app_code: string
  expire_type: string
  expire_days: number | null
  resource_ids: number[]
  dimension: string
}

export interface IResourceData {
  backend: {
    id: number
    name: string
  }
  id: number
  plugin_count: number
  name: string
  path: string
  method: string
  description: string
  created_time: string
  updated_time: string
  docs: string[]
  labels: string[]
  has_updated: boolean
}

/**
 *  获取流程日志列表
 * @param apigwId 网关id
 * @param params
 */
export function getApigwResources(apigwId: number, params: {
  no_page?: boolean
  order_by?: string
  offset: number
  limit: number
}) {
  return http.get(`/gateways/${apigwId}/resources/`, params);
}

/**
 *  获取权限申请单列表
 * @param apigwId 网关id
 * @param params
 */
export function getPermissionApplyList(apigwId: number, params: {
  limit: number
  offset: number
  bk_app_code?: string
  applied_by?: string
  grant_dimension?: string
} = {
  offset: 0,
  limit: 10,
}) {
  return http.get(`/gateways/${apigwId}/permissions/app-permission-apply/`, params);
}

/**
 *  审批操作
 * @param apigwId 网关id
 * @param data 审批参数
 */
export function updatePermissionStatus(
  apigwId: number,
  params: {
    ids: []
    status: string
    comment: string
    part_resource_ids: Record<string, unknown>
  }) {
  return http.post(`/gateways/${apigwId}/permissions/app-permission-apply/approval/`, params);
}

/**
 *  获取权限申请单详情
 * @param apigwId 网关id
 * @param id
 */
export function getPermissionApplyDetail(apigwId: number, id: number) {
  return http.get(`/gateways/${apigwId}/permissions/app-permission-apply/${id}/`);
}

/**
 *  获取权限申请记录列表--records
 * @param apigwId 网关id
 * @param params 查询参数
 */
export function getPermissionRecordList(
  apigwId: number,
  params: {
    offset: number
    limit: number
  } = {
    offset: 0,
    limit: 10,
  },
) {
  return http.get(`/gateways/${apigwId}/permissions/app-permission-records/`, params);
}

/**
 *  网关权限主动授权
 * @param apigwId 网关id
 * @param params 授权参数
 */
export function authApiPermission(apigwId: number, params: IAuthData) {
  return http.post(`/gateways/${apigwId}/permissions/app-gateway-permissions/`, params);
}

/**
 *  网关权限删除
 * @param apigwId 网关id
 * @param params 删除参数
 */
export function deleteApiPermission(apigwId: number, params: { ids: number[] }) {
  return http.delete(`/gateways/${apigwId}/permissions/app-gateway-permissions/delete/?ids=${params.ids}`);
}

/**
 *  获取权限列表
 * @param apigwId 网关id
 * @param params 查询参数
 */
export function getPermissionList(apigwId: number, params: IFilterParams) {
  return http.get(`/gateways/${apigwId}/permissions/app-permissions/`, params);
}

/**
 *  资源权限主动授权
 * @param apigwId 网关id
 * @param params 授权参数
 */
export function authResourcePermission(apigwId: number, params: IAuthData) {
  return http.post(`/gateways/${apigwId}/permissions/app-resource-permissions/`, params);
}

/**
 *  获取有资源权限的应用列表
 * @param apigwId 网关id
 */
export function getResourcePermissionAppList(apigwId: number) {
  return http.get(`/gateways/${apigwId}/permissions/app-permissions/bk-app-codes/`);
}

/**
 *  删除资源权限
 * @param apigwId 网关id
 * @param params 删除参数
 */
export function deleteResourcePermission(apigwId: number, params: { ids: number[] }) {
  return http.delete(`/gateways/${apigwId}/permissions/app-resource-permissions/delete/?ids=${params.ids}`);
}

/**
 *  资源列表数据
 * @param apigwId 网关id
 * @returns
 */
export function getResourceListData(apigwId: number, params: {
  limit: number
  order_by: string
}) {
  return http.get<{
    count: number
    results: IResourceData[]
  }>(`/gateways/${apigwId}/resources/`, params);
}

/**
 *  资源权限导出
 * @param apigwId 网关id
 * @param params 导出参数
 */
export async function exportPermissionList(apigwId: number, params: IExportParams) {
  return http.post(`/gateways/${apigwId}/permissions/app-permissions/export/`, params);
};

/**
 *  批量权限续期
 * @param apigwId 网关id
 * @param params 导出参数
 */
export function batchUpdatePermission(apigwId: number, params: IBatchUpdateParams) {
  return http.post(`/gateways/${apigwId}/permissions/app-permissions/renew/`, params);
}
