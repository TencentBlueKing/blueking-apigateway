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

export interface IVersionItem {
  id: number | string
  released_stages: {
    id: number
    name: string
  }[]
  sdk_count: number
  version: string
  schema_version: string
  comment: string
  created_time: string
  created_by: string
}

export interface IDiffData {
  add: Record<string, any>[]
  delete: Record<string, any>[]
  update: {
    source: Record<string, any>
    target: Record<string, any>
  }[]
}

/**
 *  资源列表数据
 * @param apigwId 网关id
 * @param params
 * @returns
 */
export const getResourceList = (apigwId: number, params: any) => http.get(`${path}/${apigwId}/resources/`, params);

/**
 *  获取资源详情
 * @param apigwId 网关id
 * @param resourceId 网关资源id
 * @returns
 */
export const getResourceDetail = (apigwId: number, resourceId: number) =>
  http.get(`${path}/${apigwId}/resources/${resourceId}/`);

/**
 *  创建资源
 * @param apigwId 网关id
 * @param data 网关资源数据
 * @returns
 */
export const createResources = (apigwId: number, data: any) =>
  http.post(`${path}/${apigwId}/resources/`, data);

/**
 *  更新资源
 * @param apigwId 网关id
 * @param resourceId 网关资源id
 * @param data 网关资源数据
 * @returns
 */
export const updateResources = (apigwId: number, resourceId: number, data: any) =>
  http.put(`${path}/${apigwId}/resources/${resourceId}/`, data);

/**
 *  删除资源
 * @param apigwId 网关id
 * @param resourceId 网关资源id
 * @returns
 */
export const deleteResources = (apigwId: number, resourceId: number) =>
  http.delete(`${path}/${apigwId}/resources/${resourceId}/`);

/**
 *  批量删除资源
 * @param apigwId 网关id
 * @param params
 * @returns
 */
export const batchDeleteResources = (apigwId: number, params: { ids: number[] }) =>
  http.delete(`${path}/${apigwId}/resources/batch/`, params);

/**
 *  批量编辑资源
 * @param apigwId 网关id
 * @param params
 * @returns
 */
export const batchEditResources = (apigwId: number, params: {
  ids: number[]
  is_public: boolean
  allow_apply_permission: boolean
}) => http.put(`${path}/${apigwId}/resources/batch/`, params);

/**
 * 导入资源
 * @param apigwId 网关id
 * @param data 导入参数
 */
export const importResource = (apigwId: number, data: any) =>
  http.post(`${path}/${apigwId}/resources/import/`, data);

/**
 * 导入前检查
 * @param apigwId 网关id
 * @param data 检查参数
 * @param config 拦截器选项
 */
export const checkResourceImport = (apigwId: number, data: any, config: any = {}) =>
  http.post(`${path}/${apigwId}/resources/import/check/`, data, config);

/**
 * 导出资源
 * @param apigwId 网关id
 * @param data 导出参数
 */
export const exportResources = async (apigwId: number, data: any) => {
  const res = await http.post(`${path}/${apigwId}/resources/export/`, data, { responseType: 'blob' });
  return blobDownLoad(res);
};

/**
 * 导入资源文档
 * @param apigwId 网关id
 * @param data 导入参数
 */
export const importResourceDoc = (apigwId: number, data: any) =>
  http.post(`${path}/${apigwId}/docs/import/by-archive/`, data, { responseType: 'formdata' });

/**
 * 导入资源文档by swagger
 * @param apigwId 网关id
 * @param data 导入参数
 */
export const importResourceDocSwagger = (apigwId: number, data: any) =>
  http.post(`${path}/${apigwId}/docs/import/by-swagger/`, data);

/**
 * 生成资源版本
 * @param apigwId 网关id
 * @param data 资源版本信息
 */
export const createResourceVersion = (apigwId: number, data: any) =>
  http.post(`${path}/${apigwId}/resource-versions/`, data);

/**
 * 获取建议的版本
 * @param apigwId 网关id
 */
export const getNextVersion = (apigwId: number) => http.get(`${path}/${apigwId}/resource-versions/next-version/`);

export const getVersionList = (apigwId: number, params: {
  limit?: number
  offset?: number
}) =>
  http.get<{
    count: number
    results: IVersionItem[]
  }>(`${path}/${apigwId}/resource-versions/`, params);

// 资源版本详情
export const getVersionDetail = (apigwId: number, id: number, params?: any) =>
  http.get(`${path}/${apigwId}/resource-versions/${id}/`, params);

/**
 * 是否需要创建新资源版本
 * @param apigwId 网关id
 */
export const checkNeedNewVersion = (apigwId: number) =>
  http.get(`${path}/${apigwId}/resource-versions/need-new-version/`);

export const getVersionDiff = (apigwId: number, data: {
  source_resource_version_id: number
  target_resource_version_id: number
}) =>
  http.get<IDiffData>(`${path}/${apigwId}/resource-versions/diff/`, data);

export const exportVersion = async (apigwId: number, data: {
  id?: number
  export_type: string
  file_type: string
}) => {
  const { id } = data;
  delete data.id;
  const res = await http.post(`${path}/${apigwId}/resource-versions/${id}/export/`, data, { responseType: 'blob' });
  return blobDownLoad(res);
};

/**
 *  过滤出需要认证用户的资源列表，免用户认证应用白名单插件，需要使用此数据过滤资源
 * @param apigwId 网关id
 * @param params 参数
 */
export const getVerifiedUserRequiredResources = (apigwId: number, params?: {
  limit?: number
  offset?: number
}) =>
  http.get(`${path}/${apigwId}/resources/with/verified-user-required/`, params);

// 校验资源后端地址
export const backendsPathCheck = (apigwId: number, data: any) =>
  http.get(`${path}/${apigwId}/resources/backend-path/check/`, data);

/**
 * 设置标签
 * @param apigwId 网关id
 * @param resourceId 资源id
 * @param data 标签数据
 */
export const updateResourceLabels = (apigwId: number, resourceId: number, data: any) =>
  http.put(`${path}/${apigwId}/resources/${resourceId}/labels/`, data);

/**
 * 获取资源文档数据
 * @param apigwId 网关id
 * @param resourceId 资源id
 */
export const getResourceDocs = (apigwId: number, resourceId: number) =>
  http.get(`${path}/${apigwId}/resources/${resourceId}/docs/`);

/**
 * 获取资源文档预览数据
 * @param apigwId 网关id
 * @param data 资源参数
 */
export const getResourceDocPreview = (apigwId: number, data: any) =>
  http.post(`${path}/${apigwId}/resources/import/doc/preview/`, data);

/**
 * 保存资源文档数据
 * @param apigwId 网关id
 * @param resourceId 资源id
 * @param data 文档内容
 */
export const saveResourceDocs = (apigwId: number, resourceId: number, data: any) =>
  http.post(`${path}/${apigwId}/resources/${resourceId}/docs/`, data);

/**
 * 更新资源文档数据
 * @param apigwId 网关id
 * @param resourceId 资源id
 * @param data 文档内容
 * @param docId 文档id
 */
export const updateResourceDocs = (apigwId: number, resourceId: number, data: any, docId: number) =>
  http.put(`${path}/${apigwId}/resources/${resourceId}/docs/${docId}/`, data);

/**
 * 删除资源文档数据
 * @param apigwId 网关id
 * @param resourceId 资源id
 * @param docId 文档id
 */
export const deleteResourceDocs = (apigwId: number, resourceId: number, docId: number) =>
  http.delete(`${path}/${apigwId}/resources/${resourceId}/docs/${docId}/`);
