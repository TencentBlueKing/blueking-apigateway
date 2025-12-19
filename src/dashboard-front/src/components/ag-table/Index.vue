/*
 * TencentBlueKing is pleased to support the open source community by making
 * 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
 * Copyright (C) 2025 Tencent. All rights reserved.
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
  <PrimaryTable
    ref="primaryTableRef"
    v-model:selected-row-keys="selectedRowKeys"
    class="primary-table-wrapper"
    :class="[
      {
        'primary-table-no-data': !localTableData.length,
        'primary-table-no-border': !bordered,
        'primary-table-show-pagination': showPagination
      }
    ]"
    :size="tableSetting?.rowSize ?? 'medium'"
    :data="localTableData"
    :columns="tableColumns"
    :pagination="showPagination ? pagination : null"
    :loading="loading"
    :filter-row="null"
    :hover="false"
    :bordered="bordered"
    :table-layout="tableLayout"
    :row-key="tableRowKey"
    :max-height="clientHeight"
    :bk-ui-settings="tableSetting"
    v-bind="$attrs"
    @bk-ui-settings-change="handleSettingChange"
    @row-mouseenter="handleRowEnter"
    @row-mouseleave="handleRowLeave"
    @page-change="handlePageChange"
    @select-change="handleSelectionChange"
  >
    <template #firstFullRow>
      <template v-if="isShowSelectionRow">
        <slot
          v-if="slots.firstFullRow"
          name="firstFullRow"
          v-bind="{
            selections,
            isAllSelection,
            handleSelectionChange
          }"
        />
        <div
          v-if="!slots.firstFullRow"
          class="table-first-full-row"
        >
          <span class="normal-text">
            <span>{{ t('已选') }}</span>
            <span class="count">{{ selections.length }}</span>
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
    <template #loading>
      <BkLoading :loading="loading" />
    </template>
    <template #empty>
      <slot name="empty">
        <TableEmpty
          :error="error"
          :empty-type="tableEmptyType"
          :query-list-params="params"
          @clear-filter="handlerClearFilter"
          @refresh="handleRefresh"
        />
      </slot>
    </template>
  </PrimaryTable>
</template>

<script setup lang="tsx">
import {
  PrimaryTable,
  type PrimaryTableInstance,
  type PrimaryTableProps,
  type TableRowData,
} from '@blueking/tdesign-ui';
import { Checkbox } from 'bkui-vue';
import { useRequest } from 'vue-request';
import { cloneDeep, sortBy, sortedUniq } from 'lodash-es';
import type { BkUiSettings } from '@blueking/tdesign-ui/typings/packages/table/types/table';
import type { ITableMethod } from '@/types/common';
import { useMaxTableLimit, useTDesignSelection, useTableSetting } from '@/hooks';
import i18n from '@/locales';
import router from '@/router';
import TableEmpty from '@/components/table-empty/Index.vue';

interface IProps {
  apiMethod?: (params?: Record<string, any>) => Promise<unknown>
  disabledCheckSelection?: (params?: Record<string, any>) => any
  columns?: PrimaryTableProps['columns']
  tableRowKey?: string
  immediate?: boolean
  localPage?: boolean
  showFirstFullRow?: boolean
  showSelection?: boolean
  showSettings?: boolean
  showPagination?: boolean
  bordered?: string | boolean
  tableLayout?: string
  tableEmptyType?: 'empty' | 'search-empty'
  maxLimitConfig?: Record<string, any> | null
}

const selectedRowKeys = defineModel<any[]>('selectedRowKeys', { default: () => [] });

const tableData = defineModel<any[]>('tableData', { default: () => [] });

const tableSetting = defineModel<null | ShallowRef<BkUiSettings>>('settings', { default: () => null });

const {
  apiMethod = undefined,
  columns = [],
  tableRowKey = 'id',
  // 是否首次加载
  immediate = true,
  // 是否需要本地分页
  localPage = false,
  // 是否显示自定义首行内容
  showFirstFullRow = false,
  // 本地筛选查询状态
  tableEmptyType = 'empty',
  // 是否展示自定义表格复选框
  showSelection = false,
  // 是否展示高级设置
  showSettings = false,
  // 表格布局方式
  tableLayout = 'fixed',
  // 禁止勾选复选框的条件
  disabledCheckSelection = undefined,
  // 表格最大可分页数量配置项
  maxLimitConfig = {},
  // 显示分页组件
  showPagination = true,
  // 展示外边框
  bordered = false,
} = defineProps<IProps>();

const emit = defineEmits<{
  'row-mouseenter': {
    e?: MouseEvent
    row?: TableRowData
  }
  'row-mouseleave': {
    e?: MouseEvent
    row?: TableRowData
  }
  'selection-change': {
    selections: TableRowData
    selectionsRowKeys: string[] | number[]
  }
  'clear-selection': [void]
  'request-done': [void]
  'clear-filter': [void]
  'refresh': [void]
}>();

const { t, locale } = i18n.global;

const slots = useSlots();

const { maxTableLimit, clientHeight } = useMaxTableLimit(maxLimitConfig);

const {
  isAllSelection,
  selections,
  selectionsRowKeys,
  resetSelections,
  handleSelectionChange,
  handleCustomSelectChange,
  handleCustomSelectAllChange,
} = useTDesignSelection();

const disabledSelected = computed(() => {
  return !tableData.value?.length;
});

const TDesignTableRef = useTemplateRef<PrimaryTableInstance & ITableMethod>('primaryTableRef');

let radioClickHandler: ((e: Event) => void) | null = null;
const paramsData: Record<string, any> = ref({});

const radioEl = ref<HTMLElement | null>(null);

// 设置列实例
const settingColumnEl = ref<HTMLElement | null>(null);

const localTableData = ref<any[]>([]);

const pagination = ref<PrimaryTableProps['pagination']>({
  current: 1,
  pageSize: 10,
  total: 0,
  theme: 'default',
  showPageSize: true,
  pageSizeOptions: [10, 20, 50, 100],
});

if (Object.keys(maxLimitConfig)?.length) {
  pagination.value = Object.assign(pagination.value, {
    pageSize: maxTableLimit,
    pageSizeOptions: sortedUniq(sortBy([10, 20, 50, 100, maxTableLimit])),
  });
}

const { changeTableSetting, isDiffSize } = useTableSetting(tableSetting.value);

const isShowSelectionRow = computed(() => {
  return showFirstFullRow && selections.value.length > 0;
});

// 设置表格半选效果
const setIndeterminate = computed(() => {
  const isExistCheck = tableData.value.some(item =>
    item.isCustomCheck || selections.value.map(check => check[tableRowKey]).includes(item[tableRowKey]),
  );
  return isExistCheck && selections.value.length > 0 && !isAllSelection.value;
});

// 这里采用自定义checkbox是为了后续功能扩展，用自带的无法自定义渲染函数(暂时支持跨页选择，不支持跨页全选)
const selectionColumns = computed(() => [{
  colKey: 'row-select',
  type: 'custom-checkbox',
  align: 'center',
  fixed: 'left',
  width: 60,
  title: () => {
    const isDisabled = disabledSelected.value || tableData.value.every(item => disabledCheckSelection?.(item));
    return (
      <Checkbox
        v-model={isAllSelection.value}
        disabled={isDisabled}
        indeterminate={setIndeterminate.value}
        class="custom-ag-table-checkbox"
        onChange={() => {
          if (isDisabled) {
            return;
          }
          tableData.value.forEach((item) => {
            if (!disabledCheckSelection?.(item)) {
              item.isCustomCheck = isAllSelection.value;
            }
          });
          const tables = tableData.value.filter(item => !disabledCheckSelection?.(item));
          handleCustomSelectAllChange({
            isCheck: isAllSelection.value,
            tableRowKey,
            tables,
          });
          emit('selection-change', {
            selectionsRowKeys: selections.value.map(item => item[tableRowKey]),
            selections: selections.value,
          });
        }}
      />
    );
  },
  cell: (h, { row }) => {
    const isDisabled = disabledSelected.value || disabledCheckSelection?.(row);
    row.isCustomCheck = selections.value.map(item => item[tableRowKey]).includes(row[tableRowKey]);
    return (
      <Checkbox
        v-model={row.isCustomCheck}
        v-bk-tooltips={{
          content: row.selectionTip ?? '',
          disabled: typeof disabledCheckSelection === 'undefined' ? true : !disabledCheckSelection?.(row),
        }}
        class="custom-ag-table-checkbox"
        disabled={isDisabled}
        onChange={(isCheck: boolean, e: MouseEvent) => {
          e?.stopPropagation();
          if (isDisabled) {
            return;
          }
          // 这里可以增加disabled逻辑
          handleCustomSelectChange({
            isCheck,
            tableRowKey,
            row,
          });
          const selectionTable = tableData.value.filter(item => !disabledCheckSelection?.(item));
          const checkedIds = selectionsRowKeys.value.filter(id =>
            selectionTable.some(item => item[tableRowKey] === id),
          );
          isAllSelection.value = checkedIds.length > 0 && checkedIds.length === selectionTable.length;
          tableData.value = tableData.value.map((item) => {
            if (!disabledCheckSelection?.(item) && item[tableRowKey] === row[tableRowKey]) {
              return {
                ...item,
                isCustomCheck: isCheck,
              };
            }
            return item;
          });

          emit('selection-change', {
            selectionsRowKeys: checkedIds,
            selections: selections.value,
          });
        }}
      />
    );
  },
}]);

const tableColumns = computed<PrimaryTableProps['columns']>(() => {
  if (showSelection) {
    return [
      ...selectionColumns.value,
      ...columns,
    ];
  }
  return columns;
});

const offsetAndLimit = computed(() => {
  return {
    offset: pagination.value!.pageSize! * (pagination.value!.current! - 1) || 0,
    limit: pagination.value!.pageSize || 10,
  };
});

/**
 * 请求表格数据
 * @param {Object} params 请求数据
 * @param {Boolean} loading 加载状态
 * @param {Object | Null} error 错误信息
 * @param run 手动触发请求的函数
 */
