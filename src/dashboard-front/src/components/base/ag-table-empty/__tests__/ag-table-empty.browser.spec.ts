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

import { describe, expect, it, vi } from 'vitest';
import AgTableEmpty from '@/components/base/ag-table-empty/Index.vue';
import { renderWithApp } from '@/components/__tests__/browser-render';

describe('AgTableEmpty 空态、搜索空态与异常刷新交互', () => {
  it('默认或仅含分页/忽略字段时展示「暂无数据」，不渲染清空条件与刷新按钮', async () => {
    const { screen } = await renderWithApp(AgTableEmpty, {
      props: {
        queryListParams: [{
          offset: 0,
          limit: 10,
          keyword: '',
          stage_id: 1,
        }],
        noSearchFields: ['stage_id'],
      },
    });

    expect(screen.container.textContent).toContain('暂无数据');
    expect(screen.container.querySelector('.search-empty-tips')).toBeNull();
    expect(screen.container.querySelector('button')).toBeNull();
  });

  it('存在有效搜索条件时展示搜索空态，点击触发 clear-filter', async () => {
    const onClearFilter = vi.fn();
    const { screen } = await renderWithApp(AgTableEmpty, {
      props: {
        queryListParams: [{
          offset: 0,
          limit: 10,
          keyword: 'gateway',
        }],
        onClearFilter,
      },
    });

    expect(screen.container.textContent).toContain('搜索结果为空');
    const clearBtn = screen.container.querySelector<HTMLElement>('.search-empty-tips span');
    expect(clearBtn?.textContent).toContain('清空搜索条件');
    clearBtn!.click();
    expect(onClearFilter).toHaveBeenCalledTimes(1);
  });

  it('存在 error 时展示数据获取异常与刷新按钮，点击触发 refresh', async () => {
    const onRefresh = vi.fn();
    const { screen } = await renderWithApp(AgTableEmpty, {
      props: {
        error: { message: '500' },
        onRefresh,
      },
    });

    expect(screen.container.textContent).toContain('数据获取异常');
    const refreshBtn = screen.container.querySelector<HTMLButtonElement>('button');
    expect(refreshBtn?.textContent).toContain('刷新');
    refreshBtn!.click();
    expect(onRefresh).toHaveBeenCalledTimes(1);
  });

  it('无搜索条件和 error 时，支持显式 emptyType（search-empty / searchEmpty / error）驱动对应空态与交互', async () => {
    const onClearSearchEmpty = vi.fn();
    const { screen: searchEmptyScreen } = await renderWithApp(AgTableEmpty, {
      props: {
        emptyType: 'search-empty',
        onClearFilter: onClearSearchEmpty,
      },
    });
    expect(searchEmptyScreen.container.textContent).toContain('搜索结果为空');
    const searchClearBtn = searchEmptyScreen.container.querySelector<HTMLElement>('.search-empty-tips span');
    expect(searchClearBtn?.textContent).toContain('清空搜索条件');
    searchClearBtn!.click();
    expect(onClearSearchEmpty).toHaveBeenCalledTimes(1);

    // 兼容驼峰写法 searchEmpty
    const { screen: camelScreen } = await renderWithApp(AgTableEmpty, {
      props: { emptyType: 'searchEmpty' },
    });
    expect(camelScreen.container.textContent).toContain('搜索结果为空');
    expect(camelScreen.container.querySelector('.search-empty-tips')).not.toBeNull();

    const onRefreshError = vi.fn();
    const { screen: errorScreen } = await renderWithApp(AgTableEmpty, {
      props: {
        emptyType: 'error',
        onRefresh: onRefreshError,
      },
    });
    expect(errorScreen.container.textContent).toContain('数据获取异常');
    const errorRefreshBtn = errorScreen.container.querySelector<HTMLButtonElement>('button');
    expect(errorRefreshBtn?.textContent).toContain('刷新');
    errorRefreshBtn!.click();
    expect(onRefreshError).toHaveBeenCalledTimes(1);
  });
});
