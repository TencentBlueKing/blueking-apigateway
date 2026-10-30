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
  IStageBackendListOutput,
  IStageListOutput,
  IStageRetrieveOutput,
  IStageVarsOutput,
} from '@/services/types/responses/gateways.ts';
import type {
  IGatewaysStagesBackendsListQuery,
  IGatewaysStagesListQuery,
} from '@/services/types/query/gateways.ts';
import type { IStageInputSLZ } from '@/services/types/body/post/gateways.ts';
import type {
  IStageStatusInputSLZ,
  IStageVarsSLZ,
} from '@/services/types/body/patch/gateways.ts';

const path = '/gateways';

/**
 * 获取环境列表
 * @param gatewayId 网关id
 * @param query 查询参数
 */
export const getStageList = (gatewayId: number, query: IGatewaysStagesListQuery = {}) =>
  http.get<IStageListOutput[]>(`${path}/${gatewayId}/stages/`, query);

/**
 * 获取环境详情
 * @param gatewayId 网关id
 * @param stageId 环境id
 */
export const getStageDetail = (gatewayId: number, stageId: number) =>
  http.get<IStageRetrieveOutput>(`${path}/${gatewayId}/stages/${stageId}/`);

/**
 * 新建环境
 * @param gatewayId 网关id
 * @param data 环境配置
 */
export const createStage = (gatewayId: number, data: IStageInputSLZ) =>
  http.post(`${path}/${gatewayId}/stages/`, data);

/**
 * 删除环境
 * @param gatewayId 网关id
 * @param stageId 环境id
 */
export const deleteStage = (gatewayId: number, stageId: number) =>
  http.delete(`${path}/${gatewayId}/stages/${stageId}/`);

/**
 * 更新环境
 * @param gatewayId 网关id
 * @param stageId 环境id
 * @param data 环境配置
 */
export const updateStage = (gatewayId: number, stageId: number, data: IStageInputSLZ) =>
  http.put(`${path}/${gatewayId}/stages/${stageId}/`, data);

/**
 * 更新环境状态（启用 / 停用）
 * @param gatewayId 网关id
 * @param stageId 环境id
 * @param params 状态参数
 */
export const updateStageStatus = (gatewayId: number, stageId: number, params: IStageStatusInputSLZ) =>
  http.put(`${path}/${gatewayId}/stages/${stageId}/status/`, params);

/**
 * 获取环境绑定的后端服务配置
 * @param gatewayId 网关id
 * @param stageId 环境id
 * @param query 查询参数
 */
export const getStageBackends = (
  gatewayId: number,
  stageId: number,
  query: IGatewaysStagesBackendsListQuery = {},
) =>
  http.get<IStageBackendListOutput[]>(`${path}/${gatewayId}/stages/${stageId}/backends/`, query);

/**
 * 获取环境变量
 * @param gatewayId 网关id
 * @param stageId 环境id
 */
export const getStageVars = (gatewayId: number, stageId: number) =>
  http.get<IStageVarsOutput>(`${path}/${gatewayId}/stages/${stageId}/vars/`);

/**
 * 更新环境变量
 * @param gatewayId 网关id
 * @param stageId 环境id
 * @param data 环境变量
 */
export const updateStageVars = (gatewayId: number, stageId: number, data: IStageVarsSLZ) =>
  http.put(`${path}/${gatewayId}/stages/${stageId}/vars/`, data);
