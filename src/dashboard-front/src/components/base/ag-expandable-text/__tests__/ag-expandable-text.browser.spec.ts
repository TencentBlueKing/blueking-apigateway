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

import { h, nextTick, ref } from 'vue';
import { describe, expect, it, vi } from 'vitest';
import AgExpandableText from '@/components/base/ag-expandable-text/Index.vue';
import { renderWithApp } from '@/components/__tests__/browser-render';

const LONG_TEXT = Array.from({ length: 16 }, (_, idx) =>
  `第 ${idx + 1} 段用于验证真实浏览器下多行文本溢出检测与展开收起切换的长描述文本。`).join('');

/** 等待浏览器完成布局帧，且组件 onMounted/watchEffect 注册的 setTimeout(checkOverflow, 0) 与 DOM 更新执行完毕 */
const waitForOverflowCheck = async () => {
  await new Promise(resolve => requestAnimationFrame(resolve));
  await new Promise(resolve => setTimeout(resolve, 0));
  await nextTick();
};

const mountInFixedWidth = (
  props: Record<string, any> | (() => Record<string, any>),
  text: string,
  widthPx = 220,
) => {
  const Host = () => h('div', { style: { width: `${widthPx}px` } }, [
    h(AgExpandableText, typeof props === 'function' ? props() : props, {
      description: () => text,
    }),
  ]);
  return renderWithApp(Host);
};

describe('AgExpandableText 浏览器真实排版与展开交互', () => {
  it('短文本未溢出时不展示展开按钮', async () => {
    const { screen } = await mountInFixedWidth({ maxLines: 3 }, '简短描述');

    await waitForOverflowCheck();
    expect(screen.container.querySelector('.toggle-btn')).toBeNull();
  });

  it('超长文本在 maxLines 限制下自动显示展开按钮，并支持点击展开与再次收起', async () => {
    const { screen } = await mountInFixedWidth({
      maxLines: 2,
      fontSize: 14,
      lineHeight: 1.5,
    }, LONG_TEXT);

    await vi.waitFor(() => {
      const btn = screen.container.querySelector<HTMLButtonElement>('.toggle-btn');
      expect(btn).not.toBeNull();
      expect(btn?.textContent).toContain('展开');
    });

    const contentEl = screen.container.querySelector<HTMLElement>('.description-content')!;
    const collapsedHeight = contentEl.getBoundingClientRect().height;
    expect(contentEl.classList.contains('expanded')).toBe(false);

    // 点击展开后移除行数限制，真实渲染高度显著增大
    screen.container.querySelector<HTMLButtonElement>('.toggle-btn')!.click();
    await vi.waitFor(() => {
      expect(contentEl.classList.contains('expanded')).toBe(true);
      expect(screen.container.querySelector('.toggle-btn')?.textContent).toContain('收起');
      expect(contentEl.getBoundingClientRect().height).toBeGreaterThan(collapsedHeight + 40);
    });

    // 再次点击恢复收起态
    screen.container.querySelector<HTMLButtonElement>('.toggle-btn')!.click();
    await vi.waitFor(() => {
      expect(contentEl.classList.contains('expanded')).toBe(false);
      expect(screen.container.querySelector('.toggle-btn')?.textContent).toContain('展开');
    });
  });

  it('dynamicMaxHeight 优先于 maxLines 生效，且支持 showExpandIcon=false 隐藏按钮', async () => {
    const showExpandIcon = ref(true);
    const { screen } = await mountInFixedWidth(() => ({
      maxLines: 10,
      dynamicMaxHeight: 40,
      fontSize: '1rem',
      lineHeight: '20px',
      showExpandIcon: showExpandIcon.value,
    }), LONG_TEXT);

    await vi.waitFor(() => {
      const contentEl = screen.container.querySelector<HTMLElement>('.description-content');
      expect(contentEl?.classList.contains('has-max-height')).toBe(true);
      expect(contentEl!.getBoundingClientRect().height).toBeLessThanOrEqual(41);
      expect(screen.container.querySelector('.toggle-btn')).not.toBeNull();
    });

    // 确认溢出并显示展开按钮后，将 showExpandIcon 切为 false 应立即隐藏按钮
    showExpandIcon.value = false;
    await vi.waitFor(() => {
      expect(screen.container.querySelector('.toggle-btn')).toBeNull();
    });
  });
});