const { params, loading, error, refresh, run } = useRequest(apiMethod, {
  manual: true,
  // 是否立即执行请求
  immediate,
  defaultParams: [offsetAndLimit.value],
  onSuccess: (response: {
    results: any[]
    count: number
  }) => {
    const results = response?.results ?? [];
    paramsData.value = { ...params.value?.[0] };
    pagination.value!.total = response?.count ?? 0;
    tableData.value = [...results];
    getSelectionData();
    // 处理接口调用成功后抛出事件，为每个页面提供单独业务处理
    emit('request-done');
  },
  onError: (error) => {
    tableData.value = [];
    pagination.value.total = 0;
    isAllSelection.value = false;
    getSelectionData();
    console.error(error);
  },
});

watch(tableSetting, () => {
  if (!tableSetting.value && showSettings) {
    tableSetting.value = {
      size: 'medium',
      rowSize: 'medium',
      checked: tableColumns.value?.map(col => col.colKey),
      fields: tableColumns.value.map((col) => {
        return {
          label: col.displayTitle ?? col.title,
          field: col.colKey,
        };
      }),
      // 默认禁用第一项展示文本的表列，不允许取消全部表列
      disabled: [tableColumns.value?.filter(col => !['row-select', 'serial-number'].includes(col.colKey))?.[0]?.colKey],
    };
  }
}, { immediate: true });

