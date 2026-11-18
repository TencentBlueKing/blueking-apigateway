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

import { cloneDeep } from 'lodash-es';
import { useRequest } from 'vue-request';
import type { TableRowData } from '@blueking/tdesign-ui';
import { filterSimpleEmpty } from '@/utils/filterEmptyValues';
import type { ITablePagination, ITableQuery, TableApiMethod, TablePage } from './types';

const INITIAL_LOCAL_LOADING_TIMEOUT_MS = 1000;
const LOCAL_PAGE_CHANGE_LOADING_MS = 150;

interface ITableDataSourceOptions {
  sourceRows: Ref<TableRowData[]>
  apiMethod: () => TableApiMethod | undefined
  localPage: () => boolean
  immediate: () => boolean
  externalLoading: () => boolean | undefined
  tableRowKey: () => string
  isExistUniqueKey: () => boolean
  initialPageSize: number
  onPageChange: (page: TablePage) => void
  onRequestDone: () => void
}

// 展开、溢出提示等交互可以修改渲染行。嵌套字段在首次读取时复制，父页面修改原字段后再重新取值。
const createRenderRow = (sourceRow: TableRowData): TableRowData => {
  const renderRow = { ...sourceRow };
  for (const [field, sourceValue] of Object.entries(renderRow)) {
    if (!sourceValue || typeof sourceValue !== 'object') continue;
    const fieldSnapshot = computed(() => cloneDeep(sourceValue));
    Object.defineProperty(renderRow, field, {
      enumerable: true,
      configurable: true,
      get: () => fieldSnapshot.value,
      set: (localValue) => {
        // 插槽显式替换字段（例如展开行的资源列表）后，这份渲染行使用它自己的值。
        Object.defineProperty(renderRow, field, {
          value: localValue,
          enumerable: true,
          writable: true,
          configurable: true,
        });
      },
    });
  }
  return reactive(renderRow);
};

