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
  IBackendListOutput,
  IBackendRetrieveOutput,
  IBackendTestConnectionOutput,
  IBackendUpdateOutput,
} from '@/services/types/responses/gateways.ts';
import type { IGatewaysBackendsListQuery } from '@/services/types/query/gateways.ts';
import type {
  IBackendInputSLZ,
  IBackendTestConnectionInputSLZ,
} from '@/services/types/body/post/gateways.ts';

const path = '/gateways';

/**
 * 获取后端服务列表
 * @param gatewayId 网关id
 * @param params 查询参数
 */
export const getBackendServiceList = (gatewayId: number, params: IGatewaysBackendsListQuery = {}) =>
  http.get<ICountAndResults<IBackendListOutput>>(`${path}/${gatewayId}/backends/`, params);

/**
 * 获取后端服务详情
 * @param gatewayId 网关id
 * @param id 后端服务id
 */
export const getBackendServiceDetail = (gatewayId: number, id: number) =>
  http.get<IBackendRetrieveOutput>(`${path}/${gatewayId}/backends/${id}/`);

/**
 * 创建后端服务
 * @param gatewayId 网关id
 * @param params 新建参数
 */
export const createBackendService = (gatewayId: number, params: IBackendInputSLZ) =>
  http.post(`${path}/${gatewayId}/backends/`, params);

/**
 * 更新后端服务
 * @param gatewayId 网关id
 * @param id 后端服务id
 * @param params 更新参数
 */
export const updateBackendService = (gatewayId: number, id: number, params: IBackendInputSLZ) =>
  http.put<IBackendUpdateOutput>(`${path}/${gatewayId}/backends/${id}/`, params);

/**
 * 测试 AI 后端服务连通性
 * @param gatewayId 网关id
 * @param params 连通测试参数
 */
export const testBackendServiceConnection = (gatewayId: number, params: IBackendTestConnectionInputSLZ) =>
  http.post<IBackendTestConnectionOutput>(
    `${path}/${gatewayId}/backends/test-connection/`,
    params,
    // 失败原因由表单内的提示条展示
    { catchError: true },
  );

/**
 * 删除后端服务
 * @param gatewayId 网关id
 * @param id 后端服务id
 */
export const deleteBackendService = (gatewayId: number, id: number) =>
  http.delete(`${path}/${gatewayId}/backends/${id}/`);
