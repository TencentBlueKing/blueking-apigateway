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

export interface IStageListItem {
  id: number
  name: string
  description: string | null
  description_en: string | null
  status: number
  created_time: string | null
  release: {
    status: string
    created_time: string
    created_by: string
  }
  resource_version: {
    version: string
    id: number
    schema_version: string
  }
  publish_id: number
  publish_version: string
  publish_validate_msg: string
  new_resource_version: string
}

export const getStageList = (apigwId: number, query: IGatewaysStagesListQuery = {}) =>
  http.get<IStageListOutput[]>(`${path}/${apigwId}/stages/`, query);

export const getStageDetail = (apigwId: number, stageId: number) =>
  http.get<IStageRetrieveOutput>(`${path}/${apigwId}/stages/${stageId}/`);

export const createStage = (apigwId: number, data: IStageInputSLZ) =>
  http.post(`${path}/${apigwId}/stages/`, data);

export const deleteStage = (apigwId: number, stageId: number) =>
  http.delete(`${path}/${apigwId}/stages/${stageId}/`);

export const putStage = (apigwId: number, stageId: number, data: IStageInputSLZ) =>
  http.put(`${path}/${apigwId}/stages/${stageId}/`, data);

export const toggleStatus = (apigwId: number, stageId: number, params: IStageStatusInputSLZ) =>
  http.put(`${path}/${apigwId}/stages/${stageId}/status/`, params);

export const getStageBackends = (
  apigwId: number,
  stageId: number,
  query: IGatewaysStagesBackendsListQuery = {},
) =>
  http.get<IStageBackendListOutput[]>(`${path}/${apigwId}/stages/${stageId}/backends/`, query);

export const getStageVars = (apigwId: number, stageId: number) => http.get<IStageVarsOutput>(`${path}/${apigwId}/stages/${stageId}/vars/`);

export const putStageVars = (apigwId: number, stageId: number, data: IStageVarsSLZ) => http.put(`${path}/${apigwId}/stages/${stageId}/vars/`, data);
