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
* 在线调试相关 API
*  */

import http from '@/services/http';
import type {
  IAPIDebugHistoriesListOutput,
  IAPIDebugHistoriesRetrieveOutput,
} from '@/services/types/responses/gateways.ts';
import type { IGatewaysTestsHistoriesListQuery } from '@/services/types/query/gateways.ts';

const path = '/gateways';

/**
 *  在线调试发起请求
 * @param gatewayId 网关id
 * @param data 请求数据
 */
export const createApiTest = (gatewayId: number, data: Record<string, unknown>) =>
  http.post(`${path}/${gatewayId}/tests/`, data);

/**
 *  在线调试历史记录列表
 * @param gatewayId 网关id
 * @param data 查询参数
 */
export const getApiTestHistoryList = (
  gatewayId: number,
  data: IGatewaysTestsHistoriesListQuery = {},
) =>
  http.get<IAPIDebugHistoriesListOutput[]>(`${path}/${gatewayId}/tests/histories/`, data);

/**
 *  获取调用历史详情
 * @param gatewayId 网关id
 * @param id 历史记录id
 */
export const getApiTestHistoryDetail = (gatewayId: number, id: number) =>
  http.get<IAPIDebugHistoriesRetrieveOutput>(`${path}/${gatewayId}/tests/histories/${id}/`);
