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
      :key="tableKey"
      v-model:selected-row-keys="selectedRowKeys"
      class="primary-table-wrapper"
      :class="[
        {
          'primary-table-no-data': !localTableData.length,
          'primary-table-no-border': !bordered,
          'primary-table-show-pagination': showPagination && localTableData.length > 0,
          'primary-table-hide-pagination': !showPagination && localTableData.length > 0
        }
      ]"
      :size="tableSettingSize"
      :data="localTableData"
      :columns="tableColumns"
      :pagination="showPagination ? pagination : null"
      :loading="tableLoading"
      :filter-row="null"
      :hover="hover"
      :bordered="bordered"
      :table-layout="tableLayout"
      :row-key="isExistUniqueKey ? tableRowKey : 'tempUniqueId'"
      :max-height="maxHeight || clientHeight"
      :bk-ui-settings="innerTableSettings"
      :resizable="resizable"
      v-bind="$attrs"
      @bk-ui-settings-change="handleSettingChange"
      @row-mouseenter="handleRowEnter"
      @row-mouseleave="handleRowLeave"
      @page-change="handlePageChange"
      @select-change="handleSelectionChange"
    >
      <slot />
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
              <span class="mx-4px count">{{ selections.length }}</span>
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
      <!-- 如果showCellEmptyContent开启，接受自定义空内容插槽内容和默认值 -->
      <template
        v-if="showCellEmptyContent"
        #cellEmptyContent="slotProps"
      >
        <template v-if="slots.cellEmptyContent">
          <slot
            name="cellEmptyContent"
            v-bind="slotProps"
          />
        </template>
        <!-- 这里需要处理下设置列会出现空占位符 -->
        <template v-if="!slotProps?.col?.colKey.includes('__col_setting__') && !slots.cellEmptyContent">
          <span class="empty-placeholder">--</span>
        </template>
      </template>
      <template #loading>
        <Loading :loading="tableLoading" />
      </template>
      <template #empty>
        <slot name="empty">
          <TableEmpty
            class="py-24px"
            :error="error"
            :empty-type="tableEmptyType"
            :no-search-fields="noSearchFields"
            :query-list-params="requestParams"
            @clear-filter="handlerClearFilter"
            @refresh="handleRefresh"
          />
        </slot>
      </template>
    </PrimaryTable>
  </ConfigProvider>
</template>

<script setup lang="tsx">
// @ts-nocheck
import {
  cloneDeep,
  isEqual,
  isPlainObject,
  memoize,
  some,
  sortBy,
  sortedUniq,
  throttle,
  uniq,
} from 'lodash-es';
import {
  type BkUiSettings,
  PrimaryTable,
  type PrimaryTableProps,
  type TableRowData,
} from '@blueking/tdesign-ui';
import { ConfigProvider } from 'tdesign-vue-next';
import cnConfig from 'tdesign-vue-next/es/locale/zh_CN';
import enConfig from 'tdesign-vue-next/es/locale/en_US';
import { Checkbox, Loading, Popover } from 'bkui-vue';
import { useRequest } from 'vue-request';
import type { ITableMethod, ITableSettings } from '@/types/common';
import { filterSimpleEmpty } from '@/utils/filterEmptyValues';
import { useMaxTableLimit, useTDesignSelection, useTableSetting } from '@/hooks';
import i18n from '@/locales';
import TableEmpty from '@/components/table-empty/Index.vue';
// tdesign 表格样式
import '@blueking/tdesign-ui/vue3/index.css';

interface IProps {
  apiMethod?: (params?: any) => Promise<unknown>
  disabledCheckSelection?: (row: TableRowData) => boolean
  columns?: PrimaryTableProps['columns']
  tableRowKey?: string
  immediate?: boolean
  localPage?: boolean
  // 外部传入的加载态，不传时本地分页模式下由组件内部在数据更新时自动展示 loading
  loading?: boolean
  showFirstFullRow?: boolean
  showSelection?: boolean
  showSettings?: boolean
  showPagination?: boolean
  isExistUniqueKey?: boolean
  bordered?: string | boolean
  tableLayout?: string
  tableEmptyType?: 'empty' | 'search-empty' | 'searchEmpty' | 'error'
  maxLimitConfig?: Record<string, any> | null
  hiddenColumn?: string[]
  noSearchFields?: string[]
  resizable?: boolean
  showCellEmptyContent?: boolean
  maxHeight?: string | number | undefined
  cacheSettingsInLocalStorage?: boolean
  cacheIdentifier?: string
  hover?: boolean
}

