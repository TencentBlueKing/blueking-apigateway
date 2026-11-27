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

import { defineComponent, h } from 'vue';
import { createPinia, setActivePinia } from 'pinia';
import { flushPromises, mount } from '@vue/test-utils';
import { Radio, Tag } from 'bkui-vue';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import i18n from '@/locales';
import { useGateway, useUserInfo } from '@/stores';

const {
  createGatewayMock,
  patchGatewayMock,
  pushMock,
  routeState,
} = vi.hoisted(() => ({
  createGatewayMock: vi.fn().mockResolvedValue({ id: 88 }),
  patchGatewayMock: vi.fn().mockResolvedValue({}),
  pushMock: vi.fn(),
  routeState: {
    query: {} as Record<string, string>,
  },
}));

vi.mock('vue-router', async (importOriginal) => {
  const actual = await importOriginal<typeof import('vue-router')>();
  return {
    ...actual,
    useRoute: () => routeState,
    useRouter: () => ({
      back: vi.fn(),
      push: pushMock,
    }),
  };
});

vi.mock('bkui-vue', async (importOriginal) => {
  const actual = await importOriginal<typeof import('bkui-vue')>();
  return {
    ...actual,
    Message: vi.fn(),
  };
});

vi.mock('@/services/source/gateway/gateway', () => ({
  checkNameAvailable: vi.fn().mockResolvedValue({ is_available: true }),
  checkRepoAuthorization: vi.fn(),
  createGateway: createGatewayMock,
  patchGateway: patchGatewayMock,
}));

vi.mock('@/services/source/platform/setting', () => ({
  getEnvVars: vi.fn().mockResolvedValue({}),
}));

vi.mock('@/hooks', () => ({
  useGatewayDisplayNameCheck: () => ({
    checkDisplayName: vi.fn().mockResolvedValue(true),
  }),
  usePopInfoBox: vi.fn(),
}));

import GatewayAuthProtocol from '@/components/gateway-auth-protocol/Index.vue';
import CreateGateway from '../CreateGateway.vue';

const BkFormStub = defineComponent({
  name: 'BkFormStub',
  inheritAttrs: false,

  setup(_, { slots, expose }) {
    expose({
      validate: () => Promise.resolve(true),
      clearValidate: () => undefined,
    });
    return () => h('form', slots.default?.());
  },
});

const mountCreateGateway = (options: {
  from?: string
  oauth2AppEnabled?: boolean
} = {}) => {
  const pinia = createPinia();
  setActivePinia(pinia);

  const userStore = useUserInfo();
  userStore.info = {
    ...userStore.info,
    username: 'admin',
    tenant_id: 'default',
  };

  routeState.query = options.from ? { from: options.from } : {};

  const gatewayStore = useGateway();
  if (options.from === 'basic-info') {
    gatewayStore.setCurrentGateway({
      id: 7,
      name: 'demo-gw',
      display_name: 'Demo Gateway',
      description: 'old desc',
      maintainers: ['admin'],
      developers: ['dev'],
      is_public: true,
      kind: 0,
      oauth2_app_enabled: options.oauth2AppEnabled ?? false,
      bk_app_codes: [],
      related_app_codes: ['app-1'],
    });
  }

  const wrapper = mount(CreateGateway, {
    global: {
      plugins: [pinia, i18n],
      components: {
        BkRadioGroup: Radio.Group,
        BkRadioButton: Radio.Button,
        BkTag: Tag,
      },
      stubs: {
        AgIcon: { template: '<i />' },
        BkAlert: { template: '<div />' },
        BkButton: {
          props: ['loading', 'theme'],
          emits: ['click'],
          template: '<button type="button" @click="$emit(\'click\', $event)"><slot /></button>',
        },
        BkForm: BkFormStub,
        BkFormItem: {
          props: ['label', 'property', 'required'],
          template: '<div class="bk-form-item-stub"><slot /></div>',
        },
        BkInput: {
          inheritAttrs: false,
          props: ['modelValue', 'disabled', 'prefix', 'type'],
          emits: ['update:modelValue'],
          template: '<input :value="modelValue" :disabled="disabled" @input="$emit(\'update:modelValue\', $event.target.value)" />',
        },
        BkOption: { template: '<div />' },
        BkPopConfirm: { template: '<div><slot /></div>' },
        BkSelect: { template: '<div />' },
        BkSwitcher: { template: '<div />' },
        BkTagInput: { template: '<div />' },
        BkTimeline: { template: '<div />' },
        UserSelector: { template: '<div />' },
      },
    },
  });

  return {
    gatewayStore,
    wrapper,
  };
};

describe('home/CreateGateway 认证协议集成', () => {
  beforeEach(() => {
    createGatewayMock.mockClear();
    patchGatewayMock.mockClear();
    pushMock.mockClear();
  });

  it('新建模式不渲染认证协议字段，提交创建请求不含 oauth2_app_enabled', async () => {
    const { wrapper } = mountCreateGateway();

    expect(wrapper.findComponent(GatewayAuthProtocol).exists()).toBe(false);

    const confirmBtn = wrapper.findAll('button').find(btn => btn.text().trim() === '确定')!;
    await confirmBtn.trigger('click');
    await flushPromises();

    expect(createGatewayMock).toHaveBeenCalledTimes(1);
    const [payload] = createGatewayMock.mock.calls[0];
    expect('oauth2_app_enabled' in payload).toBe(false);
  });

  it('编辑模式（from=basic-info）禁用认证协议切换，提交保存不含 oauth2_app_enabled 且保持 store 状态不变', async () => {
    const { gatewayStore, wrapper } = mountCreateGateway({
      from: 'basic-info',
      oauth2AppEnabled: false,
    });
    await flushPromises();

    const protocol = wrapper.findComponent(GatewayAuthProtocol);
    expect(protocol.exists()).toBe(true);
    expect(protocol.props('disabled')).toBe(true);

    const radioButtons = protocol.findAll('.bk-radio-button');
    expect(radioButtons).toHaveLength(2);
    radioButtons.forEach((btn) => {
      expect(btn.classes()).toContain('is-disabled');
    });

    await radioButtons[1].trigger('click');
    expect(protocol.props('modelValue')).toBe(false);

    const confirmBtn = wrapper.findAll('button').find(btn => btn.text().trim() === '确定')!;
    await confirmBtn.trigger('click');
    await flushPromises();

    expect(patchGatewayMock).toHaveBeenCalledTimes(1);
    const [gatewayId, payload] = patchGatewayMock.mock.calls[0];
    expect(gatewayId).toBe(7);
    expect('oauth2_app_enabled' in payload).toBe(false);
    expect(gatewayStore.currentGateway?.oauth2_app_enabled).toBe(false);
  });
});
