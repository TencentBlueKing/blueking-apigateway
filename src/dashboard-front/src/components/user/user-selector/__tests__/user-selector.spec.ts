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
import { mount } from '@vue/test-utils';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const { envState, featureFlagState, userInfoState } = vi.hoisted(() => ({
  envState: { tenantUserDisplayAPI: 'https://user-api.example.com' },
  featureFlagState: { isTenantMode: false },
  userInfoState: { info: { tenant_id: 'default-tenant' } },
}));

vi.mock('@blueking/bk-user-selector', () => ({
  default: {
    name: 'BkUserSelectorStub',
    props: {
      modelValue: {
        type: [Array, String],
        default: '',
      },
      apiBaseUrl: {
        type: String,
        default: '',
      },
      tenantId: {
        type: String,
        default: '',
      },
      multiple: {
        type: Boolean,
        default: true,
      },
      placeholder: {
        type: String,
        default: undefined,
      },
    },
    template: '<div class="bk-user-selector-stub" />',
  },
}));

vi.mock('@/components/user/staff-selector', () => ({
  default: {
    name: 'StaffSelectorStub',
    props: {
      modelValue: {
        type: Array,
        default: () => [],
      },
      multiple: {
        type: Boolean,
        default: true,
      },
      placeholder: {
        type: String,
        default: undefined,
      },
      hasDeleteIcon: {
        type: Boolean,
        default: false,
      },
    },
    template: '<div class="staff-selector-stub" />',
  },
}));

vi.mock('@/stores', () => ({
  useEnv: () => envState,
  useFeatureFlag: () => featureFlagState,
  useUserInfo: () => userInfoState,
}));

import UserSelector from '@/components/user/user-selector/Index.vue';

describe('components/user/user-selector', () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    featureFlagState.isTenantMode = false;
    userInfoState.info.tenant_id = 'default-tenant';
    envState.tenantUserDisplayAPI = 'https://user-api.example.com';
  });

  it('非多租户模式下渲染 StaffSelector，透传 hasDeleteIcon 并将 change 结果同步到 v-model', () => {
    const wrapper = mount(UserSelector, {
      props: {
        modelValue: ['alice'],
        hasDeleteIcon: true,
        placeholder: '请选择成员',
      },
    });

    const staff = wrapper.findComponent({ name: 'StaffSelectorStub' });
    expect(staff.exists()).toBe(true);
    expect(wrapper.findComponent({ name: 'BkUserSelectorStub' }).exists()).toBe(false);
    expect(staff.props()).toEqual({
      modelValue: ['alice'],
      multiple: true,
      placeholder: '请选择成员',
      hasDeleteIcon: true,
    });

    // 正常变更与 null 兜底
    staff.vm.$emit('change', ['alice', 'bob']);
    expect(wrapper.emitted('update:modelValue')?.[0]).toEqual([['alice', 'bob']]);
    expect(wrapper.emitted('change')?.[0]).toEqual([['alice', 'bob']]);

    staff.vm.$emit('change', null);
    expect(wrapper.emitted('update:modelValue')?.[1]).toEqual([[]]);
    expect(wrapper.emitted('change')?.[1]).toEqual([[]]);
  });

  it('多租户模式下切换 BkUserSelector，支持单选字符串绑定与用户对象到用户名数组的统一归一化', () => {
    featureFlagState.isTenantMode = true;

    // 多选模式
    const multi = mount(UserSelector, {
      props: {
        modelValue: ['u1', 'u2'],
        multiple: true,
      },
    });
    const multiSelector = multi.findComponent({ name: 'BkUserSelectorStub' });
    expect(multiSelector.exists()).toBe(true);
    expect(multiSelector.props()).toMatchObject({
      modelValue: ['u1', 'u2'],
      apiBaseUrl: 'https://user-api.example.com',
      tenantId: 'default-tenant',
      multiple: true,
    });

    multiSelector.vm.$emit('change', [{ id: 'u3' }, { id: 'u4' }]);
    expect(multi.emitted('update:modelValue')?.[0]).toEqual([['u3', 'u4']]);
    expect(multi.emitted('change')?.[0]).toEqual([['u3', 'u4']]);

    // 单选模式：向子组件传 string，收到单个用户对象或 null 均归一化为 string[]
    const single = mount(UserSelector, {
      props: {
        modelValue: ['u1'],
        multiple: false,
      },
    });
    const singleSelector = single.findComponent({ name: 'BkUserSelectorStub' });
    expect(singleSelector.props('modelValue')).toBe('u1');

    singleSelector.vm.$emit('change', { id: 'u9' });
    expect(single.emitted('update:modelValue')?.[0]).toEqual([['u9']]);
    expect(single.emitted('change')?.[0]).toEqual([['u9']]);

    singleSelector.vm.$emit('change', null);
    expect(single.emitted('update:modelValue')?.[1]).toEqual([[]]);
  });
});
