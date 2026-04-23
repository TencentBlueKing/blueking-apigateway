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
import type { ICountAndResults } from '@/services/types/utils.ts';
import type {
  IReleaseHistoryEventRetrieveOutput,
  IReleaseHistoryListOutput,
} from '@/services/types/responses/gateways.ts';
import type { IGatewaysReleasesHistoriesListQuery } from '@/services/types/query/gateways.ts';
import type { IReleaseInputSLZ } from '@/services/types/body/post/gateways.ts';

const path = '/gateways';

export const createRelease = (apigwId: number, params: IReleaseInputSLZ) =>
  http.post(`${path}/${apigwId}/releases/`, params, { catchError: true });

export const getReleaseEvents = (apigwId: number, historyId: number) =>
  http.get<IReleaseHistoryEventRetrieveOutput>(`${path}/${apigwId}/releases/histories/${historyId}/events/`);

export const getReleaseHistories = (apigwId: number, params: IGatewaysReleasesHistoriesListQuery = {}) =>
  http.get<ICountAndResults<IReleaseHistoryListOutput>>(`${path}/${apigwId}/releases/histories/`, params);
