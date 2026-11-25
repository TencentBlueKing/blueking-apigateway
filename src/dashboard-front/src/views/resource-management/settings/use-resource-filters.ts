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

import type { ISearchItem, ISearchValue } from 'bkui-vue/lib/search-select/utils';
import type { LocationQuery, LocationQueryRaw, RouteLocationNormalizedLoaded, Router } from 'vue-router';
import type { FilterValue, TableSort } from '@/components/base/ag-table';
import { HTTP_METHODS } from '@/constants';
import type { IGatewaysResourcesListQuery } from '@/services/types/gateway/resource';
import {
  type IResourceAuthFilterOption,
  type ResourceAuthFilterType,
  getResourceAuthFilterOptions,
  parseAuthTypeQuery,
} from '@/utils/auth-config';

type Translate = (key: string) => string;

export type ResourceOrderBy = 'updated_time' | '-updated_time';

export interface IResourceFilterState {
  keyword: string
  name: string
  path: string
  method: string[]
  auth_type: ResourceAuthFilterType[]
  backend_name: string
  backend_id: string
  label_ids: number[]
  kind: string
  order_by: ResourceOrderBy | ''
}

export interface IUseResourceFiltersOptions {
  gatewayId: () => number
  isResourceAuthV2: () => boolean
  isGatewayReady: () => boolean
  route: RouteLocationNormalizedLoaded
  router: Router
  t: Translate
  onQueryChange: (query: IGatewaysResourcesListQuery) => void
}

// 由资源列表页托管并同步到 URL query 的搜索字段（不包含 kind，避免与编辑页返回时携带的 kind 冲突）
export const URL_FILTER_KEYS = [
  'keyword',
  'name',
  'path',
  'method',
  'auth_type',
  'backend_name',
  'backend_id',
] as const;

type UrlFilterKey = (typeof URL_FILTER_KEYS)[number];

export const createEmptyResourceFilterState = (): IResourceFilterState => ({
  keyword: '',
  name: '',
  path: '',
  method: [],
  auth_type: [],
  backend_name: '',
  backend_id: '',
  label_ids: [],
  kind: '',
  order_by: '',
});

const areArraysEqual = <T>(left: readonly T[], right: readonly T[]): boolean =>
  left.length === right.length && left.every((item, index) => item === right[index]);

export const areFilterStatesEqual = (left: IResourceFilterState, right: IResourceFilterState): boolean =>
  left.keyword === right.keyword
  && left.name === right.name
  && left.path === right.path
  && left.backend_name === right.backend_name
  && left.backend_id === right.backend_id
  && left.kind === right.kind
  && left.order_by === right.order_by
  && areArraysEqual(left.method, right.method)
  && areArraysEqual(left.auth_type, right.auth_type)
  && areArraysEqual(left.label_ids, right.label_ids);

const extractFirstQueryString = (value: unknown): string => {
  if (Array.isArray(value)) {
    const first = value.find((item): item is string => typeof item === 'string' && item.trim().length > 0);
    return first ? first.trim() : '';
  }
  return typeof value === 'string' ? value.trim() : '';
};

const parseStringList = (input: unknown): string[] => {
  const rawValues = Array.isArray(input)
    ? input.flatMap(item => (typeof item === 'string' ? item.split(',') : []))
    : typeof input === 'string'
      ? input.split(',')
      : [];

  const result: string[] = [];
  const seen = new Set<string>();
  rawValues.forEach((item) => {
    const normalized = item.trim();
    if (!normalized || seen.has(normalized)) return;
    seen.add(normalized);
    result.push(normalized);
  });
  return result;
};

const parseNumberList = (input: unknown): number[] => {
  const rawValues = Array.isArray(input)
    ? input.flatMap(item => (typeof item === 'string' ? item.split(',') : [item]))
    : typeof input === 'string'
      ? input.split(',')
      : input != null
        ? [input]
        : [];

  const result: number[] = [];
  const seen = new Set<number>();
  rawValues.forEach((item) => {
    const num = typeof item === 'number' ? item : Number(String(item).trim());
    if (!Number.isFinite(num) || num <= 0 || seen.has(num)) return;
    seen.add(num);
    result.push(num);
  });
  return result;
};

