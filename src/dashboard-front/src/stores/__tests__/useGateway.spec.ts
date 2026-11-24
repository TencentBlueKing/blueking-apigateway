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

const { getGatewayDetailMock } = vi.hoisted(() => ({ getGatewayDetailMock: vi.fn() }));

vi.mock('@/services/source/gateway/gateway', () => ({ getGatewayDetail: getGatewayDetailMock }));

import { GATEWAY_DETAIL_TTL, useGateway } from '@/stores/useGateway';

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

describe('stores/useGateway', () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    getGatewayDetailMock.mockReset();
    vi.useFakeTimers();
    vi.setSystemTime(new Date('2026-11-24T00:00:00.000Z'));
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('getters 准确区分普通/可编程/AI 网关与资源认证 V2', () => {
    const store = useGateway();

    expect(store.isProgrammableGateway).toBe(false);
    expect(store.isAIGateway).toBe(false);
    expect(store.isResourceAuthV2).toBe(false);

    store.setCurrentGateway({
      id: 1,
      name: 'prog-gw',
      kind: 1,
      oauth2_app_enabled: true,
    });
    expect(store.isProgrammableGateway).toBe(true);
    expect(store.isAIGateway).toBe(false);
    expect(store.isResourceAuthV2).toBe(true);

    store.setCurrentGateway({
      id: 2,
      name: 'ai-gw',
      kind: 2,
      oauth2_app_enabled: false,
    });
    expect(store.isProgrammableGateway).toBe(false);
    expect(store.isAIGateway).toBe(true);
    expect(store.isResourceAuthV2).toBe(false);

    store.setApigwId(2);
    store.setApigwName('ai-gw');
    store.setGatewayLabels([{
      id: 1,
      name: 'core',
    }]);
    expect(store.apigwId).toBe(2);
    expect(store.apigwName).toBe('ai-gw');
    expect(store.labels).toEqual([{
      id: 1,
      name: 'core',
    }]);
  });

  it('ensureGatewayDetail 在 TTL 内命中缓存，过期或 force=true 时重新请求', async () => {
    const store = useGateway();
    getGatewayDetailMock
      .mockResolvedValueOnce({
        id: 10,
        name: 'gw-v1',
      })
      .mockResolvedValueOnce({
        id: 10,
        name: 'gw-v2',
      })
      .mockResolvedValueOnce({
        id: 10,
        name: 'gw-v3',
      });

    const first = await store.ensureGatewayDetail(10);
    expect(first.name).toBe('gw-v1');
    expect(getGatewayDetailMock).toHaveBeenCalledTimes(1);

    // 未过期直接返回缓存
    vi.advanceTimersByTime(GATEWAY_DETAIL_TTL - 1);
    const cached = await store.ensureGatewayDetail(10);
    expect(cached.name).toBe('gw-v1');
    expect(getGatewayDetailMock).toHaveBeenCalledTimes(1);

    // force=true 绕过缓存强制刷新
    const forced = await store.ensureGatewayDetail(10, true);
    expect(forced.name).toBe('gw-v2');
    expect(getGatewayDetailMock).toHaveBeenCalledTimes(2);

    // TTL 过期后自动重新拉取
    vi.advanceTimersByTime(GATEWAY_DETAIL_TTL);
    const expired = await store.ensureGatewayDetail(10);
    expect(expired.name).toBe('gw-v3');
    expect(getGatewayDetailMock).toHaveBeenCalledTimes(3);
  });

  it('同一网关的并发在途请求合并为一次接口调用', async () => {
    const store = useGateway();
    const deferred = createDeferred<{
      id: number
      name: string
    }>();
    getGatewayDetailMock.mockReturnValueOnce(deferred.promise);

    const p1 = store.fetchGatewayDetail(10);
    const p2 = store.ensureGatewayDetail(10);
    expect(getGatewayDetailMock).toHaveBeenCalledTimes(1);

    deferred.resolve({
      id: 10,
      name: 'shared-gw',
    });
    const [r1, r2] = await Promise.all([p1, p2]);
    expect(r1).toEqual({
      id: 10,
      name: 'shared-gw',
    });
    expect(r2).toEqual(r1);
    expect(store.currentGateway?.name).toBe('shared-gw');
  });

  it('防止竞态覆盖：切网关、本地保存与清空后，旧的在途响应不会覆盖最新状态', async () => {
    const store = useGateway();

    // 场景 1：先请求网关 1，未返回前已切到网关 2
    const gw1Deferred = createDeferred<{
      id: number
      name: string
    }>();
    const gw2Deferred = createDeferred<{
      id: number
      name: string
    }>();
    getGatewayDetailMock
      .mockReturnValueOnce(gw1Deferred.promise)
      .mockReturnValueOnce(gw2Deferred.promise);

    const p1 = store.fetchGatewayDetail(1);
    const p2 = store.fetchGatewayDetail(2);
    gw2Deferred.resolve({
      id: 2,
      name: 'gw-2',
    });
    await p2;
    gw1Deferred.resolve({
      id: 1,
      name: 'gw-1-stale',
    });
    await p1;
    expect(store.currentGateway?.id).toBe(2);

    // 场景 2：在途请求尚未返回时本地 setCurrentGateway 写入新值，旧响应到达后不得覆盖
    const staleDeferred = createDeferred<{
      id: number
      name: string
    }>();
    getGatewayDetailMock.mockReturnValueOnce(staleDeferred.promise);
    const staleReq = store.fetchGatewayDetail(2);
    store.setCurrentGateway({
      id: 2,
      name: 'gw-2-local-saved',
    });
    staleDeferred.resolve({
      id: 2,
      name: 'gw-2-old-remote',
    });
    await staleReq;
    expect(store.currentGateway?.name).toBe('gw-2-local-saved');

    // 场景 3：clearCurrentGateway 后旧响应到达不得恢复 currentGateway
    const afterClearDeferred = createDeferred<{
      id: number
      name: string
    }>();
    getGatewayDetailMock.mockReturnValueOnce(afterClearDeferred.promise);
    const reqBeforeClear = store.fetchGatewayDetail(3);
    store.clearCurrentGateway();
    afterClearDeferred.resolve({
      id: 3,
      name: 'gw-3-late',
    });
    await reqBeforeClear;
    expect(store.currentGateway).toBeNull();
  });

  it('后端返回不匹配的网关 ID 时抛出协议异常', async () => {
    const store = useGateway();
    getGatewayDetailMock.mockResolvedValueOnce({
      id: 999,
      name: 'wrong-gw',
    });

    await expect(store.fetchGatewayDetail(10)).rejects.toThrow('Unexpected gateway detail response');
    expect(store.currentGateway).toBeNull();
  });
});
