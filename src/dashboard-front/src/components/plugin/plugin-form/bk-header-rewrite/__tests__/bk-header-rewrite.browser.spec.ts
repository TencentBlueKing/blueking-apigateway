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
import BkHeaderRewriteForm from '@/components/plugin/plugin-form/bk-header-rewrite/Index.vue';
import { renderWithApp } from '@/components/__tests__/browser-render';

const mountHeaderRewrite = async (data: Record<string, any> = {}) => {
  const formRef = shallowRef<InstanceType<typeof BkHeaderRewriteForm>>();
  const Host = defineComponent({
    setup: () => () => h(BkHeaderRewriteForm, {
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

describe('PluginForm / bk-header-rewrite（含 KeyValuePairs / KeysInput）浏览器表单测试', () => {
  it('回显对象数组并兼容旧版字符串数组 remove，getValue 输出标准 { set, remove } 结构', async () => {
    const { formRef } = await mountHeaderRewrite({
      set: [
        {
          key: 'X-Tenant-Id',
          value: 'default',
        },
      ],
      remove: ['X-Legacy-Token', { key: 'X-Debug' }],
    });

    const result = await formRef.value!.getValue();
    expect(result).toEqual({
      set: [
        {
          key: 'X-Tenant-Id',
          value: 'default',
        },
      ],
      remove: [
        { key: 'X-Legacy-Token' },
        { key: 'X-Debug' },
      ],
    });
  });

  it('set 与 remove 均为空时拦截提交，向任一侧新增行后联动清除提示', async () => {
    const { formRef, screen } = await mountHeaderRewrite({});

    await expect(formRef.value!.getValue()).rejects.toBeTruthy();
    await vi.waitFor(() => {
      expect(screen.container.textContent).toContain('请求头设置或删除至少需要配置一个');
    });

    // 点击 KeyValuePairs 的初始加号新增一条设置项
    screen.container.querySelector<HTMLElement>('.key-value-pairs .add-initial .icon-btn')!.click();
    await vi.waitFor(() => {
      expect(screen.container.querySelectorAll('.key-value-pairs .pair-row')).toHaveLength(1);
      expect(screen.container.textContent).not.toContain('请求头设置或删除至少需要配置一个');
    });

    const inputs = screen.container.querySelectorAll<HTMLInputElement>('.key-value-pairs .pair-row input');
    inputs[0].value = 'X-Custom-Header';
    inputs[0].dispatchEvent(new Event('input', { bubbles: true }));
    inputs[1].value = 'enabled';
    inputs[1].dispatchEvent(new Event('input', { bubbles: true }));

    expect(await formRef.value!.getValue()).toEqual({
      set: [{
        key: 'X-Custom-Header',
        value: 'enabled',
      }],
      remove: [],
    });
  });

  it('子组件 KeyValuePairs 与 KeysInput 正确拦截非法键名与重复键名', async () => {
    // 1. KeyValuePairs 重复键名校验拦截
    const dupSet = await mountHeaderRewrite({
      set: [
        {
          key: 'X-Dup',
          value: '1',
        },
        {
          key: 'X-Dup',
          value: '2',
        },
      ],
    });
    await expect(dupSet.formRef.value!.getValue()).rejects.toBeTruthy();
    await vi.waitFor(() => {
      expect(dupSet.screen.container.textContent).toContain('键名已存在');
    });

    // 2. KeysInput 非法字符键名拦截
    const invalidRemove = await mountHeaderRewrite({ remove: [{ key: 'invalid header!' }] });
    await expect(invalidRemove.formRef.value!.getValue()).rejects.toBeTruthy();
    await vi.waitFor(() => {
      expect(invalidRemove.screen.container.textContent).toContain('允许输入：字母、数字、下划线_、连字符-');
    });
  });
});
