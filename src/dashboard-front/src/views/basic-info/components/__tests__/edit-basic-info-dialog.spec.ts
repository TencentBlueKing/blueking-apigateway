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

const {
  checkDisplayNameMock,
  patchGatewayMock,
} = vi.hoisted(() => ({
  checkDisplayNameMock: vi.fn().mockResolvedValue(true),
  patchGatewayMock: vi.fn().mockResolvedValue({}),
}));

vi.mock('bkui-vue', async (importOriginal) => {
  const actual = await importOriginal<typeof import('bkui-vue')>();
  return {
    ...actual,
    Message: vi.fn(),
  };
});

vi.mock('@/services/source/gateway/gateway', () => ({
  checkRepoAuthorization: vi.fn(),
  patchGateway: patchGatewayMock,
}));

vi.mock('@/services/source/platform/setting', () => ({
  getEnvVars: vi.fn().mockResolvedValue({}),
}));

vi.mock('@/hooks', () => ({
  useGatewayDisplayNameCheck: () => ({
    checkDisplayName: checkDisplayNameMock,
  }),
}));

import GatewayAuthProtocol from '@/components/gateway-auth-protocol/Index.vue';
import EditBasicInfoDialog from '../EditBasicInfoDialog.vue';

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

const mountEditDialog = (oauth2AppEnabled: boolean) => {
  const pinia = createPinia();
  setActivePinia(pinia);

  return mount(EditBasicInfoDialog, {
    props: {
      modelValue: true,
      initData: {
        id: 12,
        name: 'demo-gw',
        display_name: 'Demo Gateway',
        description: 'old desc',
        maintainers: ['admin'],
        developers: ['dev'],
        is_public: true,
        kind: 0,
        oauth2_app_enabled: oauth2AppEnabled,
        bk_app_codes: [],
        related_app_codes: ['app-1'],
      },
    },
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
        BkDialog: {
          props: ['isShow', 'title', 'width'],
          template: '<div v-if="isShow"><slot /><slot name="footer" /></div>',
        },
        BkForm: BkFormStub,
        BkFormItem: {
          props: ['label', 'property', 'required'],
          template: '<div class="bk-form-item-stub"><slot /></div>',
        },
        BkInput: {
          props: ['modelValue', 'disabled', 'type'],
          emits: ['update:modelValue'],
          template: '<input :value="modelValue" :disabled="disabled" @input="$emit(\'update:modelValue\', $event.target.value)" />',
        },
        BkOption: { template: '<div />' },
        BkSelect: { template: '<div />' },
        BkSwitcher: { template: '<div />' },
        BkTagInput: { template: '<div />' },
      },
    },
  });
};

describe('basic-info/EditBasicInfoDialog 认证协议集成', () => {
  beforeEach(() => {
    patchGatewayMock.mockClear();
  });

  it('V1 网关在编辑基本信息弹窗中禁止切换认证协议，且保存不下发 oauth2_app_enabled', async () => {
    const wrapper = mountEditDialog(false);
    const protocol = wrapper.findComponent(GatewayAuthProtocol);

    expect(protocol.exists()).toBe(true);
    expect(protocol.props('disabled')).toBe(true);
    expect(protocol.text()).toContain('当前仅支持通过 X-Bkapi-Authorization 传递认证票据的调用方式。');
    expect(protocol.find('.protocol-warning').exists()).toBe(false);

    const radioButtons = protocol.findAll('.bk-radio-button');
    expect(radioButtons).toHaveLength(2);
    radioButtons.forEach((btn) => {
      expect(btn.classes()).toContain('is-disabled');
    });

    // 尝试点击切换到 V2 不应改变状态
    await radioButtons[1].trigger('click');
    expect(protocol.props('modelValue')).toBe(false);

    const confirmBtn = wrapper.findAll('button').find(btn => btn.text().trim() === '确定')!;
    await confirmBtn.trigger('click');
    await flushPromises();

    expect(patchGatewayMock).toHaveBeenCalledTimes(1);
    const [gatewayId, payload] = patchGatewayMock.mock.calls[0];
    expect(gatewayId).toBe(12);
    expect('oauth2_app_enabled' in payload).toBe(false);
  });

  it('V2 网关在编辑基本信息弹窗中禁止切换认证协议，且保存不下发 oauth2_app_enabled', async () => {
    const wrapper = mountEditDialog(true);
    const protocol = wrapper.findComponent(GatewayAuthProtocol);

    expect(protocol.exists()).toBe(true);
    expect(protocol.props('disabled')).toBe(true);
    expect(protocol.text()).toContain(
      '蓝鲸认证 V2 支持 OAuth2 授权、个人令牌等方式。目前向前兼容蓝鲸认证 V1 X-Bkapi-Authorization 调用方式。',
    );
    expect(protocol.text()).toContain(
      '使用蓝鲸认证 V2 时，如果 API 本身使用了 Authorization: Bearer 请求头，会被平台覆盖。',
    );

    const radioButtons = protocol.findAll('.bk-radio-button');
    await radioButtons[0].trigger('click');
    expect(protocol.props('modelValue')).toBe(true);

    const confirmBtn = wrapper.findAll('button').find(btn => btn.text().trim() === '确定')!;
    await confirmBtn.trigger('click');
    await flushPromises();

    expect(patchGatewayMock).toHaveBeenCalledTimes(1);
    const [gatewayId, payload] = patchGatewayMock.mock.calls[0];
    expect(gatewayId).toBe(12);
    expect('oauth2_app_enabled' in payload).toBe(false);
  });
});
