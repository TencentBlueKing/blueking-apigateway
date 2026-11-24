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
import BkRateLimitForm from '@/components/plugin/plugin-form/bk-rate-limit/Index.vue';
import { renderWithApp } from '@/components/__tests__/browser-render';

const mountRateLimit = async (data: Record<string, any> = {}) => {
  const formRef = shallowRef<InstanceType<typeof BkRateLimitForm>>();
  const Host = defineComponent({
    setup: () => () => h(BkRateLimitForm, {
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

const setInputValue = (input: HTMLInputElement, value: string) => {
  input.value = value;
  input.dispatchEvent(new Event('input', { bubbles: true }));
  input.dispatchEvent(new Event('change', { bubbles: true }));
};

describe('PluginForm / bk-rate-limit 浏览器表单校验与行操作', () => {
  it('默认初始化并在回显时保留自定义时间窗口，getValue 输出标准 rates 结构', async () => {
    const { formRef, screen } = await mountRateLimit({
      rates: {
        default: {
          tokens: 500,
          period: 120,
        },
        specials: [
          {
            tokens: 20,
            period: 60,
            bk_app_code: 'demo_app',
          },
        ],
      },
    });

    const result = await formRef.value!.getValue();
    expect(result).toEqual({
      rates: {
        default: {
          tokens: 500,
          period: 120,
        },
        specials: [
          {
            tokens: 20,
            period: 60,
            bk_app_code: 'demo_app',
          },
        ],
      },
    });
    expect(screen.container.querySelectorAll('.special-rate-limit-row')).toHaveLength(1);
  });

  it('支持添加、克隆（复制配额但清空应用 ID）与删除特殊应用行', async () => {
    const { formRef, screen } = await mountRateLimit({
      rates: {
        default: {
          tokens: 100,
          period: 1,
        },
        specials: [
          {
            tokens: 50,
            period: 3600,
            bk_app_code: 'app_one',
          },
        ],
      },
    });

    // 点击「克隆」图标：复制 tokens/period，清空 bk_app_code
    screen.container.querySelector<HTMLElement>('.special-rate-limit-row .row-action.icon-ag-copy')!.click();

    await vi.waitFor(() => {
      expect(screen.container.querySelectorAll('.special-rate-limit-row')).toHaveLength(2);
    });

    // 给克隆行填入新应用 ID 后可正常提交
    const secondRowInputs = screen.container
      .querySelectorAll('.special-rate-limit-row')[1]
      .querySelectorAll<HTMLInputElement>('input');
    // 顺序：tokens(number)、select(text)、bk_app_code(text)
    const appCodeInput = secondRowInputs[secondRowInputs.length - 1];
    expect(appCodeInput.value).toBe('');
    setInputValue(appCodeInput, 'app_two');

    const valueAfterClone = await formRef.value!.getValue();
    expect(valueAfterClone.rates.specials).toEqual([
      {
        tokens: 50,
        period: 3600,
        bk_app_code: 'app_one',
      },
      {
        tokens: 50,
        period: 3600,
        bk_app_code: 'app_two',
      },
    ]);

    // 点击「添加」新增一行后，再点击「删除」删掉刚新增的行
    const addBtn = [...screen.container.querySelectorAll<HTMLButtonElement>('button')]
      .find(btn => btn.textContent?.includes('添加'));
    expect(addBtn).not.toBeUndefined();
    addBtn!.click();
    await vi.waitFor(() => {
      expect(screen.container.querySelectorAll('.special-rate-limit-row')).toHaveLength(3);
    });

    const lastRowDeleteBtn = screen.container
      .querySelectorAll('.special-rate-limit-row')[2]
      .querySelector<HTMLElement>('.row-action.icon-ag-delet')!;
    lastRowDeleteBtn.click();
    await vi.waitFor(() => {
      expect(screen.container.querySelectorAll('.special-rate-limit-row')).toHaveLength(2);
    });
  });

  it('拦截非法与重复应用 ID，删除或修正重复项后自动联动清除另一行的重复错误', async () => {
    const { formRef, screen } = await mountRateLimit({
      rates: {
        default: {
          tokens: 100,
          period: 1,
        },
        specials: [
          {
            tokens: 10,
            period: 1,
            bk_app_code: 'dup_app',
          },
          {
            tokens: 20,
            period: 1,
            bk_app_code: 'dup_app',
          },
        ],
      },
    });

    // 存在重复应用 ID，getValue 应校验失败并展示重复提示
    await expect(formRef.value!.getValue()).rejects.toBeTruthy();
    await vi.waitFor(() => {
      expect(screen.container.textContent).toContain('\'dup_app\' 存在重复项');
    });

    // 修改第二行应用 ID 后，自动联动清除第一行的重复报错，表单可通过校验
    const secondRowInputs = screen.container
      .querySelectorAll('.special-rate-limit-row')[1]
      .querySelectorAll<HTMLInputElement>('input');
    setInputValue(secondRowInputs[secondRowInputs.length - 1], 'unique_app');

    await vi.waitFor(() => {
      expect(screen.container.textContent).not.toContain('存在重复项');
    });
    const valid = await formRef.value!.getValue();
    expect(valid.rates.specials.map(item => item.bk_app_code)).toEqual(['dup_app', 'unique_app']);

    // 删除首条重复行后，通过行 ID 映射自动联动清除剩余行的重复提示并可通过提交校验
    const { formRef: deleteDupFormRef, screen: deleteDupScreen } = await mountRateLimit({
      rates: {
        default: {
          tokens: 100,
          period: 1,
        },
        specials: [
          {
            tokens: 10,
            period: 1,
            bk_app_code: 'dup_del',
          },
          {
            tokens: 20,
            period: 60,
            bk_app_code: 'dup_del',
          },
        ],
      },
    });
    await expect(deleteDupFormRef.value!.getValue()).rejects.toBeTruthy();
    await vi.waitFor(() => {
      expect(deleteDupScreen.container.textContent).toContain('\'dup_del\' 存在重复项');
    });

    deleteDupScreen.container
      .querySelectorAll('.special-rate-limit-row')[0]
      .querySelector<HTMLElement>('.row-action.icon-ag-delet')!
      .click();
    await vi.waitFor(() => {
      expect(deleteDupScreen.container.querySelectorAll('.special-rate-limit-row')).toHaveLength(1);
      expect(deleteDupScreen.container.textContent).not.toContain('存在重复项');
    });
    const validAfterDelete = await deleteDupFormRef.value!.getValue();
    expect(validAfterDelete.rates.specials).toEqual([
      {
        tokens: 20,
        period: 60,
        bk_app_code: 'dup_del',
      },
    ]);

    // 回显包含不符合正则格式（大写字母开头）的应用 ID 时保留原值并在提交校验时拦截，clearValidate 可清除错误提示
    const { formRef: invalidFormRef, screen: invalidScreen } = await mountRateLimit({
      rates: {
        default: {
          tokens: 100,
          period: 1,
        },
        specials: [
          {
            tokens: 10,
            period: 1,
            bk_app_code: 'Invalid_App',
          },
        ],
      },
    });
    await expect(invalidFormRef.value!.getValue()).rejects.toBeTruthy();
    await vi.waitFor(() => {
      expect(invalidScreen.container.querySelector('.bk-form-error')?.textContent).toContain('允许小写字母开头');
    });
    invalidFormRef.value!.clearValidate();
    await vi.waitFor(() => {
      expect(invalidScreen.container.querySelector('.bk-form-error')).toBeNull();
    });
  });
});