// 从 URL query 解析本页托管的 7 个搜索筛选字段
export const parseRouteQueryToFilterState = (
  query: LocationQuery,
  options: { isResourceAuthV2: boolean },
): Pick<IResourceFilterState, UrlFilterKey> => ({
  keyword: extractFirstQueryString(query.keyword),
  name: extractFirstQueryString(query.name),
  path: extractFirstQueryString(query.path),
  method: parseStringList(query.method),
  auth_type: options.isResourceAuthV2 ? parseAuthTypeQuery(query.auth_type) : [],
  backend_name: extractFirstQueryString(query.backend_name),
  backend_id: extractFirstQueryString(query.backend_id),
});

// 基于当前路由 query 生成下一步 query；若托管字段无实质变化返回 null，避免触发多余的 router.replace
export const buildNextRouteQuery = (
  currentQuery: LocationQuery,
  state: IResourceFilterState,
  options: { syncAuthType: boolean },
): LocationQueryRaw | null => {
  const nextQuery: LocationQueryRaw = {};
  Object.entries(currentQuery).forEach(([key, value]) => {
    if (value !== undefined) {
      nextQuery[key] = value;
    }
  });

  const desiredValues: Partial<Record<UrlFilterKey, string | undefined>> = {
    keyword: state.keyword || undefined,
    name: state.name || undefined,
    path: state.path || undefined,
    method: state.method.length ? state.method.join(',') : undefined,
    backend_name: state.backend_name || undefined,
    backend_id: state.backend_id || undefined,
  };
  if (options.syncAuthType) {
    desiredValues.auth_type = state.auth_type.length ? state.auth_type.join(',') : undefined;
  }

  let changed = false;
  (Object.entries(desiredValues) as Array<[UrlFilterKey, string | undefined]>).forEach(([key, nextValue]) => {
    const currentRaw = currentQuery[key];
    const currentNormalized = Array.isArray(currentRaw)
      ? currentRaw.filter((item): item is string => typeof item === 'string').join(',') || undefined
      : (typeof currentRaw === 'string' && currentRaw !== '' ? currentRaw : undefined);

    // 数组形式的单参（如 ?auth_type=a&auth_type=b）或值不同时均视为需要规范化写入
    const isArrayParam = Array.isArray(currentRaw);
    if (isArrayParam || currentNormalized !== nextValue) {
      changed = true;
    }

    if (nextValue === undefined) {
      delete nextQuery[key];
    }
    else {
      nextQuery[key] = nextValue;
    }
  });

  return changed ? nextQuery : null;
};

// 将单一筛选状态派生为 BkSearchSelect 的展示值
export const filterStateToSearchValue = (
  state: IResourceFilterState,
  options: {
    t: Translate
    authOptions: readonly IResourceAuthFilterOption[]
    isResourceAuthV2: boolean
  },
): ISearchValue[] => {
  const { t, authOptions, isResourceAuthV2 } = options;
  const result: ISearchValue[] = [];

  if (state.keyword) {
    result.push({
      id: state.keyword,
      name: state.keyword,
      type: 'text',
    });
  }
  if (state.name) {
    result.push({
      id: 'name',
      name: t('资源名称'),
      values: [{
        id: state.name,
        name: state.name,
      }],
    });
  }
  if (state.path) {
    result.push({
      id: 'path',
      name: t('前端请求路径'),
      values: [{
        id: state.path,
        name: state.path,
      }],
    });
  }
  if (state.method.length) {
    result.push({
      id: 'method',
      name: t('前端请求方法'),
      values: state.method.map(method => ({
        id: method,
        name: method,
      })),
    });
  }
  if (isResourceAuthV2 && state.auth_type.length) {
    const authLabelMap = new Map(authOptions.map(item => [item.id, item.name]));
    result.push({
      id: 'auth_type',
      name: t('认证方式'),
      values: state.auth_type.map(id => ({
        id,
        name: authLabelMap.get(id) ?? id,
      })),
    });
  }
  if (state.backend_name) {
    result.push({
      id: 'backend_name',
      name: t('后端服务'),
      values: [{
        id: state.backend_name,
        name: state.backend_name,
      }],
    });
  }
  if (state.backend_id) {
    result.push({
      id: 'backend_id',
      name: t('后端服务ID'),
      values: [{
        id: state.backend_id,
        name: state.backend_id,
      }],
    });
  }

  return result;
};

