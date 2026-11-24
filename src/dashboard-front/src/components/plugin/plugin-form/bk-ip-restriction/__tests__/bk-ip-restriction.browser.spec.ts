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

import { defineComponent, h, shallowRef } from 'vue';
import { describe, expect, it, vi } from 'vitest';
import BkIpRestrictionForm from '@/components/plugin/plugin-form/bk-ip-restriction/Index.vue';
import { renderWithApp } from '@/components/__tests__/browser-render';

const mountIpForm = async (data: Record<string, any> = {}) => {
  const formRef = shallowRef<InstanceType<typeof BkIpRestrictionForm>>();
  const Host = defineComponent({
    setup: () => () => h(BkIpRestrictionForm, {
      ref: formRef,
      data,
    }),
  });
  const { screen } = await renderWithApp(Host);
  return {
    formRef,
    screen,
  };
};

describe('PluginForm / bk-ip-restriction 浏览器表单校验与草稿切换', () => {
  it('默认选中白名单，仅传入黑名单时自动回显黑名单并仅提交当前类型', async () => {
    const { formRef, screen } = await mountIpForm({ blacklist: '10.0.0.1\n10.0.0.2' });

    const textarea = screen.container.querySelector<HTMLTextAreaElement>('textarea')!;
    expect(textarea.value).toBe('10.0.0.1\n10.0.0.2');
    expect(await formRef.value!.getValue()).toEqual({ blacklist: '10.0.0.1\n10.0.0.2' });
  });

  it('校验空值与最小长度（7 字符），并在切换白/黑名单时保留各自草稿与清理错误提示', async () => {
    const { formRef, screen } = await mountIpForm({ whitelist: '1.1.1' });

    // 短于 7 个字符应拦截
    await expect(formRef.value!.getValue()).rejects.toBeTruthy();
    await vi.waitFor(() => {
      expect(screen.container.textContent).toContain('白名单不应少于7个字符');
    });

    // 切换到黑名单应清除白名单错误并保留空草稿
    const radios = screen.container.querySelectorAll<HTMLElement>('.bk-radio');
    radios[1].click();
    await vi.waitFor(() => {
      expect(screen.container.textContent).not.toContain('白名单不应少于7个字符');
      expect(screen.container.querySelector<HTMLTextAreaElement>('textarea')!.value).toBe('');
    });

    // 黑名单输入合法 IP 并校验提交
    const blacklistTextarea = screen.container.querySelector<HTMLTextAreaElement>('textarea')!;
    blacklistTextarea.value = '192.168.1.1';
    blacklistTextarea.dispatchEvent(new Event('input', { bubbles: true }));

    expect(await formRef.value!.getValue()).toEqual({ blacklist: '192.168.1.1' });

    // 切回白名单仍保留之前填写的草稿内容
    radios[0].click();
    await vi.waitFor(() => {
      expect(screen.container.querySelector<HTMLTextAreaElement>('textarea')!.value).toBe('1.1.1');
    });
  });
});
