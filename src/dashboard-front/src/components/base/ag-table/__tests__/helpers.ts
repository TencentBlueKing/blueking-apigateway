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

import { type Component, type VNode, createApp, defineComponent, h } from 'vue';
import { Button, Exception } from 'bkui-vue';
import { expect, vi } from 'vitest';
import { AG_TABLE_CONTEXT_KEY, type IAgTableRuntimeContext } from '@/components/base/ag-table/context';

export interface IFixtureRow {
  id?: number | string
  name: string
  status?: string
  optional?: string
  tool_name?: string
  isOverflow?: boolean
  detail?: { resources: Array<number | string> }
  details?: Array<{
    span: number
    tags: string[]
    elapsed: number
  }>
}

export const DEFAULT_TABLE_CONTEXT: IAgTableRuntimeContext = {
  getNoticeHeight: () => 0,
};

export const FIXTURE_ROWS: IFixtureRow[] = [
  {
    id: 1,
    name: 'First row',
    status: 'on',
    optional: 'A',
  },
  {
    id: 'second',
    name: 'Second row',
    status: 'off',
    optional: 'B',
  },
];

export const createDefaultColumns = () => [
  {
    colKey: 'name',
    displayTitle: 'Name setting',
    title: () => h('span', 'Name header'),
  },
  {
    colKey: 'status',
    title: 'Status',
    className: 'need-filter-icon-handler',
    filter: {
      type: 'single' as const,
      showConfirmAndReset: true,
      list: [
        {
          label: 'Enabled',
          value: 'on',
        },
        {
          label: 'Disabled',
          value: 'off',
        },
      ],
    },
  },
  {
    colKey: 'optional',
    title: 'Optional',
  },
];

export interface IMountedFixture {
  container: HTMLDivElement
  errors: string[]
  unmount: () => void
}

/**
 * 在真实浏览器 DOM 中挂载隔离的 Vue 测试宿主，并自动捕获 Vue / 全局异常
 */
export function mountIsolated(
  renderRoot: () => VNode,
  runtimeContext: IAgTableRuntimeContext = DEFAULT_TABLE_CONTEXT,
): IMountedFixture {
  const container = document.body.appendChild(document.createElement('div'));
  const errors: string[] = [];

  const onWindowError = (event: ErrorEvent) => {
    errors.push(event.message);
  };
  const onUnhandledRejection = (event: PromiseRejectionEvent) => {
    errors.push(String(event.reason));
  };
  window.addEventListener('error', onWindowError);
  window.addEventListener('unhandledrejection', onUnhandledRejection);

  const Root: Component = defineComponent({
    setup: () => renderRoot,
  });

  const app = createApp(Root);
  app.provide(AG_TABLE_CONTEXT_KEY, runtimeContext);
  app.component('BkException', Exception);
  app.component('BkButton', Button);
  app.config.errorHandler = (error: unknown) => {
    errors.push(error instanceof Error ? (error.stack || error.message) : String(error));
  };
  app.mount(container);

  let unmounted = false;
  return {
    container,
    errors,
    unmount: () => {
      if (unmounted) {
        return;
      }
      unmounted = true;
      window.removeEventListener('error', onWindowError);
      window.removeEventListener('unhandledrejection', onUnhandledRejection);
      app.unmount();
      container.remove();
    },
  };
}

/** 查找当前在页面中可见的匹配元素（过滤隐藏的 TDesign Popup） */
export const findVisible = <T extends HTMLElement = HTMLElement>(
  selector: string,
  root: ParentNode = document,
): T | undefined => {
  return [...root.querySelectorAll<T>(selector)].find(el =>
    el.getClientRects().length > 0
    && getComputedStyle(el).visibility !== 'hidden'
    && !el.closest('.t-popup--hidden'));
};

export const findFilterPopup = () => findVisible('.t-table__filter-pop-content');

/** 轮询等待异步渲染条件成立，期间若有未捕获错误立即失败 */
export async function waitUntil(
  predicate: () => unknown,
  errors?: string[],
  label = 'Expected condition to become truthy',
  timeout = 5000,
) {
  await vi.waitFor(() => {
    if (errors?.length) {
      throw new Error(`${label}\n${errors.join('\n')}`);
    }
    expect(Boolean(predicate()), label).toBe(true);
  }, {
    timeout,
    interval: 16,
  });
}

/** 计算真实 DOM 中 .t-table 的预期自适应内容区最大高度 */
export function getExpectedDomMaxHeight(root: ParentNode): number {
  const tableEl = root.querySelector<HTMLElement>('.t-table')!;
  const top = tableEl.getBoundingClientRect().top;
  const style = getComputedStyle(tableEl);
  const borderHeight = (parseFloat(style.borderTopWidth) || 0) + (parseFloat(style.borderBottomWidth) || 0);
  return Math.max(200, Math.floor(window.innerHeight - top - 24 - 64 - borderHeight));
}

export const createDeferred = <T = void>() => {
  let resolve!: (value: T) => void;
  let reject!: (reason?: unknown) => void;
  const promise = new Promise<T>((res, rej) => {
    resolve = res;
    reject = rej;
  });
  return {
    promise,
    resolve,
    reject,
  };
};
