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

// 直接从具体文件导入，避免经由 @/stores 桶文件与 @/router 形成循环依赖
import { useGateway } from '@/stores/useGateway';
import { useUserInfo } from '@/stores/useUserInfo';
import {
  GATEWAY_PERMISSION_MATRIX,
  type GatewayPermissionKey,
  type MemberRole,
} from '@/constants/gateway-permission';

export function getGatewayRole(
  username: string,
  maintainers: string[] = [],
  developers: string[] = [],
): MemberRole | '' {
  if (!username) {
    return '';
  }
  if (maintainers.includes(username)) {
    return 'administrator';
  }
  if (developers.includes(username)) {
    return 'operator';
  }
  return '';
}

/**
 * 纯函数版权限判定，供路由守卫等非组件上下文复用
 * @param role 当前用户在该网关下的角色
 * @param permission 权限矩阵 key，对应 GATEWAY_PERMISSION_MATRIX
 * @returns 是否允许访问。运营者采用 fail-closed 策略：未声明 permission 即视为无权限
 */
export function canAccessByRole(role: MemberRole | '', permission?: GatewayPermissionKey) {
  // 管理员及其他角色不受权限矩阵限制
  if (role !== 'operator') {
    return true;
  }
  if (!permission) {
    return false;
  }
  return !!GATEWAY_PERMISSION_MATRIX[permission]?.operator;
}

export function useGatewayRole() {
  const gatewayStore = useGateway();
  const userStore = useUserInfo();

  const currentRole = computed<MemberRole | ''>(() => getGatewayRole(
    userStore.info.username,
    gatewayStore.currentGateway?.maintainers || [],
    gatewayStore.currentGateway?.developers || [],
  ));

  const isAdmin = computed(() => currentRole.value === 'administrator');
  const isOperator = computed(() => currentRole.value === 'operator');
  const canEditBasicInfo = computed(() => !isOperator.value);

  const canAccess = (permission?: GatewayPermissionKey) => {
    return isOperator.value ? canAccessByRole('operator', permission) : true;
  };

  return {
    currentRole,
    isAdmin,
    isOperator,
    canEditBasicInfo,
    canAccess,
  };
}