watch(tableData, () => {
  localTableData.value = cloneDeep(tableData.value || []);
  if (localPage) {
    pagination.value = Object.assign(pagination.value, {
      current: 1,
      total: localTableData.value.length,
    });
  }
}, {
  immediate: true,
  deep: true,
});

watch([selections, selectedRowKeys], () => {
  emit('selection-change', {
    selectionsRowKeys: selectionsRowKeys.value,
    selections: selections.value,
  });
}, { deep: true });

const fetchData = (
  params: Record<string, any> = {},
  options: { resetPage?: boolean } = { resetPage: false },
) => {
  if (options.resetPage) {
    pagination.value.current = 1;
  }
  run({
    ...params,
    ...offsetAndLimit.value,
  });
};

// 渲染复选框选中数据
const renderSelectionData = (selectList?: any[]) => {
  // 自定义传入勾选数据
  if (selectList) {
    selections.value = selectList;
    selectionsRowKeys.value = selectList.map(item => item[tableRowKey]);
  }
  const checkTableData = selectList || selectionsRowKeys.value;
  if (checkTableData?.length > 0 && tableData.value?.length > 0) {
    const selectionTable = tableData.value.filter(item => !disabledCheckSelection?.(item));
    const checkedIds = tableData.value
      .filter(item => checkTableData.includes(item[tableRowKey]))
      .map(check => check[tableRowKey]);
    isAllSelection.value = checkedIds.length > 0 && checkedIds.length === selectionTable.length;
    tableData.value.forEach((item) => {
      if (!disabledCheckSelection?.(item)) {
        item.isCustomCheck = checkedIds.includes(item[tableRowKey]);
      }
    });
  }
  else {
    isAllSelection.value = false;
  }
};

