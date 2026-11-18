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
<template>
  <ConfigProvider :global-config="localeConfig">
    <PrimaryTable
      ref="primaryTableRef"
      :key="primaryTableKey"
      :selected-row-keys="selectedRowKeys"
      class="primary-table-wrapper"
      :class="{
        'primary-table-no-data': !renderRows.length,
        'primary-table-no-border': !bordered,
        'primary-table-show-pagination': showPagination && renderRows.length > 0,
        'primary-table-hide-pagination': !showPagination && renderRows.length > 0
      }"
      :data="renderRows"
      :columns="primaryColumns"
      :pagination="showPagination ? pagination : undefined"
      :loading="tableLoading"
      :filter-row="renderEmptyFilterRow"
      :hover="hover"
      :bordered="bordered"
      :table-layout="tableLayout"
      :row-key="rowKeyField"
      :row-class-name="primaryRowClassName"
      :max-height="resolvedMaxHeight"
      :bk-ui-settings="resolvedSettings"
      :resizable="resizable"
      v-bind="$attrs"
      @bk-ui-settings-change="handleSettingsChange"
      @row-mouseenter="handleRowEnter"
      @row-mouseleave="handleRowLeave"
      @row-click="handleRowClick"
      @expand-change="handleExpandChange"
      @filter-change="handleFilterChange"
      @sort-change="handleSortChange"
      @page-change="setPagination"
      @select-change="selection.handleNativeSelectChange"
    >
      <slot />
      <template #firstFullRow>
        <template v-if="showFirstFullRow && selectedRows.length">
          <slot
            v-if="slots.firstFullRow"
            name="firstFullRow"
            v-bind="{
              selections: selectedRows,
              isAllSelection: allSelectableRowsSelected,
              handleSelectionChange: selection.handleNativeSelectChange
            }"
          />
          <div
            v-else
            class="table-first-full-row"
          >
            <span class="normal-text">
              <span>{{ t('已选') }}</span>
              <span class="mx-4px count">{{ selectedRows.length }}</span>
              <span>{{ t('条') }}</span>
              <span class="m-r4px">,</span>
            </span>
            <span
              class="hight-light-text"
              @click="handleResetSelection"
            >
              {{ t('清除选择') }}
            </span>
          </div>
        </template>
      </template>
      <template
        v-if="slots.expandedRow"
        #expandedRow="slotProps"
      >
        <slot
          name="expandedRow"
          v-bind="(slotProps as TableExpandedRowParams<TableRow<TRow>>)"
        />
      </template>
      <template
        v-if="showCellEmptyContent"
        #cellEmptyContent="slotProps"
      >
        <slot
          v-if="slots.cellEmptyContent"
          name="cellEmptyContent"
          v-bind="(slotProps as BaseTableCellParams<TableRow<TRow>>)"
        />
        <!-- 列设置按钮也占一个单元格，只为数据列补占位符。 -->
        <span
          v-else-if="!slotProps?.col?.colKey?.includes('__col_setting__')"
          class="empty-placeholder"
        >--</span>
      </template>
      <template #loading>
        <Loading :loading="tableLoading" />
      </template>
      <template #empty>
        <slot name="empty">
          <AgTableEmpty
            class="py-24px"
            :error="requestError"
            :empty-type="tableEmptyType"
            :no-search-fields="noSearchFields"
            :query-list-params="requestParams"
            @clear-filter="emit('clear-filter')"
            @refresh="handleRefresh"
          />
        </slot>
      </template>
    </PrimaryTable>
  </ConfigProvider>
</template>

