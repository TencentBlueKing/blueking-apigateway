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

import { ref, shallowRef } from 'vue';
import { describe, expect, it, vi } from 'vitest';
import type { ISearchItem, ISearchValue } from 'bkui-vue/lib/search-select/utils';
import { useSelection } from '@/hooks/use-selection-data';
import { useTableFilterChange } from '@/hooks/use-table-filter-change';
import { useTableSortChange } from '@/hooks/use-table-sort-change';

describe('hooks/use-table-filter-change', () => {
  const createOptions = () => ref<ISearchItem[]>([
    {
      id: 'method',
      name: '请求方法',
      children: [
        {
          id: 'GET',
          name: 'GET',
        },
        {
          id: 'POST',
          name: 'POST',
        },
      ],
    },
    {
      id: 'status',
      name: '状态',
      children: [
        {
          id: 'active',
          name: '启用',
        },
        {
          id: 'inactive',
          name: '停用',
        },
      ],
    },
  ]);

  it('单选与多选筛选联动更新 filterData 与 searchParams，并在置空时清理对应条件', () => {
    const { handleTableFilterChange } = useTableFilterChange();
    const filterData = ref<Record<string, string | string[]>>({});
    const searchOptions = createOptions();
    const searchParams = ref<ISearchValue[]>([]);

    // 单选新增
    handleTableFilterChange({
      filterItem: { status: 'active' },
      filterData,
      searchOptions,
      searchParams,
    });
    expect(filterData.value).toEqual({ status: 'active' });
    expect(searchParams.value).toEqual([
      {
        id: 'status',
        name: '状态',
        values: [{
          id: 'active',
          name: '启用',
        }],
      },
    ]);

    // 多选新增 + 单选原地更新
    handleTableFilterChange({
      filterItem: {
        status: 'inactive',
        method: ['GET', 'POST'],
      },
      filterData,
      searchOptions,
      searchParams,
    });
    expect(filterData.value).toEqual({
      status: 'inactive',
      method: ['GET', 'POST'],
    });
    expect(searchParams.value).toHaveLength(2);
    expect(searchParams.value[0].values).toEqual([{
      id: 'inactive',
      name: '停用',
    }]);
    expect(searchParams.value[1].values).toHaveLength(2);

    // 置空单选与多选数组
    handleTableFilterChange({
      filterItem: {
        status: '',
        method: [],
      },
      filterData,
      searchOptions,
      searchParams,
    });
    expect(filterData.value).toEqual({});
    expect(searchParams.value).toEqual([]);
  });
});

describe('hooks/use-table-sort-change', () => {
  it('仅对白名单字段写入 order_by，取消排序时清理 order_by 与 sortData', () => {
    const { handleTableSortChange } = useTableSortChange();
    const filterData = ref<Record<string, any>>({ keyword: 'api' });
    const sortData = ref<Record<string, any>>({});
    const allowSortField = shallowRef(['name', 'updated_time']);

    handleTableSortChange({
      orderBy: {
        sortBy: 'updated_time',
        descending: true,
      },
      filterData,
      sortData,
      allowSortField,
    });
    expect(filterData.value.order_by).toBe('updated_time:desc');
    expect(sortData.value).toEqual({
      sortBy: 'updated_time',
      descending: true,
    });

    handleTableSortChange({
      orderBy: {
        sortBy: 'name',
        descending: false,
      },
      filterData,
      sortData,
      allowSortField,
    });
    expect(filterData.value.order_by).toBe('name:asc');

    // 不在白名单的字段不改写 order_by
    handleTableSortChange({
      orderBy: {
        sortBy: 'not_allowed',
        descending: true,
      },
      filterData,
      sortData,
      allowSortField,
    });
    expect(filterData.value.order_by).toBe('name:asc');

    // 取消排序
    handleTableSortChange({
      orderBy: undefined as any,
      filterData,
      sortData,
      allowSortField,
    });
    expect('order_by' in filterData.value).toBe(false);
    expect(sortData.value).toEqual({});
  });
});

describe('hooks/use-selection-data', () => {
  it('支持单选增删、按规则过滤全选并深拷贝，以及重置清空表格选择', () => {
    const rows = [
      {
        id: 1,
        name: 'r1',
        disabled: false,
      },
      {
        id: 2,
        name: 'r2',
        disabled: true,
      },
      {
        id: 3,
        name: 'r3',
        disabled: false,
      },
    ];
    const {
      selections,
      handleSelectionChange,
      handleSelectAllChange,
      resetSelections,
    } = useSelection({ isRowSelectEnable: row => !row.disabled });

    handleSelectionChange({
      checked: true,
      data: rows,
      row: rows[0],
    });
    handleSelectionChange({
      checked: true,
      data: rows,
      row: rows[2],
    });
    expect(selections.value.map(item => item.id)).toEqual([1, 3]);

    handleSelectionChange({
      checked: false,
      data: rows,
      row: rows[0],
    });
    expect(selections.value.map(item => item.id)).toEqual([3]);

    // 全选过滤掉不可选行，且深拷贝隔离原行对象
    handleSelectAllChange({
      checked: true,
      data: rows,
    });
    expect(selections.value.map(item => item.id)).toEqual([1, 3]);
    selections.value[0].name = 'mutated';
    expect(rows[0].name).toBe('r1');

    // 取消全选
    handleSelectAllChange({
      checked: false,
      data: rows,
    });
    expect(selections.value).toEqual([]);

    // 重置并联动表格实例 clearSelection
    handleSelectAllChange({
      checked: true,
      data: rows,
    });
    const clearSelection = vi.fn();
    resetSelections({ clearSelection });
    expect(selections.value).toEqual([]);
    expect(clearSelection).toHaveBeenCalledTimes(1);
  });
});
