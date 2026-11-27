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

import type { PrimaryTableProps, TableRowData } from '@blueking/tdesign-ui';
import type { ITableSelection, TableRow } from '../types';

type RowKey = ITableSelection['selectionsRowKeys'][number];

const isRowKey = (key: unknown): key is RowKey => typeof key === 'string' || typeof key === 'number';

interface IRowSelectionOptions<TRow extends TableRowData = TableRowData> {
  selectedRowKeysModel: Ref<RowKey[]>
  rows: () => TableRow<TRow>[]
  rowKeyField: () => string
  isRowDisabled: (row: TableRow<TRow>) => boolean
  onChange: (selection: ITableSelection<TableRow<TRow>>) => void
}

export const useRowSelection = <TRow extends TableRowData = TableRowData>(
  options: IRowSelectionOptions<TRow>,
) => {
  type SelectedRowsByKey = Map<RowKey, TableRow<TRow> | undefined>;
  const { selectedRowKeysModel } = options;
  // 键的插入顺序就是回传顺序。父页面先传键时保留空位，等对应行加载后补齐。
  const selectedRowsByKey = shallowRef<SelectedRowsByKey>(new Map());
  // 记录通过 setSelectionData 显式注入的行对象，避免源数据重载时覆盖页面附加字段（如工具别名）。
  const pinnedRows = new WeakSet<TableRow<TRow>>();
  const selectedRowKeys = computed(() => [...selectedRowsByKey.value.keys()]);
  const selectedRows = computed<TableRow<TRow>[]>(() =>
    [...selectedRowsByKey.value.values()].filter((row): row is TableRow<TRow> => row !== undefined));
  const getNormalizedModelKeys = () =>
    Array.isArray(selectedRowKeysModel.value) ? selectedRowKeysModel.value.filter(isRowKey) : [];

  const getRowKey = (row: TableRow<TRow>): RowKey | undefined => {
    const key: unknown = row[options.rowKeyField()];
    return isRowKey(key) ? key : undefined;
  };

  const indexRowsByKey = (rows: (TableRow<TRow> | undefined)[]) => {
    const rowsByKey = new Map<RowKey, TableRow<TRow>>();
    for (const row of rows) {
      // TDesign 的 selectedRowData 为尚未加载的选中键保留 undefined。
      if (!row) continue;
      const key = getRowKey(row);
      if (key !== undefined) rowsByKey.set(key, row);
    }
    return rowsByKey;
  };

  // 远程分页只提供当前页，本地分页提供注入的全部行。表头全选作用于这批数据。
  const loadedRowsByKey = computed(() => indexRowsByKey(options.rows()));
  const selectableRowsByKey = computed(() => new Map(
    [...loadedRowsByKey.value].filter(([, row]) => !options.isRowDisabled(row)),
  ));
  const checkedSelectableCount = computed(() =>
    [...selectableRowsByKey.value.keys()].filter(key => selectedRowsByKey.value.has(key)).length);
  const hasSelectableRows = computed(() => selectableRowsByKey.value.size > 0);
  const allSelectableRowsSelected = computed(() => hasSelectableRows.value
    && checkedSelectableCount.value === selectableRowsByKey.value.size);
  const isPartiallySelected = computed(() => checkedSelectableCount.value > 0 && !allSelectableRowsSelected.value);

  const updateSelection = (nextSelection: SelectedRowsByKey, { updateKeyModel = true } = {}) => {
    const nextKeys = [...nextSelection.keys()];
    const sameKeys = nextKeys.length === selectedRowKeys.value.length
      && nextKeys.every((key, index) => key === selectedRowKeys.value[index]);
    if (sameKeys && nextKeys.every(key => nextSelection.get(key) === selectedRowsByKey.value.get(key))) return;

    selectedRowsByKey.value = nextSelection;
    if (updateKeyModel && !sameKeys) selectedRowKeysModel.value = nextKeys;
    options.onChange({
      selections: selectedRows.value,
      selectionsRowKeys: nextKeys,
    });
  };

  const syncSelectionFromKeys = () => {
    const resolvedSelection: SelectedRowsByKey = new Map();
    for (const key of getNormalizedModelKeys()) {
      const existingRow = selectedRowsByKey.value.get(key);
      const loadedRow = loadedRowsByKey.value.get(key);
      // 显式通过 setSelectionData 注入的行保留原对象，常规勾选与按 key 匹配的行在刷新后同步为最新行数据。
      const resolvedRow = existingRow && pinnedRows.has(existingRow)
        ? existingRow
        : (loadedRow ?? existingRow);
      resolvedSelection.set(key, resolvedRow);
    }
    updateSelection(resolvedSelection, { updateKeyModel: false });
  };
  watch(
    [
      getNormalizedModelKeys,
      () => (getNormalizedModelKeys().length ? loadedRowsByKey.value : undefined),
    ],
    syncSelectionFromKeys,
    { immediate: true },
  );

  const setRowSelected = (row: TableRow<TRow>, checked: boolean) => {
    const key = getRowKey(row);
    if (key === undefined || options.isRowDisabled(row)) return;
    const nextSelection = new Map(selectedRowsByKey.value);
    if (checked) nextSelection.set(key, row);
    else nextSelection.delete(key);
    updateSelection(nextSelection);
  };

  const setAllRowsSelected = (checked: boolean) => {
    const nextSelection = new Map(selectedRowsByKey.value);
    for (const [key, row] of selectableRowsByKey.value) {
      if (checked) nextSelection.set(key, row);
      else nextSelection.delete(key);
    }
    updateSelection(nextSelection);
  };

  const handleNativeSelectChange: NonNullable<PrimaryTableProps['onSelectChange']> = (rowKeys, { selectedRowData }) => {
    const nativeRowsByKey = indexRowsByKey(selectedRowData as (TableRow<TRow> | undefined)[]);
    const nextSelection: SelectedRowsByKey = new Map();
    for (const key of rowKeys) {
      if (!isRowKey(key)) continue;
      const row = nativeRowsByKey.get(key) ?? selectedRowsByKey.value.get(key) ?? loadedRowsByKey.value.get(key);
      nextSelection.set(key, row);
    }
    updateSelection(nextSelection);
  };

  const replaceSelectedRows = (rows: TRow[]) => {
    const nextSelection = indexRowsByKey(Array.isArray(rows) ? (rows as TableRow<TRow>[]) : []);
    for (const row of nextSelection.values()) {
      pinnedRows.add(row);
    }
    updateSelection(nextSelection);
  };

  return {
    selectedRowKeys,
    selectedRows,
    allSelectableRowsSelected,
    isPartiallySelected,
    hasSelectableRows,
    isRowBusinessDisabled: (row: TableRow<TRow>) => options.isRowDisabled(row),
    isRowDisabled: (row: TableRow<TRow>) => getRowKey(row) === undefined || options.isRowDisabled(row),
    isRowSelected: (row: TableRow<TRow>) => {
      const key = getRowKey(row);
      return key !== undefined && selectedRowsByKey.value.has(key);
    },
    setRowSelected,
    setAllRowsSelected,
    replaceSelectedRows,
    clearSelection: () => updateSelection(new Map()),
    syncSelectionFromKeys,
    handleNativeSelectChange,
  };
};
