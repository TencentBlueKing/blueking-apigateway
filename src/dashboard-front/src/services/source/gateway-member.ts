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

import http from '../http';
import type { IGatewayMemberUpdateInputSLZ } from '@/services/types/body/patch/gateway-members';
import type { IGatewayMemberCreateInputSLZ } from '@/services/types/body/post/gateway-members';
import type {
  IGatewayMemberBatchCreateOutput,
  IGatewayMemberOutput,
} from '@/services/types/responses/gateway-members';

// GET /gateways/{gateway_id}/members/
export function getGatewayMemberList(apigwId: number) {
  return http.get<IGatewayMemberOutput[]>(`/gateways/${apigwId}/members/`);
}

// POST /gateways/{gateway_id}/members/
export function createGatewayMembers(
  apigwId: number,
  data: IGatewayMemberCreateInputSLZ[],
) {
  return http.post<IGatewayMemberBatchCreateOutput>(`/gateways/${apigwId}/members/`, data);
}

// PATCH /gateways/{gateway_id}/members/{member_id}/
export function updateGatewayMember(
  apigwId: number,
  memberId: number,
  data: IGatewayMemberUpdateInputSLZ,
) {
  return http.patch<IGatewayMemberOutput>(`/gateways/${apigwId}/members/${memberId}/`, data);
}

// DELETE /gateways/{gateway_id}/members/{member_id}/
export function deleteGatewayMember(apigwId: number, memberId: number) {
  return http.delete<void>(`/gateways/${apigwId}/members/${memberId}/`);
}
