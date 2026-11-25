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

import { defineComponent } from 'vue';
import { mount } from '@vue/test-utils';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { useOperationLock } from '@/hooks/use-operation-lock';

// 辅助挂载带生命周期的 Composable，验证 onMounted / onUnmounted 与 AutoImport 协同工作
const mountUseOperationLock = (options?: Parameters<typeof useOperationLock>[0]) => {
  let state!: ReturnType<typeof useOperationLock>;

  const Host = defineComponent({
    setup() {
      state = useOperationLock(options);
      return () => null;
    },
  });

  const wrapper = mount(Host);
  return {
    state,
    wrapper,
  };
};

describe('hooks/use-operation-lock', () => {
  const storageKey = 'test_operation_lock';

  beforeEach(() => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date('2026-11-24T00:00:00.000Z'));
    localStorage.clear();
  });

  afterEach(() => {
    vi.useRealTimers();
    localStorage.clear();
  });

  it('无缓存时默认未锁定，触发 setLock 后倒计时并在到期时自动解锁', () => {
    const { state, wrapper } = mountUseOperationLock({
      lockTime: 3,
      storageKey,
    });

    expect(state.isLocked.value).toBe(false);
    expect(state.remainingTime.value).toBe(0);

    state.setLock();
    expect(state.isLocked.value).toBe(true);
    expect(state.remainingTime.value).toBe(3);
    expect(localStorage.getItem(storageKey)).toBe(String(Math.floor(Date.now() / 1000) + 3));

    vi.advanceTimersByTime(2000);
    expect(state.isLocked.value).toBe(true);
    expect(state.remainingTime.value).toBe(1);

    vi.advanceTimersByTime(1000);
    expect(state.isLocked.value).toBe(false);
    expect(state.remainingTime.value).toBe(0);
    expect(localStorage.getItem(storageKey)).toBeNull();

    wrapper.unmount();
  });

  it('挂载时能从 localStorage 恢复未过期的锁定状态，并清理已过期的记录', () => {
    const nowSeconds = Math.floor(Date.now() / 1000);
    localStorage.setItem(storageKey, String(nowSeconds + 5));

    const active = mountUseOperationLock({ storageKey });
    expect(active.state.isLocked.value).toBe(true);
    expect(active.state.remainingTime.value).toBe(5);
    active.wrapper.unmount();

    localStorage.setItem(storageKey, String(nowSeconds - 1));
    const expired = mountUseOperationLock({ storageKey });
    expect(expired.state.isLocked.value).toBe(false);
    expect(expired.state.remainingTime.value).toBe(0);
    expect(localStorage.getItem(storageKey)).toBeNull();
    expired.wrapper.unmount();
  });

  it('支持手动 clearLock，且组件卸载后不再继续倒计时', () => {
    const { state, wrapper } = mountUseOperationLock({
      lockTime: 5,
      storageKey,
    });

    state.setLock();
    state.clearLock();
    expect(state.isLocked.value).toBe(false);
    expect(state.remainingTime.value).toBe(0);
    expect(localStorage.getItem(storageKey)).toBeNull();

    state.setLock();
    wrapper.unmount();
    vi.advanceTimersByTime(3000);
    expect(state.remainingTime.value).toBe(5);
  });
});
