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
* 可编程网关相关 API
*  */

import http from '@/services/http';
import type { ICountAndResults } from '@/services/types/utils.ts';
import type {
  IDeployHistoryListOutput,
  IGetDeployEventsByDeployIdOutput,
  IGetDeployEventsByHistoryIdOutput,
  IProgrammableStageDeployOutput,
} from '@/services/types/responses/gateways.ts';
import type {
  IGatewaysReleasesProgrammableDeployHistoriesListQuery,
  IGatewaysResourceVersionsProgrammableNextDeployVersionReadQuery,
} from '@/services/types/query/gateways.ts';
import type { IProgrammableDeployCreateInputSLZ } from '@/services/types/body/post/gateways.ts';

const path = '/gateways';

// 发布
export const deployReleases = (gatewayId: number, data: IProgrammableDeployCreateInputSLZ) =>
  http.post(`${path}/${gatewayId}/releases/programmable/deploy/`, data, { catchError: true });

// 获取环境详情
export const getProgrammableStageDetail = (gatewayId: number, stageId: number) => http.get<IProgrammableStageDeployOutput>(`${path}/${gatewayId}/stages/${stageId}/programmable/`);

// 获取下一个发布版本号
export const getStageNextVersion = (
  gatewayId: number,
  params: IGatewaysResourceVersionsProgrammableNextDeployVersionReadQuery,
) =>
  http.get<{ version: string }>(`${path}/${gatewayId}/resource-versions/programmable/next-deploy-version/`, params);

// 查询部署中的发布事件
export const getDeployEvents = (gatewayId: number, deploy_id: string) =>
  http.get<IGetDeployEventsByDeployIdOutput>(`${path}/${gatewayId}/releases/programmable/deploy/${deploy_id}/histories/events/`);

// 查询已完成部署后的发布事件
export const getFinishedDeployEvents = (gatewayId: number, history_id: number) =>
  http.get<IGetDeployEventsByHistoryIdOutput>(`${path}/${gatewayId}/releases/programmable/deploy/histories/${history_id}/events/`);

// 查询部署历史
export const getDeployHistories = (
  gatewayId: number,
  params: IGatewaysReleasesProgrammableDeployHistoriesListQuery = {},
) =>
  http.get<ICountAndResults<IDeployHistoryListOutput>>(`${path}/${gatewayId}/releases/programmable/deploy/histories/`, params);
