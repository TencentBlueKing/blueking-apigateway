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
import { afterEach, beforeEach, describe, expect, it } from 'vitest';
import AgTable from '@/components/base/ag-table/Index.vue';
import {
  FIXTURE_ROWS,
  type IFixtureRow,
  type IMountedFixture,
  cleanupFixtures,
  createDefaultColumns,
  findVisible,
  mountIsolated,
  waitUntil,
} from './helpers';

describe('AgTable 行选择、跨页多选与视图数据隔离', () => {
  const fixtures: IMountedFixture[] = [];

  const track = (fixture: IMountedFixture) => {
    fixtures.push(fixture);
    return fixture;
  };

  beforeEach(() => {
    localStorage.clear();
  });

  afterEach(() => {
    try {
      cleanupFixtures(fixtures);
    }
    finally {
      localStorage.clear();
    }
  });

  it('远程分页下支持自定义勾选、跨页保留混合类型 rowKey 与返回恢复勾选态', async () => {
    const tableRef = shallowRef<any>(null);
    const data = ref<IFixtureRow[]>([]);
    const selectedKeys = ref<Array<string | number>>([]);
    const selected = ref<{
      selections: IFixtureRow[]
      selectionsRowKeys: Array<string | number>
    }>({
      selections: [],
      selectionsRowKeys: [],
    });
    let selectionChangeCount = 0;

    const fixture = track(mountIsolated(() => h(AgTable, {
      'ref': tableRef,
      'tableData': data.value,
      'onUpdate:tableData': (val: any) => {
        data.value = val;
      },
      'selectedRowKeys': selectedKeys.value,
      'onUpdate:selectedRowKeys': (val: Array<string | number>) => {
        selectedKeys.value = val;
      },
      'apiMethod': async (params: {
        offset: number
        limit: number
      }) => ({
        count: FIXTURE_ROWS.length,
        results: FIXTURE_ROWS.slice(params.offset, params.offset + params.limit),
      }),
      'immediate': true,
      'showSelection': true,
      'columns': createDefaultColumns(),
      'onSelectionChange': (val: any) => {
        selectionChangeCount += 1;
        selected.value = val;
      },
    })));

    const shows = (text: string) => fixture.container.querySelector('tbody')?.textContent?.includes(text);
    const checkbox = () => fixture.container.querySelector<HTMLInputElement>('tbody input[type=checkbox]');

    await waitUntil(() => shows('First row'), fixture.errors);
    tableRef.value.setPagination({
      current: 1,
      pageSize: 1,
    });
    await waitUntil(() => shows('First row') && !shows('Second row'), fixture.errors);
    expect(checkbox()?.closest('.custom-ag-table-checkbox')).not.toBeNull();

    const beforeClick = selectionChangeCount;
    checkbox()!.click();
    await nextTick();
    await waitUntil(() =>
      selectionChangeCount === beforeClick + 1
      && selectedKeys.value.length === 1
      && selectedKeys.value[0] === 1
      && selected.value.selectionsRowKeys.includes(1), fixture.errors);

    // 切到第二页并勾选字符串 key 行
    tableRef.value.setPagination({
      current: 2,
      pageSize: 1,
    });
    await waitUntil(() => shows('Second row'), fixture.errors);
    checkbox()!.click();
    await waitUntil(() => selected.value.selectionsRowKeys.join() === '1,second', fixture.errors);

    // 切回第一页恢复勾选态，支持 handleResetSelection 清空
    tableRef.value.setPagination({
      current: 1,
      pageSize: 1,
    });
    await waitUntil(() => shows('First row') && Boolean(checkbox()?.checked), fixture.errors);

    tableRef.value.handleResetSelection();
    await waitUntil(() =>
      !selected.value.selections.length && !selected.value.selectionsRowKeys.length, fixture.errors);
    expect(fixture.errors).toEqual([]);
  });

  it('本地分页下支持跨页全选、动态禁用规则、未加载 key 解析与视图数据隔离', async () => {
    const tableRef = shallowRef<any>(null);
    const data = ref<IFixtureRow[]>(FIXTURE_ROWS);
    const selectedKeys = ref<Array<string | number>>([]);
    const selected = ref<{
      selections: IFixtureRow[]
      selectionsRowKeys: Array<string | number>
    }>({
      selections: [],
      selectionsRowKeys: [],
    });
    const disabledRowKeys = ref<Array<string | number>>([]);
    let clickedRow: IFixtureRow | undefined;

    const fixture = track(mountIsolated(() => h(AgTable, {
      'ref': tableRef,
      'tableData': data.value,
      'onUpdate:tableData': (val: any) => {
        data.value = val;
      },
      'selectedRowKeys': selectedKeys.value,
      'onUpdate:selectedRowKeys': (val: Array<string | number>) => {
        selectedKeys.value = val;
      },
      'localPage': true,
      'showSelection': true,
      'columns': createDefaultColumns(),
      'disabledCheckSelection': (row: any) => row.id != null && disabledRowKeys.value.includes(row.id),
      'onRowClick': ({ row }: { row: any }) => {
        clickedRow = row;
      },
      'onSelectionChange': (val: any) => {
        selected.value = val;
      },
    })));

    const shows = (text: string) => fixture.container.querySelector('tbody')?.textContent?.includes(text);
    const headerCheckbox = () =>
      fixture.container.querySelector<HTMLInputElement>('thead .custom-ag-table-checkbox input');

    await waitUntil(() => shows('Second row'), fixture.errors);

    // 1. 本地分页 + 跨页全选
    tableRef.value.setPagination({
      current: 2,
      pageSize: 1,
    });
    await waitUntil(() => shows('Second row') && !shows('First row'), fixture.errors);
    headerCheckbox()!.click();
    await waitUntil(() => selected.value.selectionsRowKeys.join() === '1,second', fixture.errors);
    tableRef.value.handleResetSelection();

    // 2. 动态禁用规则变更后全选立即排除禁用行
    disabledRowKeys.value = ['second'];
    await nextTick();
    headerCheckbox()!.click();
    await waitUntil(() => selected.value.selectionsRowKeys.join() === '1', fixture.errors);

    // 3. 外部注入含未加载 key，后续记录到达时自动解析
    selectedKeys.value = ['second', 'unloaded'];
    await waitUntil(() =>
      selected.value.selectionsRowKeys.join() === 'second,unloaded'
      && selected.value.selections.length === 1, fixture.errors);
    data.value = [
      ...FIXTURE_ROWS,
      {
        id: 'unloaded',
        name: 'New resource',
      },
    ];
    await waitUntil(() =>
      selected.value.selections.map(row => row.name).join() === 'Second row,New resource', fixture.errors);

    // 4. setSelectionData 编程选中并在重载源数据后保留调用方附加的 tool_name 别名
    tableRef.value.setSelectionData([{
      ...FIXTURE_ROWS[0],
      tool_name: 'edited_alias',
    }]);
    await waitUntil(() => selectedKeys.value.join() === '1', fixture.errors);
    data.value = FIXTURE_ROWS.map(row => ({ ...row }));
    await nextTick();
    await waitUntil(() => selected.value.selections[0]?.tool_name === 'edited_alias', fixture.errors);

    // 5. 渲染行编辑与输入源数据隔离（含嵌套对象），父级原地更新仍能反映到视图行
    disabledRowKeys.value = [];
    tableRef.value.handleResetSelection();
    data.value = FIXTURE_ROWS.map(row => ({
      ...row,
      detail: { resources: [row.id!] },
    }));
    await nextTick();
    fixture.container.querySelector<HTMLElement>('tbody .custom-ag-table-checkbox')!.closest('tr')!.click();
    await waitUntil(() => clickedRow?.id === 'second', fixture.errors);
    clickedRow!.isOverflow = true;
    clickedRow!.detail!.resources.push('view only');
    expect(data.value[1].isOverflow).toBeUndefined();
    expect(data.value[1].detail!.resources).toHaveLength(1);

    data.value[1].detail!.resources[0] = 'updated by parent';
    await waitUntil(() =>
      clickedRow!.detail!.resources[0] === 'updated by parent'
      && clickedRow!.detail!.resources.length === 1, fixture.errors);
    expect(fixture.errors).toEqual([]);
  });

  it('缺 key 行禁用不可选，数值 0 作为合法 rowKey 支持全选与 setSelectionData 恢复', async () => {
    const missingKeyRow: IFixtureRow = { name: 'Missing key' };
    const zeroKeyRow: IFixtureRow = {
      id: 0,
      name: 'Zero key',
    };
    const tableRef = shallowRef<any>(null);
    const data = ref<IFixtureRow[]>([missingKeyRow, zeroKeyRow]);
    const selectedKeys = ref<Array<string | number>>([]);
    const selected = ref<{
      selections: IFixtureRow[]
      selectionsRowKeys: Array<string | number>
    }>({
      selections: [],
      selectionsRowKeys: [],
    });

    const fixture = track(mountIsolated(() => h(AgTable, {
      'ref': tableRef,
      'tableData': data.value,
      'onUpdate:tableData': (val: any) => {
        data.value = val;
      },
      'selectedRowKeys': selectedKeys.value,
      'onUpdate:selectedRowKeys': (val: Array<string | number>) => {
        selectedKeys.value = val;
      },
      'localPage': true,
      'showSelection': true,
      'columns': createDefaultColumns(),
      'onSelectionChange': (val: any) => {
        selected.value = val;
      },
    })));

    const shows = (text: string) => fixture.container.querySelector('tbody')?.textContent?.includes(text);
    const checkbox = () => fixture.container.querySelector<HTMLInputElement>('tbody input[type=checkbox]');
    const headerCheckbox = () =>
      fixture.container.querySelector<HTMLInputElement>('thead .custom-ag-table-checkbox input');

    await waitUntil(() => shows('Missing key') && Boolean(checkbox()?.disabled), fixture.errors);
    headerCheckbox()!.click();
    await waitUntil(() => selectedKeys.value.length === 1 && selectedKeys.value[0] === 0, fixture.errors);

    tableRef.value.setSelectionData([missingKeyRow, zeroKeyRow]);
    await waitUntil(() =>
      selected.value.selections.length === 1
      && selectedKeys.value.length === 1
      && selectedKeys.value[0] === 0, fixture.errors);
    expect(fixture.errors).toEqual([]);
  });

  it('常规勾选行在刷新后同步最新行对象并支持别名合并，且缺 key 行不弹出业务禁用提示', async () => {
    const selRows = ref<IFixtureRow[]>([
      {
        id: 1,
        name: 'Old Name',
      },
      { name: 'No Key Row' },
    ]);
    const selState = ref<{
      selections: IFixtureRow[]
      selectionsRowKeys: Array<string | number>
    }>({
      selections: [],
      selectionsRowKeys: [],
    });

    const fixture = track(mountIsolated(() => h(AgTable, {
      tableData: selRows.value,
      localPage: true,
      showSelection: true,
      columns: [{
        colKey: 'name',
        title: 'Name',
      }],
      disabledCheckSelection: (row: Record<string, any>) => row.status === 'locked',
      onSelectionChange: (val: any) => {
        selState.value = val;
      },
    }, {
      selectionPopoverContent: () => 'Business disabled tip',
    })));

    await waitUntil(() =>
      fixture.container.querySelectorAll('tbody .custom-ag-table-checkbox input').length === 2, fixture.errors);
    const inputs = fixture.container.querySelectorAll<HTMLInputElement>('tbody .custom-ag-table-checkbox input');
    inputs[0].click();
    await waitUntil(() => selState.value.selections[0]?.name === 'Old Name', fixture.errors);

    // 刷新源数据后已选行对象同步为最新值
    selRows.value = [
      {
        id: 1,
        name: 'Refreshed Name',
      },
      { name: 'No Key Row' },
    ];
    await waitUntil(() => selState.value.selections[0]?.name === 'Refreshed Name', fixture.errors);

    // 模拟 MCP 工具页：普通勾选后编辑别名，刷新源数据时按 id 合并保留未提交别名并同步最新字段
    selRows.value[0].tool_name = 'edited_alias';
    await waitUntil(() => selState.value.selections[0]?.tool_name === 'edited_alias', fixture.errors);
    const aliasById = new Map(
      selRows.value
        .filter(item => item.id != null && item.tool_name && item.tool_name !== item.name)
        .map(item => [item.id, item.tool_name]),
    );
    selRows.value = [
      {
        id: 1,
        name: 'Latest Server Name',
      },
      { name: 'No Key Row' },
    ].map(item => (aliasById.has(item.id)
      ? {
        ...item,
        tool_name: aliasById.get(item.id),
      }
      : item));
    await waitUntil(() =>
      selState.value.selectionsRowKeys.join() === '1'
      && selState.value.selections[0]?.tool_name === 'edited_alias'
      && selState.value.selections[0]?.name === 'Latest Server Name', fixture.errors);

    // 正反例对照：先验证业务禁用行移入确实会弹出业务禁用提示，再验证缺 key 行移入不弹出该提示
    selRows.value = [
      {
        id: 2,
        name: 'Locked Row',
        status: 'locked',
      },
      { name: 'No Key Row' },
    ];
    await waitUntil(() =>
      fixture.container.querySelector('tbody')?.textContent?.includes('Locked Row'), fixture.errors);

    const checkboxes = fixture.container.querySelectorAll<HTMLElement>('tbody .custom-ag-table-checkbox');
    const lockedTrigger = checkboxes[0].parentElement!;
    lockedTrigger.dispatchEvent(new MouseEvent('mouseenter', { bubbles: true }));
    await waitUntil(() =>
      findVisible('.bk-popover')?.textContent?.includes('Business disabled tip'), fixture.errors);

    lockedTrigger.dispatchEvent(new MouseEvent('mouseleave', { bubbles: true }));
    await waitUntil(() =>
      !findVisible('.bk-popover')?.textContent?.includes('Business disabled tip'), fixture.errors);

    const noKeyTrigger = checkboxes[1].parentElement!;
    noKeyTrigger.dispatchEvent(new MouseEvent('mouseenter', { bubbles: true }));
    // row-selection-column 中 Popover popoverDelay=100ms，等待 250ms 后确认仍无可见业务提示弹层
    await new Promise(resolve => setTimeout(resolve, 250));
    expect(findVisible('.bk-popover')?.textContent ?? '').not.toContain('Business disabled tip');
    expect(fixture.errors).toEqual([]);
  });

  it('原生多选列支持行点击选中、保留外部未加载 key 与全选过滤缺 key 行', async () => {
    const tableRef = shallowRef<any>(null);
    const data = ref<IFixtureRow[]>(FIXTURE_ROWS);
    const selectedKeys = ref<Array<string | number>>([]);
    const selected = ref<{
      selections: IFixtureRow[]
      selectionsRowKeys: Array<string | number>
    }>({
      selections: [],
      selectionsRowKeys: [],
    });

    const fixture = track(mountIsolated(() => h(AgTable, {
      'ref': tableRef,
      'tableData': data.value,
      'onUpdate:tableData': (val: any) => {
        data.value = val;
      },
      'selectedRowKeys': selectedKeys.value,
      'onUpdate:selectedRowKeys': (val: Array<string | number>) => {
        selectedKeys.value = val;
      },
      'localPage': true,
      'showSelection': false,
      'selectOnRowClick': true,
      'columns': [
        {
          colKey: 'row-select',
          type: 'multiple',
        },
        ...createDefaultColumns(),
      ],
      'onSelectionChange': (val: any) => {
        selected.value = val;
      },
    })));

    await waitUntil(() => fixture.container.querySelector('tbody .t-checkbox'), fixture.errors);
    fixture.container.querySelector<HTMLElement>('tbody .t-checkbox')!.closest('tr')!.click();
    await waitUntil(() =>
      selectedKeys.value.includes(1) && selected.value.selectionsRowKeys.includes(1), fixture.errors);

    // 注入外部未加载 key 后再点选其它行，保留未加载 key
    selectedKeys.value = ['unloaded'];
    await waitUntil(() =>
      selected.value.selectionsRowKeys.join() === 'unloaded'
      && selected.value.selections.length === 0, fixture.errors);
    fixture.container.querySelector<HTMLElement>('tbody .t-checkbox')!.closest('tr')!.click();
    await waitUntil(() =>
      selectedKeys.value.join() === 'unloaded,1'
      && selected.value.selections[0]?.id === 1, fixture.errors);

    // 原生全选仅发出具备有效 rowKey 的行
    tableRef.value.handleResetSelection();
    data.value = [{ name: 'Missing native key' }, FIXTURE_ROWS[0]];
    await waitUntil(() =>
      fixture.container.querySelector('tbody')?.textContent?.includes('Missing native key'), fixture.errors);
    fixture.container.querySelector<HTMLInputElement>('thead .t-checkbox input')!.click();
    await waitUntil(() => selectedKeys.value.length === 1 && selectedKeys.value[0] === 1, fixture.errors);
    expect(fixture.errors).toEqual([]);
  });
});