const selectedRowKeys = defineModel<any[]>('selectedRowKeys', { default: () => [] });

const tableData = defineModel<any[]>('tableData', { default: () => [] });

const tableSettings = defineModel<BkUiSettings | null>('settings', { default: () => null });

const {
  apiMethod = undefined,
  columns = [],
  tableRowKey = 'id',
  // 是否首次加载
  immediate = true,
  // 是否需要本地分页
  localPage = false,
  // 外部传入的加载态，不传时本地分页模式下由组件内部在数据更新时自动展示 loading
  loading = undefined,
  // 是否显示自定义首行内容
  showFirstFullRow = false,
  // 自定义处理筛选查询状态
  tableEmptyType = 'empty',
  // 是否展示自定义表格复选框
  showSelection = false,
  // 是否展示高级设置
  showSettings = false,
  // 表格布局方式
  tableLayout = 'fixed',
  // 禁止勾选复选框的条件
  disabledCheckSelection = () => false,
  // 表格最大可分页数量配置项
  maxLimitConfig = {},
  // 显示分页组件
  showPagination = true,
  // 展示外边框
  bordered = false,
  // 表格是否存在唯一标识
  isExistUniqueKey = true,
  // 默认不显示的表格列
  hiddenColumn = [],
  // 不需要处理成搜索状态的字段
  noSearchFields = [],
  // 默认tableFixed启用resizable
  resizable = true,
  // 存在列空值时，是否展示默认空内容或自定义空内容
  showCellEmptyContent = false,
  // 父组件限制最大表格高度
  maxHeight = undefined,
  // 是否缓存表格设置到 LocalStorage，默认开启
  cacheSettingsInLocalStorage = true,
  // 表格设置缓存唯一标识符，注意不是 LocalStorage 的 key，而是用于区分不同表格的标识符，不传的话会自动生成一个
  cacheIdentifier = undefined,
  // 是否鼠标hover每行出现底色
  hover = true,
} = defineProps<IProps>();

const emit = defineEmits<{
  'row-mouseenter': [payload: {
    e?: MouseEvent
    row?: TableRowData
  }]
  'row-mouseleave': [payload: {
    e?: MouseEvent
    row?: TableRowData
  }]
  'selection-change': [payload: {
    selections: TableRowData[]
    selectionsRowKeys: string[] | number[]
  }]
  'page-change': [payload: {
    current: number
    pageSize: number
  }]
  'filter-icon-click': [void]
  'clear-selection': [void]
  'clear-filter': [void]
  'request-done': [void]
  'refresh': [void]
}>();

const { t, locale } = i18n.global;

const slots = useSlots();

// 行高缓存的读取与 use-table-setting 的写入必须用同一个标识，
// 因此表格自定义了 cacheIdentifier 时要一并传给 useMaxTableLimit
const { maxTableLimit, clientHeight } = useMaxTableLimit({
  ...(maxLimitConfig ?? {}),
  className: maxLimitConfig?.className ?? cacheIdentifier,
});

const {
  localStorageKey,
  changeTableSettings,
  updateCacheIdentifier,
} = useTableSetting(tableSettings, cacheSettingsInLocalStorage, cacheIdentifier);

const {
  selections,
  selectionsRowKeys,
  resetSelections,
  handleSelectionChange,
  handleCustomSelectChange,
  handleCustomSelectAllChange,
} = useTDesignSelection();

const TDesignTableRef = useTemplateRef<InstanceType<typeof PrimaryTable> & ITableMethod>('primaryTableRef');