<script setup lang="ts" generic="TRow extends TableRowData = TableRowData">
import { ConfigProvider } from 'tdesign-vue-next';
import {
  type BaseTableCellParams,
  type BkUiSettings,
  type ExpandOptions,
  type FilterValue,
  PrimaryTable,
  type PrimaryTableProps,
  type RowEventContext,
  type SortOptions,
  type TableExpandedRowParams,
  type TableFilterChangeContext,
  type TableRowData,
  type TableSort,
} from '@blueking/tdesign-ui';
import { Loading } from 'bkui-vue';
import { t } from '@/locales';
import AgTableEmpty from '@/components/base/ag-table-empty/Index.vue';
import { AG_TABLE_CONTEXT_KEY } from './context';
import { createRowSelectionColumn } from './selection/row-selection-column';
import { useRowSelection } from './selection/use-row-selection';
import {
  getTablePreferenceKeys,
  isTableRowSize,
  readTablePreferences,
  resolveTableRowSize,
} from './settings/table-preferences';
import { useTableSettings } from './settings/use-table-settings';
import type {
  IAgTableEmits,
  IAgTableExpose,
  IAgTableProps,
  IAgTableSlots,
  ITableFilterChangeContext,
  ITableSelection,
  TableRow,
  TableRowSize,
} from './types';
import { useTableDataSource } from './use-table-data-source';
import { useTableLayout } from './use-table-layout';
import {
  clearCellOverflow,
  renderEmptyFilterRow,
  updateCellOverflow,
  useTDesignTableAdapter,
} from './use-tdesign-table-adapter';
import '@blueking/tdesign-ui/vue3/index.css';

defineOptions({ inheritAttrs: false });

const selectedRowKeysModel = defineModel<ITableSelection['selectionsRowKeys']>('selectedRowKeys', { default: () => [] });

const tableData = defineModel<TRow[]>('tableData', { default: () => [] });

const tableSettings = defineModel<BkUiSettings | null>('settings', { default: null });

const {
  apiMethod = undefined,
  columns = [],
  tableRowKey = 'id',
  isExistUniqueKey = true,
  immediate = true,
  localPage = false,
  loading = undefined,
  showPagination = true,
  autoHeight = true,
  maxLimitConfig = null,
  maxHeight = undefined,
  showSelection = false,
  showFirstFullRow = false,
  disabledCheckSelection = () => false,
  showSettings = false,
  hiddenColumn = [],
  uncheckedColumn = [],
  cacheSettingsInLocalStorage = true,
  cacheIdentifier = undefined,
  defaultRowSize = undefined,
  tableLayout = 'fixed',
  bordered = false,
  resizable = true,
  hover = true,
  tableEmptyType = 'empty',
  showCellEmptyContent = false,
  noSearchFields = [],
  rowClassName = undefined,
} = defineProps<IAgTableProps<TRow>>();

const emit = defineEmits<IAgTableEmits<TRow>>();

const slots = defineSlots<IAgTableSlots<TRow>>();

const attrs = useAttrs();
const runtimeContext = inject(AG_TABLE_CONTEXT_KEY, {});

const primaryTableRef = useTemplateRef<InstanceType<typeof PrimaryTable>>('primaryTableRef');
const preferenceKeys = computed(() =>
  getTablePreferenceKeys(
    cacheSettingsInLocalStorage,
    cacheIdentifier,
    maxLimitConfig?.className,
  ));
// 未开启列设置且未传自定义 settings 时不读取缓存，避免子表/弹窗表与主表列设置互相串扰。
const initialPreferences = showSettings || tableSettings.value
  ? readTablePreferences(preferenceKeys.value)
  : {};
// 未显式传 defaultRowSize 时兼容透传给 PrimaryTable 的 size（如子表 size="small"），保证条数反推与实际行高一致。
const defaultSettingsRowSize = computed<TableRowSize>(() => {
  if (isTableRowSize(maxLimitConfig?.defaultRowSize)) return maxLimitConfig.defaultRowSize;
  if (isTableRowSize(defaultRowSize)) return defaultRowSize;
  if (isTableRowSize(attrs.size)) return attrs.size;
  return 'medium';
});
const initialRowSize = resolveTableRowSize(initialPreferences, tableSettings.value, defaultSettingsRowSize.value);

