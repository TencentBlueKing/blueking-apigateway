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

import {
  GATEWAY_PERMISSION_MATRIX,
  type GatewayPermissionKey,
  type MemberRole,
} from '@/constants/gateway-permission';

/**
 * 独立于 Store 和路由的权限判定，供路由守卫与角色 Hook 共用。
 * 运营者未声明 permission 时拒绝访问；未知角色始终拒绝访问。
 */
export function canAccessByRole(role: MemberRole | '', permission?: GatewayPermissionKey) {
  if (role === 'administrator') {
    return true;
  }
  if (role !== 'operator' || !permission) {
    return false;
  }
  return !!GATEWAY_PERMISSION_MATRIX[permission]?.operator;
}
