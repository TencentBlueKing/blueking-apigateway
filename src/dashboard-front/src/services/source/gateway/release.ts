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
  IReleaseHistoryEventRetrieveOutput,
  IReleaseHistoryListOutput,
  IReleaseResourceSchemaOutput,
  IResourceListOutput,
} from '@/services/types/responses/gateways.ts';
import type {
  IGatewaysReleasesHistoriesListQuery,
  IGatewaysReleasesStagesResourcesListQuery,
} from '@/services/types/query/gateways.ts';
import type { IReleaseInputSLZ } from '@/services/types/body/post/gateways.ts';

const path = '/gateways';

/**
 * 发布资源版本到环境
 * @param gatewayId 网关id
 * @param params 发布参数
 */
export const createRelease = (gatewayId: number, params: IReleaseInputSLZ) =>
  http.post(`${path}/${gatewayId}/releases/`, params, { catchError: true });

/**
 * 获取某次发布的事件详情
 * @param gatewayId 网关id
 * @param historyId 发布历史id
 */
export const getReleaseEvents = (gatewayId: number, historyId: number) =>
  http.get<IReleaseHistoryEventRetrieveOutput>(`${path}/${gatewayId}/releases/histories/${historyId}/events/`);

/**
 * 获取发布历史
 * @param gatewayId 网关id
 * @param params 查询参数
 */
export const getReleaseHistories = (gatewayId: number, params: IGatewaysReleasesHistoriesListQuery = {}) =>
  http.get<ICountAndResults<IReleaseHistoryListOutput>>(`${path}/${gatewayId}/releases/histories/`, params);

/**
 *  获取环境下已发布的资源列表
 * @param gatewayId 网关id
 * @param stageId 环境id
 * @param data 查询参数
 */
export const getReleasedStageResources = (
  gatewayId: number,
  stageId: number,
  data: IGatewaysReleasesStagesResourcesListQuery = {},
) =>
  http.get<IResourceListOutput[]>(`${path}/${gatewayId}/releases/stages/${stageId}/resources/`, data);

/**
 * 获取环境下已发布的某个资源的接口 schema
 * @param gatewayId 网关id
 * @param stageId 环境id
 * @param resourceId 资源id
 */
export const getReleasedResourceSchema = (gatewayId: number, stageId: number, resourceId: number) =>
  http.get<IReleaseResourceSchemaOutput>(`${path}/${gatewayId}/releases/stages/${stageId}/resources/${resourceId}/schema/`);