const pageSizeSync: { apply?: (pageSize: number) => void } = {};
// 高度随视口/容器变化动态更新；每页条数仅在首次就绪前估算，用户或翻页接管后不再覆盖。
const {
  initialPageSize,
  resolvedMaxHeight,
  measureInitialPageSize,
} = useTableLayout({
  autoHeight: () => autoHeight,
  maxHeight: () => maxHeight,
  showPagination: () => showPagination,
  rowSize: initialRowSize,
  config: () => maxLimitConfig,
  noticeHeight: () => runtimeContext.getNoticeHeight?.() ?? 0,
  getTableElement: () => primaryTableRef.value?.$el,
  onMeasuredPageSize: pageSize => pageSizeSync.apply?.(pageSize),
});
const {
  renderRows,
  rowKeyField,
  pagination,
  tableLoading,
  requestParams,
  requestError,
  fetchData,
  refresh,
  setPagination,
  setPaginationTheme,
  resetPaginationTheme,
  applyInitialPageSize,
} = useTableDataSource<TRow>({
  sourceRows: tableData,
  apiMethod: () => apiMethod,
  localPage: () => localPage,
  immediate: () => immediate,
  externalLoading: () => loading,
  tableRowKey: () => tableRowKey,
  isExistUniqueKey: () => isExistUniqueKey,
  initialPageSize,
  prepareInitialPageSize: measureInitialPageSize,
  onPageChange: page => emit('page-change', page),
  onRequestDone: () => emit('request-done'),
});
pageSizeSync.apply = applyInitialPageSize;

const selection = useRowSelection<TRow>({
  selectedRowKeysModel,
  rows: () => renderRows.value,
  rowKeyField: () => rowKeyField.value,
  isRowDisabled: row => disabledCheckSelection(row),
  onChange: payload => emit('selection-change', payload),
});
const { selectedRowKeys, selectedRows, allSelectableRowsSelected } = selection;
const selectionColumn = createRowSelectionColumn<TRow>(selection, slots);
const tableColumns = computed(() => showSelection ? [selectionColumn, ...columns] : columns);
// 底层 PrimaryTable 为非泛型组件，在边界处桥接列与行类名类型。
const primaryColumns = computed(() => tableColumns.value as PrimaryTableProps['columns']);
const primaryRowClassName = computed(() => rowClassName as PrimaryTableProps['rowClassName']);

const { settingsEnabled, resolvedSettings, handleSettingsChange } = useTableSettings(tableSettings, {
  showSettings: () => showSettings,
  preferenceKeys,
  initialPreferences,
  columns: () => tableColumns.value,
  hiddenColumnKeys: () => hiddenColumn,
  uncheckedColumnKeys: () => uncheckedColumn,
  defaultRowSize: () => defaultSettingsRowSize.value,
});
// PrimaryTable 仅在挂载时读取一次 rowSize/fontSize，偏好标识变化时重建实例以同步外观配置。
const primaryTableKey = computed(() =>
  settingsEnabled.value ? (preferenceKeys.value.storageKey ?? preferenceKeys.value.identifier) : undefined);

const { localeConfig, handleRowEnter, handleRowLeave } = useTDesignTableAdapter<TRow>({
  getTableElement: () => primaryTableRef.value?.$el,
  onFilterIconClick: () => emit('filter-icon-click'),
  onRowMouseEnter: event => emit('row-mouseenter', event),
  onRowMouseLeave: event => emit('row-mouseleave', event),
});

const handleRowClick = (context: RowEventContext<TableRowData>) => {
  emit('row-click', context as RowEventContext<TableRow<TRow>>);
};
const handleExpandChange = (expandedRowKeys: Array<string | number>, options: ExpandOptions<TableRowData>) => {
  emit('expand-change', expandedRowKeys, options as ExpandOptions<TableRow<TRow>>);
};
const handleFilterChange = (filterValue: FilterValue, context: TableFilterChangeContext<TableRowData>) => {
  emit('filter-change', filterValue, context as unknown as ITableFilterChangeContext<TRow>);
};
const handleSortChange = (sort: TableSort, options: SortOptions<TableRowData>) => {
  emit('sort-change', sort, options as SortOptions<TableRow<TRow>>);
};

const handleResetSelection = () => {
  selection.clearSelection();
  emit('clear-selection');
};
const handleRefresh = () => {
  refresh();
  emit('refresh');
};

defineExpose<IAgTableExpose<TRow>>({
  TDesignTableRef: primaryTableRef,
  loading: tableLoading,
  fetchData,
  refresh,
  getPagination: () => pagination,
  setPagination,
  setPaginationTheme,
  resetPaginationTheme,
  // 历史方法名 getSelectionData 表示按 v-model 的键回显勾选，本身返回 void。
  getSelectionData: selection.syncSelectionFromKeys,
  setSelectionData: selection.replaceSelectedRows,
  handleResetSelection,
  handleCellEnter: updateCellOverflow,
  handleCellLeave: clearCellOverflow,
});
</script>

<style lang="scss" src="./table.scss"></style>
