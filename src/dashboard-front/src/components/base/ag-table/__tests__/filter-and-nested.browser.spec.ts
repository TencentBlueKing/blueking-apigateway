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
import { afterEach, beforeEach, describe, expect, it } from 'vitest';
import AgTable from '@/components/base/ag-table/Index.vue';
import {
  FIXTURE_ROWS,
  type IMountedFixture,
  createDefaultColumns,
  findFilterPopup,
  mountIsolated,
  waitUntil,
} from './helpers';

describe('AgTable 单选筛选弹层与嵌套子表隔离', () => {
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

  it('点击单选选项自动确认一次并关闭弹层，再次点击表头图标切换关闭不触发确认', async () => {
    const filterValue = ref<Record<string, any>>({});
    const filters: Record<string, any>[] = [];
    let filterOpenCount = 0;
    let filterConfirmCount = 0;

    const fixture = track(mountIsolated(() => h(AgTable, {
      tableData: FIXTURE_ROWS,
      localPage: true,
      columns: createDefaultColumns(),
      filterValue: filterValue.value,
      onFilterChange: (value: Record<string, any>) => {
        filters.push(value);
        filterValue.value = value;
      },
      onFilterIconClick: () => {
        filterOpenCount += 1;
      },
    })));

    const filterIcon = () => fixture.container.querySelector<HTMLElement>('.t-table__filter-icon');
    await waitUntil(() => filterIcon(), fixture.errors);

    for (const [index, status] of ['on', 'off'].entries()) {
      filterIcon()!.click();
      await waitUntil(() => findFilterPopup()?.querySelector('label.t-radio'), fixture.errors);
      const panel = findFilterPopup()!;
      panel.querySelector<HTMLButtonElement>('button.t-button--theme-primary')!.addEventListener('click', () => {
        filterConfirmCount += 1;
      });
      panel.querySelectorAll<HTMLElement>('label.t-radio .t-radio__label')[index].click();

      await waitUntil(() => filters.at(-1)?.status === status, fixture.errors);
      await waitUntil(() => !findFilterPopup(), fixture.errors);
      expect(filterOpenCount).toBe(index + 1);
      expect(filterConfirmCount).toBe(index + 1);
      expect(filters).toHaveLength(index + 1);
    }

    // 默认筛选结果栏保持隐藏
    expect(fixture.container.querySelector('.t-table__filter-result')).toBeNull();

    // 再次打开并通过表头图标切回关闭，不应触发确认
    filterIcon()!.click();
    await waitUntil(() => findFilterPopup(), fixture.errors);
    filterIcon()!.click();
    await waitUntil(() => !findFilterPopup(), fixture.errors);
    expect(filterOpenCount).toBe(3);
    expect(filterConfirmCount).toBe(2);
    expect(fixture.errors).toEqual([]);
  });

  it('Escape 关闭筛选与兄弟表存在另一弹层后，主表重新打开仍可自动确认单选筛选', async () => {
    const escFilters: Record<string, any>[] = [];
    let escOpenCount = 0;
    const columns = createDefaultColumns();

    const fixture = track(mountIsolated(() => h('div', [
      h(AgTable, {
        class: 'primary-filter-table',
        tableData: FIXTURE_ROWS,
        localPage: true,
        columns,
        onFilterIconClick: () => {
          escOpenCount += 1;
        },
        onFilterChange: (val: Record<string, any>) => {
          escFilters.push(val);
        },
      }),
      h(AgTable, {
        class: 'sibling-filter-table',
        tableData: FIXTURE_ROWS,
        localPage: true,
        columns,
      }),
    ])));

    await waitUntil(() =>
      fixture.container.querySelector('.primary-filter-table .t-table__filter-icon')
      && fixture.container.querySelector('.sibling-filter-table .t-table__filter-icon'), fixture.errors);

    const primaryTrigger = fixture.container.querySelector<HTMLElement>('.primary-filter-table .t-table__filter-icon')!;
    const siblingTrigger = fixture.container.querySelector<HTMLElement>('.sibling-filter-table .t-table__filter-icon')!;

    primaryTrigger.click();
    await waitUntil(() => findFilterPopup()?.querySelector('label.t-radio'), fixture.errors);
    document.dispatchEvent(new KeyboardEvent('keydown', {
      key: 'Escape',
      bubbles: true,
    }));

    siblingTrigger.click();
    await waitUntil(() => findFilterPopup()?.querySelector('label.t-radio'), fixture.errors);

    primaryTrigger.click();
    await waitUntil(() => findFilterPopup()?.querySelector('label.t-radio'), fixture.errors);
    findFilterPopup()!.querySelector<HTMLElement>('label.t-radio .t-radio__label')!.click();

    await waitUntil(() => escFilters.at(-1)?.status === 'on' && escOpenCount >= 2, fixture.errors);
    expect(fixture.errors).toEqual([]);
  });

  it('嵌套展开子表的行选择与单选筛选完全独立，不串扰父表状态', async () => {
    const parentKeys = ref<Array<string | number>>([]);
    const parentFilters: Record<string, any>[] = [];
    const childKeys = ref<Array<string | number>>([]);
    const childFilters: Record<string, any>[] = [];
    const columns = createDefaultColumns();

    const fixture = track(mountIsolated(() => h(AgTable, {
      'tableData': FIXTURE_ROWS,
      'localPage': true,
      'showSelection': true,
      'expandedRowKeys': [1],
      'selectedRowKeys': parentKeys.value,
      'onUpdate:selectedRowKeys': (val: Array<string | number>) => {
        parentKeys.value = val;
      },
      'onFilterChange': (val: Record<string, any>) => {
        parentFilters.push(val);
      },
      columns,
    }, {
      expandedRow: () => h(AgTable, {
        class: 'nested-resources',
        localPage: true,
        showSelection: true,
        columns,
        tableData: FIXTURE_ROWS,
        onFilterChange: (val: Record<string, any>) => {
          childFilters.push(val);
        },
        onSelectionChange: (selection: { selectionsRowKeys: Array<string | number> }) => {
          childKeys.value = selection.selectionsRowKeys;
        },
      }),
    })));

    await waitUntil(() =>
      fixture.container.querySelector('.nested-resources tbody .custom-ag-table-checkbox'), fixture.errors);

    fixture.container.querySelector<HTMLInputElement>('.nested-resources thead .custom-ag-table-checkbox input')!.click();
    await waitUntil(() => childKeys.value.join() === '1,second' && parentKeys.value.length === 0, fixture.errors);

    const parentFilterCount = parentFilters.length;
    fixture.container.querySelector<HTMLElement>('.nested-resources .t-table__filter-icon')!.click();
    await waitUntil(() => findFilterPopup()?.querySelector('label.t-radio'), fixture.errors);
    findFilterPopup()!.querySelector<HTMLElement>('label.t-radio .t-radio__label')!.click();

    await waitUntil(() =>
      childFilters.length === 1
      && childFilters[0].status === 'on'
      && parentFilters.length === parentFilterCount, fixture.errors);
    await waitUntil(() => !findFilterPopup(), fixture.errors);
    expect(fixture.errors).toEqual([]);
  });
});
