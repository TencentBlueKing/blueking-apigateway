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

import { h, ref } from 'vue';
import { describe, expect, it, vi } from 'vitest';
import AgCopyButton from '@/components/base/ag-copy-button/Index.vue';
import AgDropdown from '@/components/base/ag-dropdown/Index.vue';
import AgMarkdownViewer from '@/components/base/ag-markdown-viewer/Index.vue';
import AgSideslider from '@/components/base/ag-sideslider/Index.vue';
import AgStatusDot from '@/components/base/ag-status-dot/Index.vue';
import { renderWithApp } from '@/components/__tests__/browser-render';

/** 拦截真实 copy() 执行的 document.execCommand('copy')，捕获被选中复制的文本 */
const spyCopyCommand = () => {
  const copiedTexts: string[] = [];
  const spy = vi.spyOn(document, 'execCommand').mockImplementation((commandId: string) => {
    if (commandId === 'copy') {
      const textarea = document.body.querySelector<HTMLTextAreaElement>('textarea[readonly]');
      copiedTexts.push(textarea?.value ?? '');
    }
    return true;
  });
  return {
    copiedTexts,
    spy,
  };
};

describe('基础通用组件浏览器交互（Sideslider / Dropdown / MarkdownViewer / CopyButton / StatusDot）', () => {
  it('AgSideslider 渲染标题与插槽，并在 initData 未改/已改时按 compare 决定直接关闭或弹确认框', async () => {
    const isShow = ref(true);
    const currentForm = ref({ name: 'demo' });
    const onClosed = vi.fn();

    const Host = () => h(AgSideslider, {
      'modelValue': isShow.value,
      'onUpdate:modelValue': (val: boolean) => {
        isShow.value = val;
      },
      'title': '测试抽屉',
      'initData': { name: 'demo' },
      'onCompare': (cb: (data: object) => void) => {
        cb(currentForm.value);
      },
      onClosed,
    }, {
      default: () => h('div', { class: 'slider-body' }, '主体内容'),
      footer: () => h('div', { class: 'slider-footer' }, '底部按钮'),
    });

    await renderWithApp(Host);

    await vi.waitFor(() => {
      expect(document.body.textContent).toContain('测试抽屉');
      expect(document.body.querySelector('.slider-body')?.textContent).toBe('主体内容');
      expect(document.body.querySelector('.slider-footer')?.textContent).toBe('底部按钮');
    });

    // 数据被修改时，点击关闭图标应弹出二次确认框；点「取消」保留抽屉
    currentForm.value = { name: 'modified' };
    const closeBtn = document.body.querySelector<HTMLElement>('.bk-sideslider-close');
    expect(closeBtn).not.toBeNull();
    closeBtn!.click();

    await vi.waitFor(() => {
      expect(document.body.textContent).toContain('确认离开当前页？');
    });

    const cancelBtn = [...document.body.querySelectorAll<HTMLButtonElement>('.bk-infobox-footer button')]
      .find(btn => btn.textContent?.includes('取消'));
    expect(cancelBtn).not.toBeUndefined();
    cancelBtn!.click();

    await vi.waitFor(() => {
      const wrapper = document.body.querySelector<HTMLElement>('.bk-infobox .bk-modal-wrapper');
      expect(wrapper?.style.display).toBe('none');
      expect(isShow.value).toBe(true);
    });

    // 数据还原为未修改状态后，再次点击关闭应直接关闭抽屉
    currentForm.value = { name: 'demo' };
    closeBtn!.click();
    await vi.waitFor(() => {
      expect(isShow.value).toBe(false);
    });
  });

  it('AgDropdown 点击打开菜单，无 tooltips 项不触发 Vue 告警，且忽略禁用项并响应可用项触发 on-change', async () => {
    const warnSpy = vi.spyOn(console, 'warn');
    const onChange = vi.fn();
    const { screen } = await renderWithApp(AgDropdown, {
      props: {
        text: '批量操作',
        dropdownList: [
          {
            label: '已禁用项',
            value: 'disabled-item',
            disabled: true,
            tooltips: '不可用',
          },
          {
            label: '导出资源',
            value: 'export',
          },
        ],
        onOnChange: onChange,
      },
    });

    screen.container.querySelector<HTMLButtonElement>('button')!.click();
    await vi.waitFor(() => {
      expect(document.body.querySelectorAll('.bk-dropdown-item').length).toBe(2);
    });

    // 回归校验：未配置 tooltips 的菜单项经兜底为空串后，不再触发 bkTooltips 的 Invalid vnode type 告警
    expect(warnSpy).not.toHaveBeenCalled();

    const items = [...document.body.querySelectorAll<HTMLElement>('.bk-dropdown-item')];
    items[0].click();
    expect(onChange).not.toHaveBeenCalled();

    items[1].click();
    expect(onChange).toHaveBeenCalledTimes(1);
    expect(onChange).toHaveBeenCalledWith(expect.objectContaining({
      label: '导出资源',
      value: 'export',
    }));
  });

  it('AgMarkdownViewer 自动补齐链接 target、注入代码块复制/安装按钮，且内容更新不重复包裹', async () => {
    const { copiedTexts } = spyCopyCommand();
    const openSpy = vi.spyOn(window, 'open').mockImplementation(() => null);
    const html = ref('<p><a href="https://example.com">外链</a></p><pre><code>curl https://api.test</code></pre>');

    const Host = () => h(AgMarkdownViewer, {
      markdownHtml: html.value,
      installUrl: 'https://docs.example.com/install',
    });

    await renderWithApp(Host);

    await vi.waitFor(() => {
      const link = document.querySelector<HTMLAnchorElement>('#resMarkdown a');
      expect(link?.target).toBe('_blank');
      expect(document.querySelectorAll('#resMarkdown .pre-wrapper')).toHaveLength(1);
      expect(document.querySelector('#resMarkdown .ag-markdown-view__copy-btn')).not.toBeNull();
      expect(document.querySelector('#resMarkdown .ag-markdown-view__install-btn')).not.toBeNull();
    });

    // 点击复制与安装按钮
    document.querySelector<HTMLButtonElement>('#resMarkdown .ag-markdown-view__copy-btn')!.click();
    expect(copiedTexts.at(-1)).toBe('curl https://api.test');

    document.querySelector<HTMLButtonElement>('#resMarkdown .ag-markdown-view__install-btn')!.click();
    expect(openSpy).toHaveBeenCalledWith('https://docs.example.com/install', '_blank');

    // 更新内容后仅保留一层 .pre-wrapper，不重复嵌套
    html.value = '<pre><code>echo second</code></pre>';
    await vi.waitFor(() => {
      expect(document.querySelectorAll('#resMarkdown .pre-wrapper')).toHaveLength(1);
      document.querySelector<HTMLButtonElement>('#resMarkdown .ag-markdown-view__copy-btn')!.click();
      expect(copiedTexts.at(-1)).toBe('echo second');
    });
  });

  it('AgCopyButton 与 AgStatusDot 渲染与点击复制行为符合预期', async () => {
    const { copiedTexts, spy } = spyCopyCommand();

    const { screen: copyScreen } = await renderWithApp(AgCopyButton, {
      props: { source: 'gw-token-123' },
    });
    copyScreen.container.querySelector<HTMLElement>('.copy-icon')!.click();
    expect(copiedTexts).toEqual(['gw-token-123']);

    spy.mockClear();
    const { screen: emptyCopyScreen } = await renderWithApp(AgCopyButton, { props: {} });
    emptyCopyScreen.container.querySelector<HTMLElement>('.copy-icon')!.click();
    expect(spy).not.toHaveBeenCalled();

    const { screen: okDot } = await renderWithApp(AgStatusDot, {
      props: {
        type: 'success',
        text: '已发布',
      },
    });
    expect(okDot.container.textContent).toContain('已发布');
    expect(okDot.container.innerHTML).toContain('bg-#2caf5e');

    const { screen: errDot } = await renderWithApp(AgStatusDot, {
      props: {
        type: 'error',
        text: '发布失败',
      },
    });
    expect(errDot.container.textContent).toContain('发布失败');
    expect(errDot.container.innerHTML).toContain('bg-#ea3636');
  });
});