export const useTableDataSource = (options: ITableDataSourceOptions) => {
  const { sourceRows, initialPageSize } = options;
  const dataMode = computed(() => {
    if (options.localPage()) return 'local';
    return options.apiMethod() ? 'remote' : 'static';
  });
  const rowKeyField = computed(() => options.isExistUniqueKey() ? options.tableRowKey() : 'tempUniqueId');
  const sourceRowList = computed(() => Array.isArray(sourceRows.value) ? sourceRows.value : []);
  // 列表排序或过滤后复用同一输入行的渲染状态。输入行的顶层字段变化时只重建对应的渲染行。
  const renderRowBySource = new WeakMap<TableRowData, ComputedRef<TableRowData>>();
  const renderRows = computed(() => sourceRowList.value.map((sourceRow) => {
    if (!sourceRow || typeof sourceRow !== 'object') return sourceRow;
    let cachedRow = renderRowBySource.get(sourceRow);
    if (!cachedRow) {
      cachedRow = computed(() => createRenderRow(sourceRow));
      renderRowBySource.set(sourceRow, cachedRow);
    }
    return cachedRow.value;
  }));
  const pagination = reactive<ITablePagination>({
    current: 1,
    pageSize: initialPageSize,
    total: 0,
    theme: 'default',
    pageSizeOptions: [...new Set([10, 20, 50, 100, initialPageSize])].sort((left, right) => left - right),
  });
  const getPageQuery = () => ({
    offset: (pagination.current - 1) * pagination.pageSize,
    limit: pagination.pageSize,
  });

  const remoteRequest = useRequest(async (query: ITableQuery) => options.apiMethod()?.(query), {
    manual: true,
    defaultParams: [getPageQuery()],
    onSuccess: (result) => {
      if (!result || dataMode.value !== 'remote') return;
      // 业务页面通过 v-model 补充行字段，先复制一次以保护请求层缓存的响应。
      const fetchedRows = cloneDeep(result.results ?? []);
      if (!options.isExistUniqueKey()) {
        fetchedRows.forEach((row, index) => {
          row.tempUniqueId = `row_${row[options.tableRowKey()]}_${index}_${Math.random().toString(36).slice(2)}`;
        });
      }
      pagination.total = result.count ?? 0;
      sourceRows.value = fetchedRows;
      options.onRequestDone();
    },
    onError: (error) => {
      if (dataMode.value !== 'remote') return;
      sourceRows.value = [];
      pagination.total = 0;
      console.error(error);
    },
  });

  const fetchData = (filters: object = {}, { resetPage = false } = {}) => {
    if (dataMode.value !== 'remote') return;
    if (resetPage) pagination.current = 1;
    remoteRequest.run({
      ...filterSimpleEmpty(filters),
      ...getPageQuery(),
    });
  };
  const refresh = () => {
    if (dataMode.value === 'remote') remoteRequest.refresh();
  };

  const localLoading = ref(false);
  let localLoadingTimer: ReturnType<typeof setTimeout>;
  const stopLocalLoading = () => {
    clearTimeout(localLoadingTimer);
    localLoading.value = false;
  };
  const showLocalLoading = (durationMs: number) => {
    clearTimeout(localLoadingTimer);
    localLoading.value = true;
    localLoadingTimer = setTimeout(stopLocalLoading, durationMs);
  };

  // PrimaryTable 负责本地分页。删除末页最后一条数据时，这里把页码拉回最后一个有效页。
  watch([sourceRowList, () => sourceRowList.value.length, dataMode], ([, rowCount, currentMode], previous) => {
    stopLocalLoading();
    if (currentMode === 'local') {
      pagination.total = rowCount;
      const lastPage = Math.max(1, Math.ceil(rowCount / pagination.pageSize));
      pagination.current = Math.min(pagination.current, lastPage);
      // 外部重新注入数据时，遮罩只覆盖本轮渲染。immediate 的首次回调没有旧值。
      if (previous.length) showLocalLoading(0);
    }
    else if (currentMode === 'static') {
      pagination.total = 0;
    }
  }, { immediate: true });

  const setPagination = ({ current, pageSize }: TablePage) => {
    pagination.current = current;
    pagination.pageSize = pageSize;
    if (dataMode.value === 'remote') {
      // vue-request 在请求开始时记录参数，因此在筛选请求尚未返回时翻页也能沿用该筛选。
      const [lastQuery] = remoteRequest.params.value;
      fetchData(lastQuery);
    }
    if (dataMode.value === 'local') showLocalLoading(LOCAL_PAGE_CHANGE_LOADING_MS);
    options.onPageChange({
      current,
      pageSize,
    });
  };

  const setPaginationTheme = ({ theme, showPageSize = true }: {
    theme: 'default' | 'simple'
    showPageSize?: boolean
  }) => {
    pagination.theme = theme;
    pagination.showPageSize = showPageSize;
  };

  if (dataMode.value === 'local' && !sourceRowList.value.length) {
    showLocalLoading(INITIAL_LOCAL_LOADING_TIMEOUT_MS);
  }

  onScopeDispose(stopLocalLoading);

  watch(dataMode, () => remoteRequest.cancel());

  onMounted(() => {
    if (options.immediate()) fetchData();
  });

  const tableLoading = computed(() => {
    if (options.externalLoading()) return true;
    if (dataMode.value === 'local') return localLoading.value;
    return dataMode.value === 'remote' && remoteRequest.loading.value;
  });

  return {
    renderRows,
    rowKeyField,
    pagination,
    tableLoading,
    // AgTableEmpty 按请求参数区分“暂无数据”和“搜索结果为空”。切走远程模式时使用当前数据源的空态。
    requestParams: computed(() => dataMode.value === 'remote' ? remoteRequest.params.value : []),
    requestError: computed(() => dataMode.value === 'remote' ? remoteRequest.error.value : undefined),
    fetchData,
    refresh,
    setPagination,
    setPaginationTheme,
    resetPaginationTheme: () => setPaginationTheme({ theme: 'default' }),
  };
};
