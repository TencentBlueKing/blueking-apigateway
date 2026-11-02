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
import type {
  IDisplayNameCheckResult,
  IGatewayCheckNameAvailableOutput,
  IGatewayCheckRepoAuthOutput,
  IGatewayDevGuidelineOutput,
  IGatewayListOutput,
  IGatewayReleasingStatusOutput,
  IGatewayRetrieveOutput,
} from '@/services/types/responses/gateways.ts';
import type { ICountAndResults } from '@/services/types/utils.ts';
import type {
  IGatewaysCheckNameAvailableReadQuery,
  IGatewaysListQuery,
} from '@/services/types/query/gateways.ts';
import type { IGatewayCreateInputSLZ } from '@/services/types/body/post/gateways.ts';
import type {
  IGatewayUpdateInputSLZ,
  IGatewayUpdateStatusInputSLZ,
} from '@/services/types/body/patch/gateways.ts';

const path = '/gateways';

/**
 * 获取网关列表
 * @param params 查询参数
 */
export const getGatewayList = (params: IGatewaysListQuery = {}) =>
  http.get<ICountAndResults<IGatewayListOutput>>(`${path}/`, params);

/**
 * 获取网关详情
 * @param gatewayId 网关id
 */
export const getGatewayDetail = (gatewayId: number) =>
  http.get<IGatewayRetrieveOutput>(`${path}/${gatewayId}/`);

/**
 * 新建网关
 * @param param 新建参数
 */
export const createGateway = (param: IGatewayCreateInputSLZ) =>
  http.post(`${path}/`, param);

/**
 * 删除网关
 * @param gatewayId 网关id
 */
export const deleteGateway = (gatewayId: number) => http.delete(`${path}/${gatewayId}/`);

/**
 * 部分更新网关信息
 * @param gatewayId 网关id
 * @param data 需要更新的字段
 */
export const patchGateway = (gatewayId: number, data: IGatewayUpdateInputSLZ) =>
  http.patch(`${path}/${gatewayId}/`, data);

/**
 * 更新网关基本信息
 * @param gatewayId 网关id
 * @param data 网关基本信息
 */
export const updateGateway = (gatewayId: number, data: IGatewayUpdateInputSLZ) =>
  http.put(`${path}/${gatewayId}/`, data);

/**
 * 检查网关名称是否可用
 * @param param 查询参数
 */
export const checkNameAvailable = (param: IGatewaysCheckNameAvailableReadQuery) =>
  http.get<IGatewayCheckNameAvailableOutput>(`${path}/check-name-available/`, param);

/**
 * 新建网关时检查展示名是否可用
 * @param displayName 网关展示名
 */
export const checkDisplayNameAvailable = (displayName: string) =>
  http.post<IDisplayNameCheckResult>(`${path}/check-display-name-available/`, { display_name: displayName });

/**
 * 编辑网关时检查展示名是否可用，网关 ID 仅放在 URL 中，用于排除自身
 * @param gatewayId 网关id
 * @param displayName 网关展示名
 */
export const checkDisplayNameAvailableForUpdate = (gatewayId: number, displayName: string) =>
  http.post<IDisplayNameCheckResult>(`${path}/${gatewayId}/check-display-name-available/`, { display_name: displayName });

/**
 * 检查当前用户是否已授权代码仓库（可编程网关）
 */
export const checkRepoAuthorization = () =>
  http.get<IGatewayCheckRepoAuthOutput>(`${path}/repo-authorization/`);

/**
 * 获取操作指引
 * @param gatewayId 网关id
 */
export const getGuideDocs = (gatewayId: number) =>
  http.get<IGatewayDevGuidelineOutput>(`${path}/${gatewayId}/dev-guideline/`);

/**
 * 更新网关状态（启用 / 停用）
 * @param gatewayId 网关id
 * @param data 状态参数
 */
export const updateGatewayStatus = (gatewayId: number, data: IGatewayUpdateStatusInputSLZ) =>
  http.put(`${path}/${gatewayId}/status/`, data);

/**
 * 获取网关的发布中状态
 * @param gatewayId 网关id
 */
export const getReleasingStatus = (gatewayId: number) =>
  http.get<IGatewayReleasingStatusOutput>(`${path}/${gatewayId}/releasing-status/`);