const extractSearchFirstId = (item: ISearchValue): string => {
  const firstVal = item.values?.find(val => val?.id != null && String(val.id).trim() !== '');
  return firstVal ? String(firstVal.id).trim() : '';
};

// 从 BkSearchSelect 的变更结果合并回单一状态，完整保留仅表头字段（label_ids、kind、order_by）
export const applySearchValueToFilterState = (
  current: IResourceFilterState,
  searchValue: readonly ISearchValue[],
  options: { isResourceAuthV2: boolean },
): IResourceFilterState => {
  const next: IResourceFilterState = {
    ...createEmptyResourceFilterState(),
    label_ids: [...current.label_ids],
    kind: current.kind,
    order_by: current.order_by,
  };

  searchValue.forEach((item) => {
    if (!item) return;

    // 无子值的纯文本输入作为全局 keyword 模糊搜索
    if (item.type === 'text' || (!item.values?.length && item.id === item.name)) {
      const keyword = String(item.name ?? item.id ?? '').trim();
      if (keyword) {
        next.keyword = keyword;
      }
      return;
    }

    switch (item.id) {
      case 'name':
        next.name = extractSearchFirstId(item);
        break;
      case 'path':
        next.path = extractSearchFirstId(item);
        break;
      case 'method':
        next.method = parseStringList(item.values?.map(val => String(val?.id ?? '')));
        break;
      case 'auth_type':
        if (options.isResourceAuthV2) {
          next.auth_type = parseAuthTypeQuery(item.values?.map(val => String(val?.id ?? '')));
        }
        break;
      case 'backend_name':
        next.backend_name = extractSearchFirstId(item);
        break;
      case 'backend_id':
        next.backend_id = extractSearchFirstId(item);
        break;
      default:
        break;
    }
  });

  return next;
};

// 将 AgTable 的 @filter-change 载荷合并回单一状态
export const applyTableFilterChangeToFilterState = (
  current: IResourceFilterState,
  filterItem: FilterValue,
  options: { isResourceAuthV2: boolean },
): IResourceFilterState => {
  const next: IResourceFilterState = {
    ...current,
    method: [...current.method],
    auth_type: [...current.auth_type],
    label_ids: [...current.label_ids],
  };

  Object.entries(filterItem).forEach(([colKey, rawValue]) => {
    if (colKey === 'auth_config' || colKey === 'auth_type') {
      if (options.isResourceAuthV2) {
        next.auth_type = parseAuthTypeQuery(rawValue);
      }
    }
    else if (colKey === 'method') {
      next.method = parseStringList(rawValue);
    }
    else if (colKey === 'label_ids') {
      next.label_ids = parseNumberList(rawValue);
    }
    else if (colKey === 'kind') {
      next.kind = typeof rawValue === 'string' ? rawValue.trim() : '';
    }
  });

  return next;
};

// 将 AgTable 的 @sort-change 载荷合并回单一状态
export const applyTableSortToFilterState = (
  current: IResourceFilterState,
  sort: TableSort | null | undefined,
): IResourceFilterState => {
  const sortInfo = Array.isArray(sort) ? sort[0] : sort;
  let orderBy: ResourceOrderBy | '' = '';
  if (sortInfo?.sortBy === 'updated_time') {
    orderBy = sortInfo.descending ? '-updated_time' : 'updated_time';
  }
  else if (sortInfo) {
    // 非受支持排序列不改动现有 order_by
    return current;
  }

  if (current.order_by === orderBy) {
    return current;
  }

  return {
    ...current,
    order_by: orderBy,
  };
};

// 派生 AgTable :filter-value 受控值（表头列 colKey 为 auth_config，对外参数为 auth_type）
export const filterStateToTableFilterValue = (
  state: IResourceFilterState,
  options: { isResourceAuthV2: boolean },
): FilterValue => {
  const result: FilterValue = {};
  if (state.method.length) {
    result.method = [...state.method];
  }
  if (options.isResourceAuthV2 && state.auth_type.length) {
    result.auth_config = [...state.auth_type];
  }
  if (state.label_ids.length) {
    result.label_ids = [...state.label_ids];
  }
  if (state.kind) {
    result.kind = state.kind;
  }
  return result;
};

