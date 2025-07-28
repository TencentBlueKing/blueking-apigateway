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

/*
* 可编程网关相关 API
*  */

import http from '../http';

const path = '/gateways';

/**
 * 新增标签
 * @param apigwId 网关id
 * @param data 标签名称
 */
export const createLabels = (apigwId: number, data: { name: string }) => http.post(`${path}/${apigwId}/labels/`, data);

/**
 * 删除标签
 * @param apigwId 网关id
 * @param labelsId 标签id
 */
export const deleteLabels = (apigwId: number, labelsId: number) => http.delete(`${path}/${apigwId}/labels/${labelsId}/`);

/**
 * 更新标签
 * @param apigwId 网关id
 * @param labelsId 标签id
 * @param data 标签数据
 */
export const updateLabel = (apigwId: number, labelsId: number, data: { name: string }) =>
  http.put(`${path}/${apigwId}/labels/${labelsId}/`, data);
