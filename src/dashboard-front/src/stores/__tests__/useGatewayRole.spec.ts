/*
 * TencentBlueKing is pleased to support the open source community by making
 * 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
 * Copyright (C) 2026 Tencent. All rights reserved.
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

import { createPinia, setActivePinia } from 'pinia';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

const { getMyGatewayRoleMock } = vi.hoisted(() => ({ getMyGatewayRoleMock: vi.fn() }));

vi.mock('@/services/source/gateway/member', () => ({ getMyGatewayRole: getMyGatewayRoleMock }));
vi.mock('@/services/source/platform/account', () => ({ getUserInfo: vi.fn() }));

import { GATEWAY_ROLE_TTL, useGatewayRoleStore } from '@/stores/useGatewayRole';
import { useUserInfo } from '@/stores/useUserInfo';

const createDeferred = <T>() => {
  let resolve!: (value: T) => void;
  let reject!: (reason?: unknown) => void;
  const promise = new Promise<T>((res, rej) => {
    resolve = res;
    reject = rej;
  });
  return {
    promise,
    resolve,
    reject,
  };
};

describe('stores/useGatewayRole', () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    getMyGatewayRoleMock.mockReset();
    vi.useFakeTimers();
    vi.setSystemTime(new Date('2026-11-24T00:00:00.000Z'));
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('非法网关 ID 或未登录时不发起请求且不写入缓存', async () => {
    const userStore = useUserInfo();
    const roleStore = useGatewayRoleStore();

    // 未登录
    expect(await roleStore.fetchGatewayRole(10)).toBe('');
    expect(getMyGatewayRoleMock).not.toHaveBeenCalled();
    expect(roleStore.roles[10]).toBeUndefined();

    // 登录后传入非法 ID
    userStore.info.username = 'alice';
    expect(await roleStore.fetchGatewayRole(0)).toBe('');
    expect(await roleStore.fetchGatewayRole(-1)).toBe('');
    expect(await roleStore.fetchGatewayRole(1.5)).toBe('');
    expect(await roleStore.fetchGatewayRole(Number.NaN)).toBe('');
    expect(getMyGatewayRoleMock).not.toHaveBeenCalled();
  });

  it('支持并发在途请求合并、TTL 缓存，且刷新期间立即撤销旧角色并记录 previousRole', async () => {
    const userStore = useUserInfo();
    userStore.info.username = 'alice';
    const roleStore = useGatewayRoleStore();

    const firstDeferred = createDeferred<{ role: string }>();
    getMyGatewayRoleMock.mockReturnValueOnce(firstDeferred.promise);

    const p1 = roleStore.fetchGatewayRole(10);
    const p2 = roleStore.fetchGatewayRole(10);
    expect(getMyGatewayRoleMock).toHaveBeenCalledTimes(1);
    expect(roleStore.roles[10]?.status).toBe('loading');
    expect(roleStore.roles[10]?.role).toBe('');

    firstDeferred.resolve({ role: 'administrator' });
    const [r1, r2] = await Promise.all([p1, p2]);
    expect(r1).toBe('administrator');
    expect(r2).toBe('administrator');
    expect(roleStore.roles[10]?.status).toBe('ready');
    expect(roleStore.roles[10]?.role).toBe('administrator');
    expect(getMyGatewayRoleMock).toHaveBeenCalledTimes(1);

    // TTL 有效期内直接命中缓存
    vi.advanceTimersByTime(GATEWAY_ROLE_TTL - 1);
    expect(await roleStore.fetchGatewayRole(10)).toBe('administrator');
    expect(getMyGatewayRoleMock).toHaveBeenCalledTimes(1);

    // TTL 过期后重新请求：刷新期间立即清空 role，保留 previousRole
    vi.advanceTimersByTime(1);
    const refreshDeferred = createDeferred<{ role: string }>();
    getMyGatewayRoleMock.mockReturnValueOnce(refreshDeferred.promise);

    const refreshPromise = roleStore.fetchGatewayRole(10);
    expect(roleStore.roles[10]).toEqual({
      role: '',
      status: 'loading',
      previousRole: 'administrator',
    });

    refreshDeferred.resolve({ role: 'operator' });
    expect(await refreshPromise).toBe('operator');
    expect(roleStore.roles[10]?.role).toBe('operator');
    expect(roleStore.roles[10]?.previousRole).toBeUndefined();
  });

  it('保留错误态避免重复请求，支持 force 重试，并拒绝非法协议角色', async () => {
    const userStore = useUserInfo();
    userStore.info.username = 'alice';
    const roleStore = useGatewayRoleStore();

    const netErr = new Error('network down');
    getMyGatewayRoleMock.mockRejectedValueOnce(netErr);
    await expect(roleStore.fetchGatewayRole(10)).rejects.toBe(netErr);
    expect(roleStore.roles[10]).toEqual({
      role: '',
      status: 'error',
      error: netErr,
    });

    // 非 force 再次调用直接复用缓存错误，不再发请求
    await expect(roleStore.fetchGatewayRole(10)).rejects.toBe(netErr);
    expect(getMyGatewayRoleMock).toHaveBeenCalledTimes(1);

    // force=true 重新发起请求；返回未知角色视为协议异常
    getMyGatewayRoleMock.mockResolvedValueOnce({ role: 'unknown-role' });
    await expect(roleStore.fetchGatewayRole(10, true)).rejects.toThrow('Unexpected gateway role response');
    expect(roleStore.roles[10]?.status).toBe('error');

    // 再次 force=true 恢复正常
    getMyGatewayRoleMock.mockResolvedValueOnce({ role: 'operator' });
    expect(await roleStore.fetchGatewayRole(10, true)).toBe('operator');
    expect(roleStore.roles[10]?.status).toBe('ready');
  });

  it('invalidateGatewayRole 与身份切换会同步清缓存并使旧的在途响应失效', async () => {
    const userStore = useUserInfo();
    userStore.info.username = 'alice';
    userStore.info.tenant_id = 't1';
    const roleStore = useGatewayRoleStore();

    // 发起请求后主动失效，旧响应既不写缓存也返回空串
    const staleDeferred = createDeferred<{ role: string }>();
    getMyGatewayRoleMock.mockReturnValueOnce(staleDeferred.promise);
    const stalePromise = roleStore.fetchGatewayRole(10);
    roleStore.invalidateGatewayRole(10);
    staleDeferred.resolve({ role: 'administrator' });
    expect(await stalePromise).toBe('');
    expect(roleStore.roles[10]).toBeUndefined();

    // 正常加载后，仅更新 display_name 不清缓存
    getMyGatewayRoleMock.mockResolvedValueOnce({ role: 'administrator' });
    expect(await roleStore.fetchGatewayRole(10)).toBe('administrator');
    userStore.info.display_name = 'Alice Wang';
    expect(roleStore.roles[10]?.role).toBe('administrator');

    // 切换 username 或 tenant_id 时同步清空全部缓存角色
    userStore.info.username = 'bob';
    expect(roleStore.roles).toEqual({});

    getMyGatewayRoleMock.mockResolvedValueOnce({ role: 'operator' });
    expect(await roleStore.fetchGatewayRole(10)).toBe('operator');
    userStore.info.tenant_id = 't2';
    expect(roleStore.roles).toEqual({});
  });
});
