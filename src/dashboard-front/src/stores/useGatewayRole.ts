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

import { defineStore } from 'pinia';
import { MEMBER_ROLES, type MemberRole } from '@/constants/gateway-permission';
import { getUserGatewayRole } from '@/services/source/me';
import { useUserInfo } from './useUserInfo';

export type GatewayRoleStatus = 'idle' | 'loading' | 'ready' | 'error';

// 按需过期，不后台轮询；同网关导航最多复用一分钟前的角色。
export const GATEWAY_ROLE_TTL = 60_000;

interface IGatewayRoleState {
  // 空字符串表示当前没有可信角色，权限判断应拒绝放行。
  role: MemberRole | ''
  status: Exclude<GatewayRoleStatus, 'idle'>
  expiresAt?: number
  error?: unknown
}

/**
 * 只管理角色数据、请求和缓存，不读取路由或决定页面跳转。
 * 与网关详情分离：maintainers/developers 只用于展示、编辑，不能作为授权依据。
 */
export const useGatewayRoleStore = defineStore('useGatewayRole', () => {
  const userStore = useUserInfo();
  // 按网关 ID 隔离当前身份的角色；没有对应条目时，Hook 将其视为 idle（未加载）。
  const roles = ref<Partial<Record<number, IGatewayRoleState>>>({});
  // 内部非响应式缓存：既复用在途 Promise，也用 Promise 身份识别回调是否仍然有效。
  const requests = new Map<number, Promise<MemberRole | ''>>();

  // 清空不会取消已发出的 HTTP 请求；移除 Promise 后，其回调不再有权更新角色状态。
  const clearRoles = () => {
    roles.value = {};
    requests.clear();
  };

  // 成员调整等操作只使指定网关失效；是否重新查询由调用方决定，此处不自动请求。
  const invalidateGatewayRole = (gatewayId: number) => {
    if (!Number.isSafeInteger(gatewayId) || gatewayId <= 0) {
      return;
    }
    delete roles.value[gatewayId];
    requests.delete(gatewayId);
  };

  /**
   * 获取接口角色，成功时返回已知角色或空字符串，当前请求失败时记录 error 并向调用方抛出异常。
   * force 只绕过已有结果缓存，不绕过在途请求；需要使旧请求失效时先调用 invalidateGatewayRole。
   */
  const fetchGatewayRole = (gatewayId: number, force = false): Promise<MemberRole | ''> => {
    // 身份未就绪或 ID 非法时不发请求，也不创建缓存条目。
    if (!Number.isSafeInteger(gatewayId) || gatewayId <= 0 || !userStore.info.username) {
      return Promise.resolve('');
    }
    // 路由守卫与多个组件共享在途请求，避免同一网关重复查询。
    const pending = requests.get(gatewayId);
    if (pending) {
      return pending;
    }
    const cached = roles.value[gatewayId];
    // 错误状态也保留，避免多个调用方或 404 跳转反复重试；重试需要 force 或先使缓存失效。
    if (!force && cached?.status === 'error') {
      // 保留查询失败的语义，不能把网络故障转换成“已确认没有角色”。
      return Promise.reject(cached.error);
    }
    if (!force && cached?.status === 'ready' && Date.now() < (cached.expiresAt ?? 0)) {
      return Promise.resolve(cached.role);
    }

    // 刷新期间立即撤销旧角色，不能在新结果到达前继续沿用旧权限。
    roles.value[gatewayId] = {
      role: '',
      status: 'loading',
    };
    const request: Promise<MemberRole | ''> = getUserGatewayRole(gatewayId)
      .then((data) => {
        // 身份变化、主动失效或新请求已替代当前请求时，旧响应既不写缓存，也不返回旧角色，
        // 避免等待该 Promise 的旧导航继续用过期结果授权。
        if (requests.get(gatewayId) !== request) {
          return '';
        }
        // 协议异常不等于已确认无权限；仍拒绝授权，但允许用户在错误页重试。
        if (!MEMBER_ROLES.includes(data?.role)) {
          throw new Error('Unexpected gateway role response');
        }
        const { role } = data;
        roles.value[gatewayId] = {
          role,
          status: 'ready',
          expiresAt: Date.now() + GATEWAY_ROLE_TTL,
        };
        return role;
      })
      .catch((error) => {
        // 旧请求的失败不能覆盖新请求的状态；异常仍交由各自的调用方处理。
        if (requests.get(gatewayId) === request) {
          roles.value[gatewayId] = {
            role: '',
            status: 'error',
            error,
          };
        }
        throw error;
      })
      .finally(() => {
        // 只清理自己的在途标记，不能误删失效后重新发起的请求。
        if (requests.get(gatewayId) === request) {
          requests.delete(gatewayId);
        }
      });
    requests.set(gatewayId, request);
    return request;
  };

  // 仅监听用户/租户标识，避免 App 刷新同一身份的资料时反复清缓存。
  // sync 确保身份变化时同步撤销旧权限；当前网关的重新加载由布局负责，不在 Store 中触发。
  watch(
    [() => userStore.info.username, () => userStore.info.tenant_id],
    clearRoles,
    { flush: 'sync' },
  );

  // Setup Store：返回的 ref 被 Pinia 识别为 state，返回的函数被识别为 actions。
  return {
    roles,
    fetchGatewayRole,
    invalidateGatewayRole,
    clearRoles,
  };
});
