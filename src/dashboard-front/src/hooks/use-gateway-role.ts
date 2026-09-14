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
import { type GatewayRoleStatus, useGatewayRoleStore } from '@/stores/useGatewayRole';
import type { GatewayPermissionKey } from '@/constants/gateway-permission';
import { canAccessByRole } from '@/utils/gateway-permission';

/**
 * 当前网关角色的只读视图，不发起请求或监听身份变化。
 * 角色加载由路由守卫负责，身份变化后的补载由网关布局负责。
 */
export function useGatewayRole() {
  const roleStore = useGatewayRoleStore();
  const route = useRoute();

  const gatewayId = computed(() => Number(route.params.id));
  const roleStatus = computed<GatewayRoleStatus>(() => roleStore.roles[gatewayId.value]?.status ?? 'idle');
  const roleError = computed(() => roleStore.roles[gatewayId.value]?.error);
  const currentRole = computed(() => roleStore.roles[gatewayId.value]?.role ?? '');

  const canEditBasicInfo = computed(() => canAccessByRole(currentRole.value, 'basic-edit'));

  const canAccess = (permission?: GatewayPermissionKey) => {
    return canAccessByRole(currentRole.value, permission);
  };

  return {
    currentRole,
    roleStatus,
    roleError,
    canEditBasicInfo,
    canAccess,
  };
}
