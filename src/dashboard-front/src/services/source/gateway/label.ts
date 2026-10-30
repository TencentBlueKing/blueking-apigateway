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
* 网关标签相关 API
*  */

import http from '@/services/http';
import type { IGatewayLabelOutput } from '@/services/types/responses/gateways.ts';
import type { IGatewaysLabelsListQuery } from '@/services/types/query/gateways.ts';
import type { IGatewayLabelInputSLZ } from '@/services/types/body/post/gateways.ts';

const path = '/gateways';

/**
 * 获取标签列表
 * @param gatewayId 网关id
 * @param query 查询参数
 */
export const getLabelList = (gatewayId: number, query: IGatewaysLabelsListQuery = {}) =>
  http.get<IGatewayLabelOutput[]>(`${path}/${gatewayId}/labels/`, query);

/**
 * 新增标签
 * @param gatewayId 网关id
 * @param data 标签名称
 */
export const createLabel = (gatewayId: number, data: IGatewayLabelInputSLZ) =>
  http.post(`${path}/${gatewayId}/labels/`, data);

/**
 * 删除标签
 * @param gatewayId 网关id
 * @param labelsId 标签id
 */
export const deleteLabel = (gatewayId: number, labelsId: number) => http.delete(`${path}/${gatewayId}/labels/${labelsId}/`);

/**
 * 更新标签
 * @param gatewayId 网关id
 * @param labelsId 标签id
 * @param data 标签数据
 */
export const updateLabel = (gatewayId: number, labelsId: number, data: IGatewayLabelInputSLZ) =>
  http.put(`${path}/${gatewayId}/labels/${labelsId}/`, data);
