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
      :columns="tableColumns"
      :pagination="showPagination ? pagination : undefined"
      :loading="tableLoading"
      :filter-row="renderEmptyFilterRow"
      :hover="hover"
      :bordered="bordered"
      :table-layout="tableLayout"
      :row-key="rowKeyField"
      :max-height="maxHeight || availableHeight"
      :bk-ui-settings="resolvedSettings"
      :resizable="resizable"
      v-bind="$attrs"
      @bk-ui-settings-change="handleSettingsChange"
      @row-mouseenter="handleRowEnter"
      @row-mouseleave="handleRowLeave"
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
          v-bind="slotProps"
        />
      </template>
      <template
        v-if="showCellEmptyContent"
        #cellEmptyContent="slotProps"
      >
        <slot
          v-if="slots.cellEmptyContent"
          name="cellEmptyContent"
          v-bind="slotProps"
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

<script setup lang="ts">
import { ConfigProvider } from 'tdesign-vue-next';
import { type BkUiSettings, PrimaryTable, type TableRowData } from '@blueking/tdesign-ui';
import { Loading } from 'bkui-vue';
import type { ITableSelection } from '@/types/common';
import { t } from '@/locales';
import AgTableEmpty from '@/components/base/ag-table-empty/Index.vue';
import { AG_TABLE_CONTEXT_KEY } from './context';
import { calculateInitialTableLayout } from './initial-table-layout';
import { createRowSelectionColumn } from './selection/row-selection-column';
import { useRowSelection } from './selection/use-row-selection';
import {
  getTablePreferenceKeys,
  isTableRowSize,
  readTablePreferences,
  resolveTableRowSize,
} from './settings/table-preferences';
import { useTableSettings } from './settings/use-table-settings';
import type { IAgTableEmits, IAgTableProps } from './types';
import { useTableDataSource } from './use-table-data-source';
import {
  clearCellOverflow,
  renderEmptyFilterRow,
  updateCellOverflow,
  useTDesignTableAdapter,
} from './use-tdesign-table-adapter';
import '@blueking/tdesign-ui/vue3/index.css';

defineOptions({ inheritAttrs: false });

const selectedRowKeysModel = defineModel<ITableSelection['selectionsRowKeys']>('selectedRowKeys', { default: () => [] });

const tableData = defineModel<TableRowData[]>('tableData', { default: () => [] });

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
  defaultRowSize = 'medium',
  tableLayout = 'fixed',
  bordered = false,
  resizable = true,
  hover = true,
  tableEmptyType = 'empty',
  showCellEmptyContent = false,
  noSearchFields = [],
} = defineProps<IAgTableProps>();

const emit = defineEmits<IAgTableEmits>();

const slots = useSlots();
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
const defaultSettingsRowSize = computed(() =>
  isTableRowSize(maxLimitConfig?.defaultRowSize) ? maxLimitConfig.defaultRowSize : defaultRowSize);

// 每页条数只在挂载时估算。之后由分页器管理，编辑行高或调整窗口不会覆盖用户选定的条数。
const { availableHeight, initialPageSize } = calculateInitialTableLayout({
  viewportHeight: window.innerHeight,
  noticeHeight: runtimeContext.getNoticeHeight?.() ?? 0,
  rowSize: resolveTableRowSize(initialPreferences, tableSettings.value, defaultSettingsRowSize.value),
  config: maxLimitConfig,
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
} = useTableDataSource({
  sourceRows: tableData,
  apiMethod: () => apiMethod,
  localPage: () => localPage,
  immediate: () => immediate,
  externalLoading: () => loading,
  tableRowKey: () => tableRowKey,
  isExistUniqueKey: () => isExistUniqueKey,
  initialPageSize,
  onPageChange: page => emit('page-change', page),
  onRequestDone: () => emit('request-done'),
});

const selection = useRowSelection({
  selectedRowKeysModel,
  rows: () => renderRows.value,
  rowKeyField: () => rowKeyField.value,
  isRowDisabled: row => disabledCheckSelection(row),
  onChange: payload => emit('selection-change', payload),
});
const { selectedRowKeys, selectedRows, allSelectableRowsSelected } = selection;
const selectionColumn = createRowSelectionColumn(selection, slots);
const tableColumns = computed(() => showSelection ? [selectionColumn, ...columns] : columns);
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

const { localeConfig, handleRowEnter, handleRowLeave } = useTDesignTableAdapter({
  getTableElement: () => primaryTableRef.value?.$el,
  onFilterIconClick: () => emit('filter-icon-click'),
  onRowMouseEnter: event => emit('row-mouseenter', event),
  onRowMouseLeave: event => emit('row-mouseleave', event),
});
const handleResetSelection = () => {
  selection.clearSelection();
  emit('clear-selection');
};
const handleRefresh = () => {
  refresh();
  emit('refresh');
};

defineExpose({
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
