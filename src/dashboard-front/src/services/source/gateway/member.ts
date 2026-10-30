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
import type { IGatewayMemberUpdateInputSLZ } from '@/services/types/body/patch/gateway-members';
import type { IGatewayMemberCreateInputSLZ } from '@/services/types/body/post/gateway-members';
import type {
  GatewayMemberRole,
  IGatewayMemberBatchCreateOutput,
  IGatewayMemberOutput,
} from '@/services/types/responses/gateway-members';

const path = '/gateways';

/**
 * 获取网关成员列表
 * @param gatewayId 网关id
 */
export const getGatewayMemberList = (gatewayId: number) =>
  http.get<IGatewayMemberOutput[]>(`${path}/${gatewayId}/members/`);

/**
 * 批量添加网关成员
 * @param gatewayId 网关id
 * @param data 成员列表
 */
export const createGatewayMembers = (gatewayId: number, data: IGatewayMemberCreateInputSLZ[]) =>
  http.post<IGatewayMemberBatchCreateOutput>(`${path}/${gatewayId}/members/`, data);

/**
 * 修改网关成员（如角色）
 * @param gatewayId 网关id
 * @param memberId 成员id
 * @param data 修改内容
 */
export const patchGatewayMember = (gatewayId: number, memberId: number, data: IGatewayMemberUpdateInputSLZ) =>
  http.patch<IGatewayMemberOutput>(`${path}/${gatewayId}/members/${memberId}/`, data);

/**
 * 删除网关成员
 * @param gatewayId 网关id
 * @param memberId 成员id
 */
export const deleteGatewayMember = (gatewayId: number, memberId: number) =>
  http.delete<void>(`${path}/${gatewayId}/members/${memberId}/`);

/**
 * 获取当前用户在网关中的角色
 * @param gatewayId 网关id
 */
export const getMyGatewayRole = (gatewayId: number) =>
  http.get<{ role: GatewayMemberRole }>(`${path}/${gatewayId}/me/role/`);
