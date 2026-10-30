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
import type { IResourceImportCheckResult } from '@/types/resource';
import type { ICountAndResults } from '@/services/types/utils.ts';
import type {
  IBackendPathCheckOutput,
  IResourceListPageOutput,
  IResourcePathConflictOutput,
  IResourceRetrieveOutput,
  IResourceWithVerifiedUserRequiredOutput,
} from '@/services/types/responses/gateways.ts';
import type {
  IGatewaysResourcesBackendPathCheckReadQuery,
  IGatewaysResourcesListQuery,
  IGatewaysResourcesWithVerifiedUserRequiredListQuery,
} from '@/services/types/query/gateways.ts';
import type {
  IResourceExportInputSLZ,
  IResourceImportCheckInputSLZ,
  IResourceImportDocPreviewInputSLZ,
  IResourceImportInputSLZ,
  IResourceInputSLZ,
} from '@/services/types/body/post/gateways.ts';
import type {
  IResourceBatchUpdateInputSLZ,
  IResourceLabelUpdateInputSLZ,
} from '@/services/types/body/patch/gateways.ts';

const path = '/gateways';

/**
 *  获取资源列表
 * @param gatewayId 网关id
 * @param params 查询参数
 */
export const getResourceList = (gatewayId: number, params: IGatewaysResourcesListQuery = {}) =>
  http.get<ICountAndResults<IResourceListPageOutput>>(`${path}/${gatewayId}/resources/`, params);

/**
 *  获取资源详情
 * @param gatewayId 网关id
 * @param resourceId 网关资源id
 */
export const getResourceDetail = (gatewayId: number, resourceId: number) =>
  http.get<IResourceRetrieveOutput>(`${path}/${gatewayId}/resources/${resourceId}/`);

/**
 *  创建资源
 * @param gatewayId 网关id
 * @param data 网关资源数据
 */
export const createResources = (gatewayId: number, data: IResourceInputSLZ) =>
  http.post(`${path}/${gatewayId}/resources/`, data);

/**
 *  更新资源
 * @param gatewayId 网关id
 * @param resourceId 网关资源id
 * @param data 网关资源数据
 */
export const updateResources = (gatewayId: number, resourceId: number, data: IResourceInputSLZ) =>
  http.put(`${path}/${gatewayId}/resources/${resourceId}/`, data);

/**
 *  删除资源
 * @param gatewayId 网关id
 * @param resourceId 网关资源id
 */
export const deleteResources = (gatewayId: number, resourceId: number) =>
  http.delete(`${path}/${gatewayId}/resources/${resourceId}/`);

/**
 *  批量删除资源
 * @param gatewayId 网关id
 * @param params.ids 资源id列表
 */
export const batchDeleteResources = (gatewayId: number, params: { ids: number[] }) =>
  http.delete(`${path}/${gatewayId}/resources/batch/`, params);

/**
 *  批量编辑资源
 * @param gatewayId 网关id
 * @param params 批量编辑参数
 */
export const batchEditResources = (gatewayId: number, params: IResourceBatchUpdateInputSLZ) =>
  http.put(`${path}/${gatewayId}/resources/batch/`, params);

/**
 * 导入资源
 * @param gatewayId 网关id
 * @param data 导入参数
 */
export const importResource = (gatewayId: number, data: IResourceImportInputSLZ) =>
  http.post(`${path}/${gatewayId}/resources/import/`, data);

/**
 * 导入前检查
 * @param gatewayId 网关id
 * @param data 检查参数
 * @param config 拦截器选项
 */
export const checkResourceImport = (
  gatewayId: number,
  data: IResourceImportCheckInputSLZ,
  config: Record<string, unknown> = {},
) =>
  http.post<IResourceImportCheckResult[]>(`${path}/${gatewayId}/resources/import/check/`, data, config);

/**
 * 获取导入资源的文档预览数据
 * @param gatewayId 网关id
 * @param data 资源参数
 */
export const getResourceDocPreview = (gatewayId: number, data: IResourceImportDocPreviewInputSLZ) =>
  http.post(`${path}/${gatewayId}/resources/import/doc/preview/`, data);

/**
 * 导出资源
 * @param gatewayId 网关id
 * @param data 导出参数
 */
export const exportResources = (gatewayId: number, data: IResourceExportInputSLZ) =>
  http.post(`${path}/${gatewayId}/resources/export/`, data, { responseType: 'blob' });

/**
 * 检测编辑区全部资源的请求路径冲突
 * @param gatewayId 网关id
 */
export const getResourcePathConflicts = (gatewayId: number) =>
  http.get<IResourcePathConflictOutput>(
    `${path}/${gatewayId}/resources/-/path-conflicts/`,
    undefined,
    { catchError: true },
  );

/**
 *  过滤出需要认证用户的资源列表，免用户认证应用白名单插件，需要使用此数据过滤资源
 * @param gatewayId 网关id
 * @param params 参数
 */
export const getVerifiedUserRequiredResources = (
  gatewayId: number,
  params: IGatewaysResourcesWithVerifiedUserRequiredListQuery = {},
) =>
  http.get<IResourceWithVerifiedUserRequiredOutput[]>(`${path}/${gatewayId}/resources/with/verified-user-required/`, params);

/**
 * 校验资源的后端请求地址
 * @param gatewayId 网关id
 * @param data 校验参数
 */
export const backendsPathCheck = (gatewayId: number, data: IGatewaysResourcesBackendPathCheckReadQuery) =>
  http.get<IBackendPathCheckOutput[]>(`${path}/${gatewayId}/resources/backend-path/check/`, data);

/**
 * 设置标签
 * @param gatewayId 网关id
 * @param resourceId 资源id
 * @param data 标签数据
 */
export const updateResourceLabels = (gatewayId: number, resourceId: number, data: IResourceLabelUpdateInputSLZ) =>
  http.put(`${path}/${gatewayId}/resources/${resourceId}/labels/`, data);
