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

/*
* 资源文档相关 API（单个资源的文档，以及网关级文档的导入、导出）
*  */

import http from '@/services/http';
import type { ICreatedIdOutput } from '@/services/types/gateway/common.ts';
import type {
  IDocArchiveParseInputSLZ,
  IDocArchiveParseOutput,
  IDocExportInputSLZ,
  IDocImportByArchiveInputSLZ,
  IDocImportBySwaggerInputSLZ,
  IDocInputSLZ,
  IDocListOutput,
  IGatewaysResourcesDocsListQuery,
} from '@/services/types/gateway/resource-doc.ts';

const path = '/gateways';

/**
 * 导出文档
 * @param gatewayId 网关id
 * @param data 导出参数
 */
export const exportDocs = (gatewayId: number, data: IDocExportInputSLZ) =>
  http.post<void>(`${path}/${gatewayId}/docs/export/`, data, { responseType: 'blob' });

/**
 * 解析资源文档压缩包
 * @param gatewayId 网关id
 * @param data 文档压缩包
 */
export const parseDocArchive = (gatewayId: number, { file }: IDocArchiveParseInputSLZ) => {
  const data = new FormData();
  data.append('file', file);
  return http.post<IDocArchiveParseOutput[]>(`${path}/${gatewayId}/docs/archive/parse/`, data);
};

/**
 * 通过压缩包导入资源文档
 * @param gatewayId 网关id
 * @param data 导入参数
 */
export const importDocsByArchive = (
  gatewayId: number,
  { file, selected_resource_docs }: IDocImportByArchiveInputSLZ,
) => {
  const data = new FormData();
  data.append('file', file);
  data.append('selected_resource_docs', JSON.stringify(selected_resource_docs));
  return http.post<void>(`${path}/${gatewayId}/docs/import/by-archive/`, data, { responseType: 'formdata' });
};

/**
 * 通过 swagger 导入资源文档
 * @param gatewayId 网关id
 * @param data 导入参数
 */
export const importDocsBySwagger = (gatewayId: number, data: IDocImportBySwaggerInputSLZ) =>
  http.post<void>(`${path}/${gatewayId}/docs/import/by-swagger/`, data);

/**
 * 获取资源文档数据
 * @param gatewayId 网关id
 * @param resourceId 资源id
 */
export const getResourceDocs = (gatewayId: number, resourceId: number, query: IGatewaysResourcesDocsListQuery = {}) =>
  http.get<IDocListOutput[]>(`${path}/${gatewayId}/resources/${resourceId}/docs/`, query);

/**
 * 新建资源文档
 * @param gatewayId 网关id
 * @param resourceId 资源id
 * @param data 文档内容
 */
export const createResourceDoc = (gatewayId: number, resourceId: number, data: IDocInputSLZ) =>
  http.post<ICreatedIdOutput>(`${path}/${gatewayId}/resources/${resourceId}/docs/`, data);

/**
 * 更新资源文档
 * @param gatewayId 网关id
 * @param resourceId 资源id
 * @param data 文档内容
 * @param docId 文档id
 */
export const updateResourceDoc = (gatewayId: number, resourceId: number, data: IDocInputSLZ, docId: number) =>
  http.put<void>(`${path}/${gatewayId}/resources/${resourceId}/docs/${docId}/`, data);

/**
 * 删除资源文档
 * @param gatewayId 网关id
 * @param resourceId 资源id
 * @param docId 文档id
 */
export const deleteResourceDoc = (gatewayId: number, resourceId: number, docId: number) =>
  http.delete<void>(`${path}/${gatewayId}/resources/${resourceId}/docs/${docId}/`);
