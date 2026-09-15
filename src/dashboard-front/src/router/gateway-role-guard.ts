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
// 直接导入具体 Store，避免桶文件引入路由循环依赖。
import { useGateway } from '@/stores/useGateway';
import { useGatewayRoleStore } from '@/stores/useGatewayRole';
import { useUserInfo } from '@/stores/useUserInfo';
import { canAccessByRole } from '@/utils/gateway-permission';
import { getGatewayErrorRoute } from '@/utils/gateway-access-error';

const pendingRouters = new WeakSet<Router>();

// 守卫刷新角色时，由目标路由决定落点；布局不能按尚未离开的旧页面权限抢先重定向。
export const isGatewayNavigationPending = (router: Router) => pendingRouters.has(router);

/**
 * 角色决定授权，详情只用于展示。确认无权限进入 404，查询失败进入可重试错误页；
 * 两种异常都不挂载目标业务页面，不能以“请求失败”为由绕过授权。
 */
export function setupGatewayRoleGuard(router: Router) {
  // Vue Router 会取消过期导航，但异步 beforeEach 返回的重定向可能先于其取消检查执行。
  // 因此每次 await 后仍需核对序号，尤其不能让旧请求的失败重定向覆盖已完成的新导航。
  let navigationId = 0;
  const checkedSwitches = new WeakSet<object>();
  router.beforeEach(async (to, from) => {
    const currentNavigationId = ++navigationId;
    pendingRouters.add(router);
    const gatewayId = Number(to.params.id);
    const toNotFound = () => ({
      name: 'GatewayNotFound',
      params: { id: to.params.id },
      replace: true,
    });

    try {
      // 异常页不触发请求，避免失败 → 异常页 → 再次请求形成重试环。
      if (!to.matched.some(record => record.name === 'Resources') || to.meta.skipRoleCheck) {
        return true;
      }
      if (!Number.isSafeInteger(gatewayId) || gatewayId <= 0) {
        return toNotFound();
      }
      const userStore = useUserInfo();
      const gatewayStore = useGateway();
      const roleStore = useGatewayRoleStore();
      if (!userStore.info.username) {
        await userStore.fetchUserInfo();
      }
      if (currentNavigationId !== navigationId) {
        return false;
      }

      const fromGateway = from.matched.some(record => record.name === 'Resources');
      const switchingGateway = fromGateway && from.params.id !== to.params.id;
      // 同网关导航受 Store 的 TTL 约束；重新进入、切换或从异常页重试必须刷新。
      // 仅复用本守卫刚检查过的切换回退，不把普通路由 redirect 当作缓存有效的依据。
      const checkedRedirect = !!to.redirectedFrom && checkedSwitches.has(to.redirectedFrom);
      const force = !checkedRedirect && (!fromGateway || switchingGateway || !!from.meta.skipRoleCheck);
      const role = await roleStore.fetchGatewayRole(gatewayId, force);
      if (currentNavigationId !== navigationId) {
        return false;
      }
      if (role) {
        await gatewayStore.ensureGatewayDetail(gatewayId, force);
      }
      if (currentNavigationId !== navigationId) {
        return false;
      }
      if (canAccessByRole(role, to.meta.permission)) {
        return true;
      }
      // 切换网关优先保留菜单，目标角色不支持该菜单时回退；直接访问无权页面仍是 404。
      if (switchingGateway && canAccessByRole(role, 'basic-view')) {
        checkedSwitches.add(to);
        return {
          name: 'BasicInfo',
          params: { id: to.params.id },
          replace: true,
        };
      }
      return toNotFound();
    }
    catch (error) {
      if (currentNavigationId !== navigationId) {
        return false;
      }
      return getGatewayErrorRoute(error, gatewayId, to.fullPath);
    }
    finally {
      // 旧导航结束时不能解除新导航的保护。
      if (currentNavigationId === navigationId) {
        pendingRouters.delete(router);
      }
    }
  });
}
