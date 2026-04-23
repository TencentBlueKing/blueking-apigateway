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
import type {
  IGatewayCheckNameAvailableOutput,
  IGatewayDevGuidelineOutput,
  IGatewayLabelOutput,
  IGatewayListOutput,
  IGatewayReleasingStatusOutput,
  IGatewayRetrieveOutput,
} from '@/services/types/responses/gateways.ts';
import type { ICountAndResults } from '@/services/types/utils.ts';
import type {
  IGatewaysCheckNameAvailableReadQuery,
  IGatewaysLabelsListQuery,
  IGatewaysListQuery,
} from '@/services/types/query/gateways.ts';
import type {
  IDocExportInputSLZ,
  IGatewayCreateInputSLZ,
} from '@/services/types/body/post/gateways.ts';
import type {
  IGatewayUpdateInputSLZ,
  IGatewayUpdateStatusInputSLZ,
} from '@/services/types/body/patch/gateways.ts';

const path = '/gateways';

export function getGatewayList(params: IGatewaysListQuery = {}) {
  return http.get<ICountAndResults<IGatewayListOutput>>(`${path}/`, params);
}

export function getGatewayDetail(id: number) {
  return http.get<IGatewayRetrieveOutput>(`${path}/${id}/`);
}

// 新建网关
export const createGateway = (param: IGatewayCreateInputSLZ) =>
  http.post(`${path}/`, param);

export const deleteGateway = (id: number) => http.delete(`${path}/${id}/`);

export const patchGateway = (id: number, data: IGatewayUpdateInputSLZ) =>
  http.patch(`${path}/${id}/`, data);

export const putGatewayBasics = (id: number, data: IGatewayUpdateInputSLZ) =>
  http.put(`${path}/${id}/`, data);

export const checkNameAvailable = (param: IGatewaysCheckNameAvailableReadQuery) =>
  http.get<IGatewayCheckNameAvailableOutput>(`${path}/check-name-available/`, param);

// 获取操作指引
export const getGuideDocs = (id: number) => http.get<IGatewayDevGuidelineOutput>(`${path}/${id}/dev-guideline/`);

export const toggleStatus = (id: number, data: IGatewayUpdateStatusInputSLZ) => http.put(`${path}/${id}/status/`, data);

export const getGatewayLabels = (apigwId: number, query: IGatewaysLabelsListQuery = {}) =>
  http.get<IGatewayLabelOutput[]>(`${path}/${apigwId}/labels/`, query);

export const getReleasingStatus = (apigwId: number) => http.get<IGatewayReleasingStatusOutput>(`${path}/${apigwId}/releasing-status/`);

/**
 * 导出文档
 * @param apigwId 网关id
 * @param data 导出参数
 */
export const exportDocs = async (apigwId: number, data: IDocExportInputSLZ) => http.post(`${path}/${apigwId}/docs/export/`, data, { responseType: 'blob' });
