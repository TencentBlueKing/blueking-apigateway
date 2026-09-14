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

import type { Router } from 'vue-router';
// 直接从具体文件导入，避免经由 @/stores、@/hooks 桶文件放大循环依赖
import { useGateway } from '@/stores/useGateway';
import { useUserInfo } from '@/stores/useUserInfo';
import { canAccessByRole, getGatewayRole } from '@/hooks/use-gateway-role';

/**
 * 网关内页面的角色权限守卫
 * 依据当前用户在该网关下的角色（administrator / operator）判断能否进入目标页面，
 * 无权限或网关不存在时统一导向网关内 404 页面
 */
export function setupGatewayRoleGuard(router: Router) {
  router.beforeEach(async (to) => {
    // 仅 /:id 下的网关内路由需要角色校验
    if (!to.matched.some(record => record.name === 'Resources')) {
      return true;
    }

    // 404 等异常页自身跳过，避免死循环
    if (to.meta.skipRoleCheck) {
      return true;
    }

    const gatewayId = Number(to.params.id);
    const toNotFound = () => ({
      name: 'GatewayNotFound',
      params: { id: to.params.id },
      replace: true,
    });

    if (!gatewayId) {
      return toNotFound();
    }

    const userStore = useUserInfo();
    const gatewayStore = useGateway();

    try {
      // 角色判定依赖 username 与网关的 maintainers/developers，必须先就绪，
      // 否则刷新页面时角色为空会导致校验被绕过
      if (!userStore.info.username) {
        await userStore.fetchUserInfo();
      }
      await gatewayStore.ensureGatewayDetail(gatewayId);
    }
    catch {
      // 网关不存在或当前用户无权查看，同样视为页面不存在
      return toNotFound();
    }

    const role = getGatewayRole(
      userStore.info.username,
      gatewayStore.currentGateway?.maintainers,
      gatewayStore.currentGateway?.developers,
    );

    // 运营者采用 fail-closed 策略，未声明 permission 的网关内路由会被拒绝，
    // 漏标情况由 audit-route-permissions 在开发环境启动时统一提示
    if (!canAccessByRole(role, to.meta.permission)) {
      return toNotFound();
    }

    return true;
  });
}