// 本地分页场景下数据由外部异步注入，组件内部没有请求，这里统一补充 loading 效果
// 首屏 loading 的兜底时长，避免父组件始终不注入数据时一直 loading
const LOCAL_PAGE_FIRST_LOADING_TIMEOUT = 1000;
// 本地切页 loading 的最小展示时长，确保覆盖当前页重新渲染的过程（避免露出空状态）
const LOCAL_PAGE_CHANGE_LOADING_DURATION = 150;
let isLocalPageFirstLoading = false;
// 用于跳过 watch 挂载时的首次触发，避免初始值触发无意义的 loading
let isTableDataWatchInitialized = false;
let localPageFirstLoadingTimer: ReturnType<typeof setTimeout> | null = null;
let radioClickHandler: ((e: Event) => void) | null = null;
// 标记filterPopup是否已经触发过一次emit
let hasEmitFilterPopup = false;

const radioEl = ref<HTMLElement | undefined | null>(null);
const paramsData: Record<string, any> = ref({});
// 设置列实例
const settingColumnEl = ref<HTMLElement | null>(null);
const localTableData = ref<any[]>([]);
const pagination = ref<PrimaryTableProps['pagination']>({
  current: 1,
  pageSize: 10,
  total: 0,
  theme: 'default',
  pageSizeOptions: [10, 20, 50, 100],
});
const isAllSelection = ref(false);
// 用于处理同步更新表格组件数据后，组件实例销毁重建
const tableKey = ref(-1);
const localPageLoading = ref(false);

if (Object.keys(maxLimitConfig ?? {})?.length) {
  pagination.value = Object.assign(pagination.value, {
    pageSize: maxTableLimit,
    pageSizeOptions: sortedUniq(sortBy([10, 20, 50, 100, maxTableLimit])),
  });
}

const isShowSelectionRow = computed(() => {
  return showFirstFullRow && selections.value.length > 0;
});

const disabledSelected = computed(() => {
  return !tableData.value?.length;
});
// 缓存filteredTableData
const memoizedFilter = memoize(
  (list: any[]) => list.filter(item => !disabledCheckSelection(item)),
  (list: any[]) => JSON.stringify(list.map(item => item[tableRowKey])),
);

// 过滤掉禁止勾选的数据
const filteredTableData = computed(() => memoizedFilter(tableData.value));