// 获取回显勾选项数据
const getSelectionData = () => {
  renderSelectionData();
};

// 本地分页设置回显勾选项数据
const setSelectionData = (selectionList: any[]) => {
  renderSelectionData(selectionList);
};

const handleRowEnter = ({ e, row }: {
  e: MouseEvent
  row: TableRowData
}) => {
  emit('row-mouseenter', {
    e,
    row,
  });
};

const handleRowLeave = ({ e, row }: {
  e: MouseEvent
  row: TableRowData
}) => {
  delete row.isOverflow;
  emit('row-mouseleave', {
    e,
    row,
  });
};

const handleCellEnter = ({ e, row }: {
  e: MouseEvent
  row: TableRowData
}) => {
  const cell = (e.target as HTMLElement).closest('.truncate');
  if (cell) {
    row.isOverflow = cell.scrollWidth > cell.clientWidth;
  }
};

const handleCellLeave = ({ row }: { row: TableRowData }) => {
  delete row.isOverflow;
};

const handlePageChange = ({ current, pageSize }: {
  current: number
  pageSize: number
}) => {
  pagination.value = Object.assign(pagination.value, {
    current,
    pageSize,
  });
  if (!localPage) {
    fetchData({
      ...paramsData.value,
      ...offsetAndLimit.value,
    });
  }
};

const handleSettingChange = (setting: BkUiSettings) => {
  const isExistDiff = isDiffSize(setting);
  changeTableSetting(setting);
  tableSetting.value = Object.assign(tableSetting.value, setting ?? {});
  delete tableSetting.value.value;
  if (!isExistDiff) {
    // 这里处理高级设置事件回调后需要处理的业务
    return;
  }
};

// 处理自定义重置功能和点击单选直接关闭弹框
const handleRadioFilterClick = () => {
  setTimeout(() => {
    const filterPopup = document.querySelector('.t-table__filter-pop-content');
    radioEl.value = filterPopup?.querySelector('.t-radio-group');
    if (radioEl.value) {
      const confirmBtn = document.querySelector('.t-table__filter--bottom-buttons > .t-button--theme-primary');
      radioClickHandler = (event: MouseEvent) => {
        const radioLabel = event.target.closest('label.t-radio');
        const radioInput = radioLabel.querySelector('input.t-radio__former');
        if (radioInput.checked) {
          confirmBtn.click();
        }
      };
      radioEl.value.addEventListener('click', radioClickHandler);
    }
  }, 0);
};

// 处理点击设置列触发设置弹框
const handleSettingColumnClick = (e: MouseEvent) => {
  e?.stopPropagation();
  const isIconClick = e.target?.closest('.t-icon-setting');
  if (!isIconClick && settingColumnEl.value) {
    settingColumnEl.value?.querySelector('.column-settings-icon')?.click();
  };
};

const handleListenerRadio = () => {
  const table = unref(TDesignTableRef);
  if (!table) return;

  // 获取表头filter筛选框容器元素
  const filterEl = table.$el.querySelector('.t-table__filter-icon-wrap');
  if (!filterEl) {
    return;
  }
  document.addEventListener('click', handleRadioFilterClick);
};

// 设置列点击
const handleListenerSetting = () => {
  settingColumnEl.value = TDesignTableRef.value?.$el?.querySelector('th[data-colkey="__col_setting__"]');
  settingColumnEl.value?.addEventListener('click', handleSettingColumnClick);
};

