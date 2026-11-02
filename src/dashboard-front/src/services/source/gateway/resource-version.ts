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
import type { ICountAndResults } from '@/services/types/utils.ts';
import type {
  IResourceVersionDiffOutput,
  IResourceVersionListOutput,
  IResourceVersionRetrieveOutput,
} from '@/services/types/responses/gateways.ts';
import type {
  IGatewaysResourceVersionsDiffReadQuery,
  IGatewaysResourceVersionsListQuery,
  IGatewaysResourceVersionsReadQuery,
} from '@/services/types/query/gateways.ts';
import type {
  IResourceVersionCreateInputSLZ,
  IResourceVersionExportInputSLZ,
} from '@/services/types/body/post/gateways.ts';

const path = '/gateways';

/**
 * 生成资源版本
 * @param gatewayId 网关id
 * @param data 资源版本信息
 */
export const createResourceVersion = (gatewayId: number, data: IResourceVersionCreateInputSLZ) =>
  http.post(`${path}/${gatewayId}/resource-versions/`, data);

/**
 * 获取建议的版本
 * @param gatewayId 网关id
 */
export const getNextVersion = (gatewayId: number) =>
  http.get<{ version: string }>(`${path}/${gatewayId}/resource-versions/next-version/`);

/**
 * 获取资源版本列表
 * @param gatewayId 网关id
 * @param params 查询参数
 */
export const getVersionList = (gatewayId: number, params: IGatewaysResourceVersionsListQuery = {}) =>
  http.get<ICountAndResults<IResourceVersionListOutput>>(`${path}/${gatewayId}/resource-versions/`, params);

/**
 * 获取资源版本详情
 * @param gatewayId 网关id
 * @param id 资源版本id
 * @param params 查询参数
 */
export const getVersionDetail = (gatewayId: number, id: number, params: IGatewaysResourceVersionsReadQuery = {}) =>
  http.get<IResourceVersionRetrieveOutput>(`${path}/${gatewayId}/resource-versions/${id}/`, params);

/**
 * 是否需要创建新资源版本
 * @param gatewayId 网关id
 */
export const checkNeedNewVersion = (gatewayId: number) =>
  http.get<{
    msg: string | null
    need_new_version: boolean
  }>(`${path}/${gatewayId}/resource-versions/need-new-version/`, undefined, { catchError: true });

/**
 * 对比两个资源版本（或资源版本与编辑区）的差异
 * @param gatewayId 网关id
 * @param data 对比参数
 */
export const getVersionDiff = (gatewayId: number, data: IGatewaysResourceVersionsDiffReadQuery) =>
  http.get<IResourceVersionDiffOutput>(`${path}/${gatewayId}/resource-versions/diff/`, data);

/**
 * 导出资源版本（文件下载由 http 响应拦截器统一处理）
 * @param gatewayId 网关id
 * @param data 导出参数，id 为资源版本id
 */
export const exportVersion = (gatewayId: number, data: IResourceVersionExportInputSLZ) => {
  const { id, ...payload } = data;
  return http.post(`${path}/${gatewayId}/resource-versions/${id}/export/`, payload, {
    responseType: 'blob',
    catchError: true,
  });
};

/**
 * 导出资源版本对应的文档（文件下载由 http 响应拦截器统一处理）
 * @param gatewayId 网关id
 * @param data 导出参数，id 为资源版本id
 */
export const exportVersionDocs = (
  gatewayId: number,
  data: {
    id?: number
    file_type: string
  },
) => {
  const { id, ...payload } = data;
  return http.post(`${path}/${gatewayId}/resource-versions/${id}/export-docs/`, payload, {
    responseType: 'blob',
    catchError: true,
  });
};

/**
 * 删除资源版本
 * @param gatewayId 网关id
 * @param id 资源版本id
 */
export const deleteResourceVersion = (gatewayId: number, id: number) =>
  http.delete(`${path}/${gatewayId}/resource-versions/${id}/`);

/**
 * 批量删除资源版本
 * @param gatewayId 网关id
 * @param params 资源版本id列表
 */
export const batchDeleteResourceVersions = (gatewayId: number, params: { ids: number[] }) =>
  http.delete(`${path}/${gatewayId}/resource-versions/batch/`, params);