// 设置表格半选效果
const setIndeterminate = computed(() => {
  const availableCount = filteredTableData.value.length;
  if (availableCount === 0) return false;

  const selectedAvailableCount = filteredTableData.value.filter((item) => {
    return selectionsRowKeys.value.includes(item[tableRowKey]);
  }).length;

  return selectedAvailableCount > 0 && selectedAvailableCount < availableCount;
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

          handleCustomSelectAllChange({
            isCheck: isAllSelection.value,
            tableRowKey,
            tables: filteredTableData.value,
          });

          emit('selection-change', {
            selectionsRowKeys: selections.value.map(item => item[tableRowKey]),
            selections: selections.value,
          });
        }}
      />
    );
  },
  cell: (h: unknown, { row }: { row: TableRowData }) => {
    const isDisabled = disabledSelected.value || disabledCheckSelection?.(row);
    const isChecked = selections.value.map(item => item[tableRowKey]).includes(row[tableRowKey]);

    return (
      <Popover
        trigger="hover"
        placement="top"
        popoverDelay={100}
        disabled={typeof disabledCheckSelection === 'undefined' ? true : !disabledCheckSelection?.(row)}
      >
        {{
          default: () => (
            <Checkbox
              modelValue={isChecked}
              class="custom-ag-table-checkbox"
              disabled={isDisabled}
              onChange={(isCheck: boolean, e: MouseEvent) => {
                e?.stopPropagation();

                if (isDisabled) return;

                // 这里可以增加disabled逻辑
                handleCustomSelectChange({
                  isCheck,
                  tableRowKey,
                  row,
                });
                const selectionTable = filteredTableData.value;
                const checkedIds = selectionsRowKeys.value.filter((id: number | string) =>
                  selectionTable.some(item => item[tableRowKey] === id),
                );
                isAllSelection.value = checkedIds.length > 0 && checkedIds.length === selectionTable.length;

                emit('selection-change', {
                  selectionsRowKeys: checkedIds,
                  selections: selections.value,
                });
              }}
            />
          ),
          content: () => (
            <div>
              {slots?.selectionPopoverContent?.(row) ?? row.selectionTip}
            </div>
          ),
        }}
      </Popover>
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

const localeConfig = computed(() => locale.value === 'zh-cn' ? cnConfig : enConfig);

/**
 * 请求表格数据
 * @param {Object} requestParams 请求数据
 * @param {Boolean} loading 加载状态
 * @param {Object | Null} error 错误信息
 * @param run 手动触发请求的函数
 */
const { params: requestParams, loading: requestLoading, error, refresh, run } = useRequest(apiMethod, {
  manual: true,
  // 是否立即执行请求
  // @ts-ignore
  immediate,
  defaultParams: [offsetAndLimit.value],
  onSuccess: (response: {
    results: any[]
    count: number
  }) => {
    let results = response?.results ?? [];
    // 如果表格不存在唯一标识，自动生成随机rowKey
    if (!isExistUniqueKey && results.length > 0) {
      results = results.map((item, index) => {
        return {
          ...item,
          tempUniqueId: `row_${item[tableRowKey]}_${index}_${Math.random().toString(36).slice(2)}`,
        };
      });
    }
    paramsData.value = { ...requestParams.value?.[0] };
    pagination.value!.total = response?.count ?? 0;
    tableData.value = cloneDeep(results);
    setTimeout(() => {
      getSelectionData();
    });
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

// 表格最终加载态：外部传入 true 时优先展示 loading，
// 外部为 false 或未传时由内部加载态决定，避免外部提前结束时打断正在接续的 loading（露出空状态）
const tableLoading = computed(() => {
  const innerLoading = localPage ? localPageLoading.value : requestLoading.value;
  return loading || innerLoading;
});

// 数据刷新时的 loading：只覆盖「数据变更 -> 同步渲染完成」这段，
// 避免数据已经渲染出来而遮罩还在（看起来像又调了一次 loading）
const startLocalPageRefreshLoading = () => {
  // 首屏 loading 未结束时直接延续为刷新 loading，避免先结束再重新开始出现两次 loading
  isLocalPageFirstLoading = false;
  if (localPageFirstLoadingTimer) {
    clearTimeout(localPageFirstLoadingTimer);
    localPageFirstLoadingTimer = null;
  }
  localPageLoading.value = true;
};

// 数据已同步渲染完成，结束本地分页 loading（含首屏 loading）
const stopLocalPageLoading = () => {
  isLocalPageFirstLoading = false;
  if (localPageFirstLoadingTimer) {
    clearTimeout(localPageFirstLoadingTimer);
    localPageFirstLoadingTimer = null;
  }
  localPageLoading.value = false;
};

// 首屏 loading：本地分页首次渲染时内部数据尚未同步完成，先展示 loading，避免先闪一次空状态占位
const startLocalPageFirstLoading = () => {
  if (!localPage) {
    return;
  }
  isLocalPageFirstLoading = true;
  localPageLoading.value = true;
  // 兜底：父组件始终不注入数据时避免一直 loading
  localPageFirstLoadingTimer = setTimeout(() => {
    stopLocalPageLoading();
  }, LOCAL_PAGE_FIRST_LOADING_TIMEOUT);
};

startLocalPageFirstLoading();

// 初始化表格配置项
const initTableSettings = () => {
  const columns = tableColumns.value || [];
  const visibleColumn = columns.filter(tc => !hiddenColumn.includes(tc.colKey));
  const allColKeys = visibleColumn.map(col => col.colKey);

  const baseConfig = {
    fontSize: 'medium',
    rowSize: 'medium',
    disabled: [] as string[],
    checked: [...allColKeys],
    fields: visibleColumn.map(col => ({
      label: col.displayTitle ?? col.title,
      field: col.colKey,
    })),
  };

  const filterCols = columns.filter(col => !['row-select', 'serial-number'].includes(col.colKey));
  const firstValidKey = filterCols[0]?.colKey;
  if (firstValidKey) baseConfig.disabled = [firstValidKey];

  const tableSettingStorage = localStorage.getItem(localStorageKey.value);

  if (!tableSettingStorage) return baseConfig;

  let storageSettings = null;
  try {
    storageSettings = JSON.parse(tableSettingStorage);
  }
  catch {
    return baseConfig;
  }

  let safeChecked = [...baseConfig.checked];
  if (storageSettings && Array.isArray(storageSettings.checked)) {
    safeChecked = storageSettings.checked.filter(key => allColKeys.includes(key));
  }

  return {
    ...baseConfig,
    fontSize: storageSettings?.fontSize ?? baseConfig.fontSize,
    rowSize: storageSettings?.rowSize ?? baseConfig.rowSize,
    checked: safeChecked,
  };
};

// 业务侧会通过 v-model:settings 主动置 null 来触发设置重算（如每次请求数据前），
// 若把 null 直接透传给 tdesign/bkui，中间态会把内部 rowSize/fontSize 固化为默认值，
// 导致刷新后设置面板（行高、字号）回显不正确，因此对外统一暴露一个非空的设置对象
const innerTableSettings = computed<BkUiSettings>(() => tableSettings.value ?? initTableSettings());

const tableSettingSize = computed(() => innerTableSettings.value?.rowSize ?? 'medium');

// 同步初始化：表格设置必须在首次渲染前就绪，
// 否则 tdesign-ui 会把内部 rowSize/fontSize 固化为默认值，导致设置面板回显错误
watch(
  tableSettings,
  () => {
    if (!tableSettings.value && showSettings) {
      tableSettings.value = initTableSettings();
    }
  },
  {
    deep: true,
    immediate: true,
    // 外部置空后需要同步补齐，避免 null 中间态被 tdesign/bkui 固化成默认值
    flush: 'sync',
  },
);

// 当cacheIdentifier发生变化时需要按新的缓存读取设置（使用场景，同路由下多表格复用）
// 用标记位跳过 immediate 首次执行，而非用 oldVal !== undefined 守卫：
// 否则当 cacheIdentifier 初始为 undefined、挂载后才被赋值时，'undefined -> 有值' 的首次
// 切换也会因 oldVal 仍为 undefined 而被跳过，导致新标识下的表格设置不会被读取
let isCacheIdentifierWatchInitialized = false;
watch(
  () => cacheIdentifier,
  (newVal: string, oldVal: string) => {
    if (!isCacheIdentifierWatchInitialized) {
      isCacheIdentifierWatchInitialized = true;
      return;
    }
    if (newVal && newVal !== oldVal && showSettings) {
      updateCacheIdentifier(newVal);
      // 直接重算设置，不销毁表格实例，避免整体重绘
      tableSettings.value = initTableSettings();
      tableKey.value = +new Date();
    }
  },
  { immediate: true },
);

watch(
  tableData,
  (newTableData: any) => {
    // 首次触发为挂载时的初始数据，之后均为外部注入
    const isFirstSync = !isTableDataWatchInitialized;
    if (localPage) {
      if (!isFirstSync) {
        // 外部注入数据后展示刷新 loading，首屏 loading 未结束时自动延续
        startLocalPageRefreshLoading();
      }
      isTableDataWatchInitialized = true;
    }

    setTimeout(() => {
      localTableData.value = cloneDeep(newTableData || []);
      if (localPage) {
        pagination.value.total = localTableData.value.length;
        // 挂载时的初始数据为空时保留 loading，等待外部注入数据或兜底超时；
        // 外部注入的数据即使为空也视为已就绪，结束 loading 避免数据渲染后遮罩仍在
        if (isFirstSync && isLocalPageFirstLoading && !localTableData.value.length) {
          return;
        }
        stopLocalPageLoading();
      }
    }, 0);

    // 缓存清空仍同步执行，避免数据不一致
    const rowKeys = (newTableData || []).map(item => item?.[tableRowKey]);
    if (rowKeys.length > 0) {
      // @ts-ignore
      memoizedFilter?.cache?.clear();
    }
  },
  {
    immediate: true,
    deep: true,
  },
);

watch([selections, selectedRowKeys], () => {
  emit('selection-change', {
    selectionsRowKeys: selectionsRowKeys.value,
    selections: selections.value,
  });
  if (localPage) {
    const { current, pageSize, total } = pagination.value;
    if (current > Math.ceil(total / pageSize) && total > 0) {
      pagination.value.current = Math.ceil(total / pageSize);
    }
  }
}, { deep: true });

// hiddenColumn 只影响表格设置的列清单与默认勾选，
// 变化时按新的列集合重算设置即可，无需销毁表格实例
watch(
  () => hiddenColumn,
  (newVal: string[], oldVal: string[]) => {
    if (!showSettings || isEqual(newVal, oldVal)) return;
    tableSettings.value = initTableSettings();
  },
  { deep: true },
);

const fetchData = (
  params: Record<string, any> = {},
  options: { resetPage?: boolean } = { resetPage: false },
) => {
  if (options.resetPage) {
    pagination.value.current = 1;
  }
  run({
    ...filterSimpleEmpty(params),
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
    const isArrayObject = some(checkTableData, isPlainObject);
    const filterCheckTableData = isArrayObject ? checkTableData.map(check => check[tableRowKey]) : checkTableData;
    const selectionTable = filteredTableData.value;
    const checkedIds = selectionTable
      .filter(item => filterCheckTableData.includes(item[tableRowKey]))
      .map(check => check[tableRowKey]);
    isAllSelection.value = checkedIds.length === selectionTable.length;
  }
  else {
    isAllSelection.value = false;
  }
};

// 获取回显勾选项数据
const getSelectionData = () => {
  setTimeout(() => {
    renderSelectionData();
  }, 50);
};

// 本地分页设置回显勾选项数据
const setSelectionData = (selectionList: any[]) => {
  // 延迟执行，确保表格 DOM 已挂载
  setTimeout(() => {
    renderSelectionData(selectionList);
  }, 100);
};

// 节流处理：100ms 内最多触发 1 次
const throttledHandleRowEnter = throttle((e, row) => {
  emit('row-mouseenter', {
    e,
    row,
  });
}, 100);

const throttledHandleRowLeave = throttle((e, row) => {
  delete row.isOverflow;
  emit('row-mouseleave', {
    e,
    row,
  });
}, 100);

const handleRowEnter = ({ e, row }: {
  e: MouseEvent
  row: TableRowData
}) => {
  throttledHandleRowEnter(e, row);
};

const handleRowLeave = ({ e, row }: {
  e: MouseEvent
  row: TableRowData
}) => {
  throttledHandleRowLeave(e, row);
};

const handleCellEnter = ({ e, row }: {
  e: MouseEvent
  row: TableRowData
}) => {
  const cell = (e.target as HTMLElement).closest('.truncate');
  if (cell) {
    const isOverflow = cell.scrollWidth > cell.clientWidth;
    // 仅当状态变化时才赋值
    if (row.isOverflow !== isOverflow) {
      row.isOverflow = isOverflow;
    }
  }
};

const handleCellLeave = ({ row }: { row: TableRowData }) => {
  if (row.isOverflow) {
    delete row.isOverflow;
  }
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
  // 本地分页切换后，重新渲染当前页的勾选状态
  if (localPage) {
    // 本地切页时补充 loading，覆盖当前页重新渲染的过程，避免大数据量下的空白感
    startLocalPageRefreshLoading();
    nextTick(() => {
      if (showSelection) {
        getSelectionData();
      }
      // 延后关闭：表格重渲染存在中间帧，过早结束会露出空状态
      setTimeout(() => {
        stopLocalPageLoading();
      }, LOCAL_PAGE_CHANGE_LOADING_DURATION);
    });
  }
  emit('page-change', {
    current,
    pageSize,
  });
};

const handleSettingChange = (settings: ITableSettings) => {
  // 事件回调偶尔会发生 columns 重复问题，这里做去重处理
  const correctSettings = {
    ...settings,
    columns: uniq(settings.columns),
  };
  changeTableSettings(correctSettings);
};

// 处理自定义重置功能和点击单选直接关闭弹框
const handleRadioFilterClick = () => {
  // 获取filterPopup内容区域，没获取到代表已关闭弹框重置默认值
  const popupWrapper = document.querySelector('.t-table__filter-pop-wrapper');
  if (!popupWrapper) {
    hasEmitFilterPopup = false;
  }

  setTimeout(() => {
    const filterIconEl = document.querySelector('.need-filter-icon-handler .t-table__filter-icon-wrap');
    const filterPopup = document.querySelector('.t-table__filter-pop-content');
    radioEl.value = filterPopup?.querySelector('.t-radio-group');

    if (radioEl.value) {
      const confirmBtn = document.querySelector('.t-table__filter--bottom-buttons > .t-button--theme-primary');
      // @ts-ignore
      radioClickHandler = (event: MouseEvent) => {
        // @ts-ignore
        const radioLabel = event.target.closest('label.t-radio');
        const radioInput = radioLabel?.querySelector('input.t-radio__former');
        if (radioInput?.checked) {
          // @ts-ignore
          confirmBtn.click();
        }
      };
      radioEl.value.addEventListener('click', radioClickHandler);
    }

    // 抛出filter Icon点击事件用于处理相关功能业务
    if (filterIconEl && !hasEmitFilterPopup) {
      hasEmitFilterPopup = true;
      emit('filter-icon-click');
    }
  }, 0);
};

// 处理点击设置列触发设置弹框
const handleSettingColumnClick = (e: MouseEvent) => {
  e?.stopPropagation();
  // @ts-ignore
  const isIconClick = e.target?.closest('.t-icon-setting');
  if (!isIconClick && settingColumnEl.value) {
    settingColumnEl.value?.querySelector('.column-settings-icon')?.click();
  }
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
  handleListenerRadio();
  handleListenerSetting();
});

onBeforeUnmount(() => {
  if (localPageFirstLoadingTimer) {
    clearTimeout(localPageFirstLoadingTimer);
    localPageFirstLoadingTimer = null;
  }
  memoizedFilter?.cache?.clear();
  document.removeEventListener('click', handleRadioFilterClick);
  radioEl.value?.removeEventListener('click', radioClickHandler);
  settingColumnEl.value?.removeEventListener('click', handleSettingColumnClick);
  radioEl.value = null;
  radioClickHandler = null;
  settingColumnEl.value = null;
  tableSettings.value = null;
});

defineExpose({
  TDesignTableRef,
  loading: tableLoading,
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
  border: 1px solid #dcdee5;

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

  &.t-table--hoverable {

    .t-table__header th,
    .t-table__body tr {

      &:hover {
        background-color: #f0f1f5 !important;
      }
    }
  }

  &.t-size-m {

    .t-table__header {

      th {
        padding-top: 10.5px;

        &.t-table__th-row-select {
          padding-top: 9.5px;
        }
      }
    }
  }

  &.t-table--column-resizable:not(.t-table--bordered) {

    thead.t-table__header {

      &:hover {

        th {

          border-top: none;

          &:not(:last-child):not([data-colkey="__col_setting__"]) {
            border-right: none;
          }
        }
      }

      th {

        border-top: none;

        &:not(:last-child):not([data-colkey="__col_setting__"]) {
          border-right: none;
        }

        &[data-colkey="__col_setting__"] {
          box-shadow: inset 1px 0 0 #dcdee5;
        }
      }
    }
  }

  &.primary-table-no-data {

    .t-table__row--full.t-table__first-full-row {
      height: 0;
    }

    .t-table__pagination-wrap {
      display: none;
    }
  }

  &.primary-table-show-pagination {

    .t-table--scroll-vertical {
      bottom: 64px;
    }
  }

  &.primary-table-hide-pagination {

    .t-table__body {

      tr {

        &:last-of-type {

          td {
            border-bottom: none;
          }
        }
      }
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