const getPagination = () => {
  return pagination.value;
};

const setPagination = ({ current, pageSize }: {
  current: number
  pageSize: number
}) => {
  handlePageChange({
    current,
    pageSize,
  });
};

const setPaginationTheme = ({ theme, showPageSize }: {
  theme: 'default' | 'simple'
  showPageSize?: boolean
}) => {
  Object.assign(pagination.value!, {
    theme,
    showPageSize: showPageSize ?? true,
  });
};

const resetPaginationTheme = () => {
  pagination.value!.theme = 'default';
  pagination.value!.showPageSize = true;
};

const handleResetSelection = () => {
  isAllSelection.value = false;
  localTableData.value.forEach((item) => {
    item.isCustomCheck = false;
  });
  resetSelections();
  selectedRowKeys.value = [];
  emit('clear-selection');
};

// 清空过滤条件
const handlerClearFilter = () => {
  emit('clear-filter');
};

// 异常刷新
const handleRefresh = () => {
  refresh();
  emit('refresh');
};

onMounted(() => {
  if (immediate && !localPage) {
    fetchData({ ...offsetAndLimit.value });
  }
  const tableSet = localStorage.getItem(`table-setting-${locale.value}-${router?.currentRoute?.value?.name}`);
  if (tableSet && tableSetting.value) {
    const storageCache = JSON.parse(tableSet);
    tableSetting.value = {
      ...tableSetting.value,
      ...storageCache,
      size: storageCache.rowSize,
    };
    delete tableSetting.value.value;
  }
  handleListenerRadio();
  handleListenerSetting();
});

onBeforeUnmount(() => {
  document.removeEventListener('click', handleRadioFilterClick);
  radioEl.value?.removeEventListener('click', radioClickHandler);
  settingColumnEl.value?.removeEventListener('click', handleSettingColumnClick);
  radioEl.value = null;
  radioClickHandler = null;
  settingColumnEl.value = null;
});

defineExpose({
  TDesignTableRef,
  loading,
  fetchData,
  getSelectionData,
  getPagination,
  setPagination,
  setSelectionData,
  setPaginationTheme,
  resetPaginationTheme,
  refresh,
  handleResetSelection,
  handleCellEnter,
  handleCellLeave,
});

</script>

<style lang="scss">
.primary-table-wrapper {

  .table-first-full-row {
    width: 100%;
    height: 32px;
    font-size: 12px;
    line-height: 32px;
    text-align: center;
    background-color: #f0f1f5;

    .normal-text {
      color: #4d4f56;

      .count {
        font-weight: 700;
      }
    }

    .hight-light-text {
      color: #3a84ff;
      cursor: pointer;
    }
  }

  .t-table__body {
    color: #63656e;

    .t-table__cell--fixed-left {
      line-height: 1;

      .bk-checkbox {
        vertical-align: middle;
      }
    }
  }

  .t-table__pagination {
    font-size: 12px;

    .t-pagination {
      color: #63656e;

      .t-input--focused {
        box-shadow: none;
      }

      .t-pagination__total {
        font-size: 12px;
      }
    }

    .t-pagination__number.t-is-current {
      font-size: 12px;
      color: #3a84ff;
      background-color: #e1ecff;
      border: none;
    }
  }

  // 默认的 loading 图标

  .t-loading svg.t-icon-loading {
    display: none !important;
  }

  .t-table__row--full.t-table__first-full-row {
    background-color: #f0f1f5;

    td {
      border: none;
    }

    .t-table__row-full-element {
      padding: 0;
    }
  }

  .t-table__row--hover {
    background-color: transparent !important;
  }

  &.primary-table-no-data {

    .t-table__row--full.t-table__first-full-row {
      height: 0;
    }
  }

  &.primary-table-no-border {

    .t-table__header--fixed {
      top: -1px;
    }
  }

  &.primary-table-show-pagination {

    .t-table--scroll-vertical {
      bottom: 64px;
    }
  }
}

.custom-radio-filter-wrapper {

  .t-table__filter--bottom-buttons {

    .t-button:nth-child(2) {
      display: none !important;
    }
  }
}
</style>
