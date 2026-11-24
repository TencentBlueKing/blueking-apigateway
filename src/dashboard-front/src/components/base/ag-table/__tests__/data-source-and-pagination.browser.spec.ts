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

import { h, nextTick, ref, shallowRef } from 'vue';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import AgTable from '@/components/base/ag-table/Index.vue';
import {
  FIXTURE_ROWS,
  type IFixtureRow,
  type IMountedFixture,
  createDefaultColumns,
  createDeferred,
  mountIsolated,
  waitUntil,
} from './helpers';

describe('AgTable 数据源模式、分页边界与异常重试', () => {
  const fixtures: IMountedFixture[] = [];

  const track = (fixture: IMountedFixture) => {
    fixtures.push(fixture);
    return fixture;
  };

  beforeEach(() => {
    localStorage.clear();
  });

  afterEach(() => {
    while (fixtures.length) {
      fixtures.pop()!.unmount();
    }
    localStorage.clear();
  });

  it('远程搜索去除空筛选条件，在途搜索时翻页保留 query，并支持多页大数据集稳定切换', async () => {
    const tableRef = shallowRef<any>(null);
    const requests: any[] = [];
    let pendingRequest: Promise<void> | undefined;
    let source: IFixtureRow[] = FIXTURE_ROWS;

    const fixture = track(mountIsolated(() => h(AgTable, {
      ref: tableRef,
      columns: createDefaultColumns(),
      immediate: true,
      apiMethod: async (params: any) => {
        requests.push({ ...params });
        if (pendingRequest) {
          const pending = pendingRequest;
          pendingRequest = undefined;
          await pending;
        }
        return {
          count: source.length,
          results: source.slice(params.offset, params.offset + params.limit),
        };
      },
    })));

    const shows = (text: string) => fixture.container.querySelector('tbody')?.textContent?.includes(text);
    await waitUntil(() => shows('First row'), fixture.errors);

    // 搜索去除空字符串参数，且在途请求期间翻页保留 query
    const inFlight = createDeferred<void>();
    pendingRequest = inFlight.promise;
    tableRef.value.fetchData({
      search: 'api',
      unused: '',
    }, { resetPage: true });
    await waitUntil(() =>
      requests.at(-1).search === 'api' && !('unused' in requests.at(-1)), fixture.errors);

    tableRef.value.setPagination({
      current: 1,
      pageSize: 1,
    });
    await waitUntil(() =>
      requests.at(-1).search === 'api' && requests.at(-1).limit === 1, fixture.errors);
    inFlight.resolve();
    await waitUntil(() => shows('First row') && !shows('Second row'), fixture.errors);

    tableRef.value.setPagination({
      current: 2,
      pageSize: 1,
    });
    await waitUntil(() => requests.at(-1).offset === 1 && shows('Second row'), fixture.errors);

    // 300 条带嵌套明细的数据连续翻页渲染
    source = Array.from({ length: 300 }, (_, id) => ({
      id,
      name: `Log entry #${id}#`,
      details: Array.from({ length: 20 }, (_, span) => ({
        span,
        tags: ['gateway', 'upstream'],
        elapsed: span + id,
      })),
    }));
    tableRef.value.fetchData({}, { resetPage: true });
    await waitUntil(() => shows('Log entry #0#'), fixture.errors);

    for (const page of [2, 3, 6, 1]) {
      tableRef.value.setPagination({
        current: page,
        pageSize: 50,
      });
      await waitUntil(() => shows(`Log entry #${(page - 1) * 50}#`), fixture.errors);
    }
    expect(fixture.errors).toEqual([]);
  });

  it('本地分页删除末页记录自动纠正页码，静态模式刷新不发请求并保留注入数据', async () => {
    const tableRef = shallowRef<any>(null);
    const data = ref<IFixtureRow[]>(FIXTURE_ROWS);

    const localFixture = track(mountIsolated(() => h(AgTable, {
      'ref': tableRef,
      'tableData': data.value,
      'onUpdate:tableData': (val: any) => {
        data.value = val;
      },
      'localPage': true,
      'columns': createDefaultColumns(),
    })));

    await waitUntil(() =>
      localFixture.container.querySelector('tbody')?.textContent?.includes('Second row'), localFixture.errors);
    tableRef.value.setPagination({
      current: 2,
      pageSize: 1,
    });
    await waitUntil(() =>
      localFixture.container.querySelector('tbody')?.textContent?.includes('Second row')
      && !localFixture.container.querySelector('tbody')?.textContent?.includes('First row'), localFixture.errors);

    // 移除最后一条后自动回退到第 1 页
    data.value = [FIXTURE_ROWS[0]];
    await waitUntil(() =>
      tableRef.value.getPagination().current === 1
      && tableRef.value.getPagination().total === 1
      && localFixture.container.querySelector('tbody')?.textContent?.includes('First row'), localFixture.errors);
    localFixture.unmount();

    // 静态数据模式下 fetchData / refresh 不覆盖注入数据
    const staticRef = shallowRef<any>(null);
    const staticData = ref<IFixtureRow[]>([FIXTURE_ROWS[0]]);
    const staticFixture = track(mountIsolated(() => h(AgTable, {
      'ref': staticRef,
      'tableData': staticData.value,
      'onUpdate:tableData': (val: any) => {
        staticData.value = val;
      },
      'columns': createDefaultColumns(),
    })));
    await waitUntil(() =>
      staticFixture.container.querySelector('tbody')?.textContent?.includes('First row'), staticFixture.errors);
    staticRef.value.fetchData();
    staticRef.value.refresh();
    await nextTick();
    expect(staticData.value).toHaveLength(1);
    expect(staticFixture.errors).toEqual([]);
  });

  it('远程请求失败支持保留筛选条件重试，切换本地模式后清理错误态与重试按钮', async () => {
    vi.spyOn(console, 'error').mockImplementation(() => undefined);
    const mode = ref<'remote' | 'local'>('remote');
    const data = ref<IFixtureRow[]>([]);
    const tableRef = shallowRef<any>(null);
    const requests: any[] = [];
    let failNextRequest = false;

    const fixture = track(mountIsolated(() => h(AgTable, {
      'ref': tableRef,
      'tableData': data.value,
      'onUpdate:tableData': (val: any) => {
        data.value = val;
      },
      'apiMethod': mode.value === 'remote'
        ? async (params: any) => {
          requests.push({ ...params });
          if (failNextRequest) {
            failNextRequest = false;
            throw new Error('Fixture request failed');
          }
          return {
            count: FIXTURE_ROWS.length,
            results: FIXTURE_ROWS,
          };
        }
        : undefined,
      'localPage': mode.value === 'local',
      'immediate': mode.value === 'remote',
      'columns': createDefaultColumns(),
    })));

    const shows = (text: string) => fixture.container.querySelector('tbody')?.textContent?.includes(text);
    const retryBtn = () => fixture.container.querySelector<HTMLButtonElement>('.api-gateways-exception button');

    await waitUntil(() => shows('Second row'), fixture.errors);

    // 触发失败 -> 展示异常与重试按钮 -> 点击重试沿用 search 条件恢复结果
    failNextRequest = true;
    tableRef.value.fetchData({ search: 'retry-me' });
    await waitUntil(() => tableRef.value.getPagination().total === 0 && Boolean(retryBtn()), fixture.errors);

    retryBtn()!.click();
    await waitUntil(() => requests.at(-1).search === 'retry-me' && shows('First row'), fixture.errors);

    // 远程失败后切换至本地数据源，清空错误态与重试按钮并展示空数据文案
    failNextRequest = true;
    tableRef.value.fetchData({ search: 'remote-only' });
    await waitUntil(() => Boolean(retryBtn()), fixture.errors);

    mode.value = 'local';
    await waitUntil(() =>
      fixture.container.querySelector('.api-gateways-exception')?.textContent?.includes('暂无数据')
      && !retryBtn(), fixture.errors);
    expect(fixture.errors).toEqual([]);
  });

  it('容错处理 null 数据源、非法 selectedRowKeys 与缺少 count 的远程响应', async () => {
    const tableRef = shallowRef<any>(null);
    const nullData = ref<any>(null);
    const badKeys = ref<any>(null);
    const selected = ref<{
      selections: any[]
      selectionsRowKeys: Array<string | number>
    }>({
      selections: [],
      selectionsRowKeys: [],
    });

    const fixture = track(mountIsolated(() => h(AgTable, {
      'ref': tableRef,
      'tableData': nullData.value,
      'onUpdate:tableData': (val: any) => {
        nullData.value = val;
      },
      'selectedRowKeys': badKeys.value,
      'onUpdate:selectedRowKeys': (val: any) => {
        badKeys.value = val;
      },
      'showSelection': true,
      'columns': [{
        colKey: 'name',
        title: 'Name',
      }],
      'apiMethod': async () => [] as any,
      'onSelectionChange': (val: any) => {
        selected.value = val;
      },
    })));

    await waitUntil(() => tableRef.value?.getPagination().total === 0, fixture.errors);

    badKeys.value = [undefined, null, {}, 1, 'valid'];
    await nextTick();
    await waitUntil(() => selected.value.selectionsRowKeys.join() === '1,valid', fixture.errors);
    expect(fixture.errors).toEqual([]);
  });
});
