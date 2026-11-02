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
import type { IGatewaySDKListOutput } from '@/services/types/responses/gateways.ts';
import type { IGatewaysSdksListQuery } from '@/services/types/query/gateways.ts';
import type { IGatewaySDKGenerateInputSLZ } from '@/services/types/body/post/gateways.ts';

const path = '/gateways';

/**
 * 获取网关 SDK 列表
 * @param gatewayId 网关id
 * @param data 查询参数
 */
export const getSDKList = (gatewayId: number, data: IGatewaysSdksListQuery = {}) =>
  http.get<ICountAndResults<IGatewaySDKListOutput>>(`${path}/${gatewayId}/sdks/`, data);

/**
 * 生成网关 SDK
 * @param gatewayId 网关id
 * @param data 生成参数
 */
export const createSDK = (gatewayId: number, data: IGatewaySDKGenerateInputSLZ) =>
  http.post(`${path}/${gatewayId}/sdks/`, data);
