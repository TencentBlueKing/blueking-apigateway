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
import { mount } from '@vue/test-utils';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { useGateway } from '@/stores';
import { useTextGetter } from '@/hooks/use-text-getter';

vi.mock('vue-i18n', async (importOriginal) => {
  const actual = await importOriginal<typeof import('vue-i18n')>();
  return {
    ...actual,
    useI18n: () => ({ t: (key: string) => key }),
  };
});

const createTextGetter = (isV2: boolean) => {
  const pinia = createPinia();
  setActivePinia(pinia);
  const gatewayStore = useGateway();
  gatewayStore.setCurrentGateway({
    id: 1,
    name: 'demo-gw',
    oauth2_app_enabled: isV2,
  });

  let api!: ReturnType<typeof useTextGetter>;
  const Host = defineComponent({
    setup() {
      api = useTextGetter();
      return () => h('div');
    },
  });
  const wrapper = mount(Host, {
    global: {
      plugins: [pinia],
    },
  });
  return {
    api,
    wrapper,
  };
};

describe('hooks/use-text-getter', () => {
  beforeEach(() => {
    setActivePinia(createPinia());
  });

  it('V1 模式下返回认证大类组合文案且不附加 V2 用户子方式括号说明', () => {
    const { api, wrapper } = createTextGetter(false);

    expect(api.getAuthConfigText({
      auth_verified_required: true,
      app_verified_required: true,
      resource_perm_required: true,
      oauth2_personal_client_enabled: true,
    })).toBe('用户认证、应用认证');

    expect(api.getAuthConfigText({
      auth_verified_required: true,
      app_verified_required: false,
      resource_perm_required: false,
    })).toBe('用户认证');

    expect(api.getAuthConfigText({
      auth_verified_required: false,
      app_verified_required: true,
      resource_perm_required: true,
    })).toBe('应用认证');

    expect(api.getAuthConfigText({
      auth_verified_required: false,
      app_verified_required: false,
      resource_perm_required: false,
    })).toBe('不认证');

    expect(api.getAuthConfigText(null)).toBe('--');
    expect(api.getAuthConfigText('{invalid')).toBe('--');

    wrapper.unmount();
  });

  it('V2 模式下在用户认证后附加具体用户认证方式，应用认证与不认证直接返回类型名', () => {
    const { api, wrapper } = createTextGetter(true);

    expect(api.getAuthConfigText({
      auth_verified_required: true,
      app_verified_required: true,
      resource_perm_required: true,
      oauth2_personal_client_enabled: true,
      oauth2_public_client_enabled: false,
    })).toBe('用户认证（个人令牌、OAuth2 授权）');

    expect(api.getAuthConfigText(JSON.stringify({
      auth_verified_required: true,
      app_verified_required: false,
      resource_perm_required: false,
      oauth2_personal_client_enabled: false,
      oauth2_public_client_enabled: true,
    }))).toBe('用户认证（公开客户端）');

    // 用户认证但未勾选任何 V2 子方式时仅返回「用户认证」
    expect(api.getAuthConfigText({
      auth_verified_required: true,
      app_verified_required: false,
      resource_perm_required: false,
      oauth2_personal_client_enabled: false,
      oauth2_public_client_enabled: false,
    })).toBe('用户认证');

    expect(api.getAuthConfigText({
      auth_verified_required: false,
      app_verified_required: true,
      resource_perm_required: true,
    })).toBe('应用认证');

    expect(api.getAuthConfigText({
      auth_verified_required: false,
      app_verified_required: false,
      resource_perm_required: false,
    })).toBe('不认证');

    wrapper.unmount();
  });

  it('准确转换校验应用权限、是否公开与允许申请权限文案，并安全处理异常入参', () => {
    const { api, wrapper } = createTextGetter(true);

    expect(api.getPermRequiredText({
      app_verified_required: true,
      resource_perm_required: true,
    })).toBe('是');
    expect(api.getPermRequiredText({
      app_verified_required: true,
      resource_perm_required: false,
    })).toBe('否');
    expect(api.getPermRequiredText('{"app_verified_required":true,"resource_perm_required":true}')).toBe('是');
    expect(api.getPermRequiredText('{"app_verified_required":true,"resource_perm_required":false}')).toBe('否');
    expect(api.getPermRequiredText(null)).toBe('--');
    expect(api.getPermRequiredText(undefined)).toBe('--');
    expect(api.getPermRequiredText('')).toBe('--');
    expect(api.getPermRequiredText('{bad-json')).toBe('--');

    // 公开设置与允许申请权限文案（保持 undefined/null 默认为「是」的存量约定）
    expect(api.getPublicSettingText(true)).toBe('是');
    expect(api.getPublicSettingText(false)).toBe('否');
    expect(api.getPublicSettingText(undefined)).toBe('是');

    expect(api.getAllowApplyPermissionText(true)).toBe('是');
    expect(api.getAllowApplyPermissionText(false)).toBe('否');
    expect(api.getAllowApplyPermissionText(null)).toBe('是');

    wrapper.unmount();
  });

  it('app_verified_required 为 false 或缺失时均与详情页口径一致返回「否」，非对象 JSON 返回「--」', () => {
    const { api, wrapper } = createTextGetter(true);

    // 与 canConfigureResourcePerm / 详情页 / 版本对比保持统一口径
    expect(api.getPermRequiredText({
      app_verified_required: false,
      resource_perm_required: true,
    })).toBe('否');
    expect(api.getPermRequiredText({ resource_perm_required: true })).toBe('否');
    expect(api.getPermRequiredText('[]')).toBe('--');

    wrapper.unmount();
  });
});