// 派生请求 GET /gateways/{gateway_id}/resources/ 的查询参数
export const filterStateToApiQuery = (
  state: IResourceFilterState,
  options: { isResourceAuthV2: boolean },
): IGatewaysResourcesListQuery => {
  const query: IGatewaysResourcesListQuery = {};
  if (state.keyword) query.keyword = state.keyword;
  if (state.name) query.name = state.name;
  if (state.path) query.path = state.path;
  if (state.method.length) query.method = state.method.join(',');
  if (options.isResourceAuthV2 && state.auth_type.length) {
    query.auth_type = state.auth_type.join(',');
  }
  if (state.backend_name) query.backend_name = state.backend_name;
  if (state.backend_id) {
    const parsedBackendId = Number(state.backend_id);
    query.backend_id = Number.isFinite(parsedBackendId) ? parsedBackendId : (state.backend_id as unknown as number);
  }
  if (state.label_ids.length) query.label_ids = state.label_ids.join(',');
  if (state.kind === 'standard' || state.kind === 'ai') query.kind = state.kind;
  if (state.order_by) query.order_by = state.order_by;
  return query;
};

// 派生 AgTable :sort 受控值，保证清空筛选时表头排序箭头同步复位
export const filterStateToTableSort = (state: IResourceFilterState): TableSort | undefined => {
  if (state.order_by === 'updated_time') {
    return {
      sortBy: 'updated_time',
      descending: false,
    };
  }
  if (state.order_by === '-updated_time') {
    return {
      sortBy: 'updated_time',
      descending: true,
    };
  }
  return undefined;
};

export const serializeApiQueryKey = (query: IGatewaysResourcesListQuery): string =>
  JSON.stringify(
    Object.keys(query)
      .sort()
      .map(key => [key, query[key as keyof IGatewaysResourcesListQuery]]),
  );

