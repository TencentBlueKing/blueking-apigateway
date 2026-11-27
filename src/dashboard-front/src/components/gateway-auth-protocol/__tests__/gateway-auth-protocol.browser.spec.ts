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

import { defineComponent, h, nextTick, ref } from 'vue';
import { Form, Radio } from 'bkui-vue';
import { describe, expect, it } from 'vitest';
import { renderWithApp } from '@/components/__tests__/browser-render';
import GatewayAuthProtocol from '../Index.vue';

const mountProtocol = async (initialEnabled: boolean, disabled = true) => {
  const modelValue = ref(initialEnabled);

  const Host = defineComponent({
    setup() {
      return () => h(Form, {
        model: { oauth2_app_enabled: modelValue.value },
      }, () => h(GatewayAuthProtocol, {
        'modelValue': modelValue.value,
        'disabled': disabled,
        'onUpdate:modelValue': (val: boolean) => {
          modelValue.value = val;
        },
      }));
    },
  });

  const { screen } = await renderWithApp(Host, {
    global: {
      components: {
        BkRadioButton: Radio.Button,
      },
    },
  });

  return {
    modelValue,
    screen,
  };
};

describe('GatewayAuthProtocol 浏览器组件测试', () => {
  it('V1 模式下禁用切换且仅展示当前协议描述（不展示告警提示）', async () => {
    const { modelValue, screen } = await mountProtocol(false, true);

    expect(screen.container.textContent).toContain('当前仅支持通过 X-Bkapi-Authorization 传递认证票据的调用方式。');
    expect(screen.container.querySelector('.protocol-warning')).toBeNull();

    const radioButtons = [...screen.container.querySelectorAll<HTMLElement>('.bk-radio-button')];
    expect(radioButtons).toHaveLength(2);
    radioButtons.forEach((btn) => {
      expect(btn.classList.contains('is-disabled')).toBe(true);
    });

    // 尝试点击 V2 按钮不应改变绑定值
    radioButtons[1].click();
    await nextTick();
    expect(modelValue.value).toBe(false);
  });

  it('V2 模式下禁用切换，展示向前兼容描述与 Bearer 覆盖提示', async () => {
    const { modelValue, screen } = await mountProtocol(true, true);

    expect(screen.container.textContent).toContain(
      '蓝鲸认证 V2 支持 OAuth2 授权、个人令牌等方式。目前向前兼容蓝鲸认证 V1 X-Bkapi-Authorization 调用方式。',
    );
    expect(screen.container.textContent).toContain(
      '使用蓝鲸认证 V2 时，如果 API 本身使用了 Authorization: Bearer 请求头，会被平台覆盖。',
    );

    const radioButtons = [...screen.container.querySelectorAll<HTMLElement>('.bk-radio-button')];
    radioButtons[0].click();
    await nextTick();
    expect(modelValue.value).toBe(true);
  });
});