export const useResourceFilters = (options: IUseResourceFiltersOptions) => {
  const {
    gatewayId,
    isResourceAuthV2,
    isGatewayReady,
    route,
    router,
    t,
    onQueryChange,
  } = options;

  const filterState = ref<IResourceFilterState>(createEmptyResourceFilterState());
  // 标记网关切换过渡期（route.params.id 尚未跟上新 gatewayId prop），防止误读写旧网关 URL query
  let wasInTransition = false;
  // 标记是否已完成首次挂载查询，挂载前仅构建状态不提前发请求
  let isReadyForFetch = false;
  let lastDispatchedQueryKey = '';

  const authFilterOptions = computed(() => getResourceAuthFilterOptions(t));
  const authTypeFilterList = computed(() => [
    {
      label: 'All',
      checkAll: true,
    },
    ...authFilterOptions.value.map(item => ({
      label: item.name,
      value: item.id,
    })),
  ]);

  const searchData = computed<ISearchItem[]>(() => [
    {
      name: t('资源名称'),
      id: 'name',
      placeholder: t('请输入资源名称'),
    },
    {
      name: t('前端请求路径'),
      id: 'path',
      placeholder: t('请输入前端请求路径'),
    },
    {
      name: t('前端请求方法'),
      id: 'method',
      placeholder: t('请选择前端请求方法'),
      children: HTTP_METHODS,
      multiple: true,
    },
    ...(isResourceAuthV2()
      ? [
        {
          name: t('认证方式'),
          id: 'auth_type',
          placeholder: t('请选择认证方式'),
          children: authFilterOptions.value,
          multiple: true,
        },
      ]
      : []),
    {
      name: t('后端服务'),
      id: 'backend_name',
      placeholder: t('请输入后端服务'),
    },
    {
      name: t('后端服务ID'),
      id: 'backend_id',
      placeholder: t('请输入后端服务ID'),
    },
  ]);

  const apiQuery = computed<IGatewaysResourcesListQuery>(() =>
    filterStateToApiQuery(filterState.value, { isResourceAuthV2: isResourceAuthV2() }));

  const tableFilterValue = computed<FilterValue>(() =>
    filterStateToTableFilterValue(filterState.value, { isResourceAuthV2: isResourceAuthV2() }));

  const tableSort = computed<TableSort | undefined>(() => filterStateToTableSort(filterState.value));

  const syncRouteQueryIfNeeded = () => {
    if (Number(route.params.id) !== gatewayId()) {
      return;
    }
    const nextQuery = buildNextRouteQuery(route.query, filterState.value, {
      syncAuthType: isGatewayReady(),
    });
    if (nextQuery) {
      void router.replace({ query: nextQuery });
    }
  };

  const dispatchQueryIfChanged = (force = false) => {
    if (!isReadyForFetch) return;
    const nextQuery = apiQuery.value;
    const nextKey = serializeApiQueryKey(nextQuery);
    if (!force && nextKey === lastDispatchedQueryKey) {
      return;
    }
    lastDispatchedQueryKey = nextKey;
    onQueryChange(nextQuery);
  };

  const commitFilterState = (nextState: IResourceFilterState, commitOptions: { syncUrl?: boolean } = {}) => {
    const { syncUrl = true } = commitOptions;
    if (areFilterStatesEqual(filterState.value, nextState)) {
      return false;
    }
    filterState.value = nextState;
    if (syncUrl) {
      syncRouteQueryIfNeeded();
    }
    dispatchQueryIfChanged();
    return true;
  };

  const searchValue = computed<ISearchValue[]>({
    get: () => filterStateToSearchValue(filterState.value, {
      t,
      authOptions: authFilterOptions.value,
      isResourceAuthV2: isResourceAuthV2(),
    }),
    set: (nextSearchValue) => {
      const nextState = applySearchValueToFilterState(filterState.value, nextSearchValue ?? [], {
        isResourceAuthV2: isResourceAuthV2(),
      });
      commitFilterState(nextState, { syncUrl: true });
    },
  });

  const handleFilterChange = (filterItem: FilterValue) => {
    const nextState = applyTableFilterChangeToFilterState(filterState.value, filterItem, {
      isResourceAuthV2: isResourceAuthV2(),
    });
    commitFilterState(nextState, { syncUrl: true });
  };

  const handleSortChange = (sort: TableSort | null | undefined) => {
    const nextState = applyTableSortToFilterState(filterState.value, sort);
    commitFilterState(nextState, { syncUrl: false });
  };

  const handleClearQueries = () => {
    const emptyState = createEmptyResourceFilterState();
    const changed = commitFilterState(emptyState, { syncUrl: true });
    if (!changed) {
      syncRouteQueryIfNeeded();
      dispatchQueryIfChanged(true);
    }
  };

  // 从外部路由（首屏加载、刷新、浏览器前进/后退）或网关 V1/V2 协议状态变化同步筛选条件
  watch(
    [() => route.params.id, () => route.query, isResourceAuthV2],
    () => {
      if (Number(route.params.id) !== gatewayId()) {
        wasInTransition = true;
        return;
      }

      if (wasInTransition) {
        wasInTransition = false;
        const hasLocalFilters = !areFilterStatesEqual(filterState.value, createEmptyResourceFilterState());
        if (!hasLocalFilters && Object.keys(route.query).some(key => route.query[key])) {
          void router.replace({ query: {} });
          return;
        }
      }

      const v2Enabled = isResourceAuthV2();
      const parsedFromRoute = parseRouteQueryToFilterState(route.query, { isResourceAuthV2: v2Enabled });
      const nextState: IResourceFilterState = {
        ...filterState.value,
        ...parsedFromRoute,
      };
      commitFilterState(nextState, { syncUrl: false });

      // 若 URL 中携带了被清洗掉的非法 auth_type（如 ?auth_type=personal,invalid），规范化写回 URL
      if (isGatewayReady() && v2Enabled && route.query.auth_type !== undefined) {
        syncRouteQueryIfNeeded();
      }
    },
    {
      immediate: true,
      deep: true,
    },
  );

  // 由页面 onMounted 调用，确保只执行一次首屏查询并记录已派发参数签名
  const markInitialFetchDispatched = () => {
    isReadyForFetch = true;
    lastDispatchedQueryKey = serializeApiQueryKey(apiQuery.value);
  };

  const startInitialFetch = () => {
    isReadyForFetch = true;
    dispatchQueryIfChanged(true);
  };

  return {
    filterState,
    authFilterOptions,
    authTypeFilterList,
    searchData,
    searchValue,
    tableFilterValue,
    tableSort,
    apiQuery,
    handleFilterChange,
    handleSortChange,
    handleClearQueries,
    markInitialFetchDispatched,
    startInitialFetch,
  };
};
