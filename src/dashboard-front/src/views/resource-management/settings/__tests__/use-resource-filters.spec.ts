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

import { defineComponent, h, nextTick, reactive, ref } from 'vue';
import { mount } from '@vue/test-utils';
import { describe, expect, it, vi } from 'vitest';
import type { LocationQuery, LocationQueryRaw, RouteLocationNormalizedLoaded, Router } from 'vue-router';
import { getResourceAuthFilterOptions } from '@/utils/auth-config';
import {
  applySearchValueToFilterState,
  applyTableFilterChangeToFilterState,
  applyTableSortToFilterState,
  buildNextRouteQuery,
  createEmptyResourceFilterState,
  filterStateToApiQuery,
  filterStateToSearchValue,
  filterStateToTableFilterValue,
  filterStateToTableSort,
  parseRouteQueryToFilterState,
  useResourceFilters,
} from '../use-resource-filters';

const t = (key: string) => key;

interface IHarnessOptions {
  gatewayId?: number
  routeGatewayId?: string
  initialQuery?: LocationQuery
  isResourceAuthV2?: boolean
  isGatewayReady?: boolean
  asyncRouterReplace?: boolean
}

const createFilterHarness = (options: IHarnessOptions = {}) => {
  const gatewayId = ref(options.gatewayId ?? 632);
  const isResourceAuthV2 = ref(options.isResourceAuthV2 ?? true);
  const isGatewayReady = ref(options.isGatewayReady ?? true);
  const route = reactive({
    params: { id: options.routeGatewayId ?? String(options.gatewayId ?? 632) },
    query: { ...options.initialQuery } as LocationQuery,
  });

  const replaceCalls: LocationQueryRaw[] = [];
  const applyRouteQuery = (nextQuery: LocationQueryRaw) => {
    const cleaned: LocationQuery = {};
    Object.entries(nextQuery).forEach(([key, value]) => {
      if (value !== undefined) {
        cleaned[key] = value as LocationQuery[string];
      }
    });
    route.query = cleaned;
  };

  const router = {
    replace: vi.fn((location: { query?: LocationQueryRaw }) => {
      const nextQuery = location.query ?? {};
      replaceCalls.push({ ...nextQuery });
      if (options.asyncRouterReplace) {
        return Promise.resolve().then(() => {
          applyRouteQuery(nextQuery);
        });
      }
      applyRouteQuery(nextQuery);
      return Promise.resolve();
    }),
  } as unknown as Router;

  const onQueryChange = vi.fn();
  let api!: ReturnType<typeof useResourceFilters>;

  const Host = defineComponent({
    setup() {
      api = useResourceFilters({
        gatewayId: () => gatewayId.value,
        isResourceAuthV2: () => isResourceAuthV2.value,
        isGatewayReady: () => isGatewayReady.value,
        route: route as unknown as RouteLocationNormalizedLoaded,
        router,
        t,
        onQueryChange,
      });
      return () => h('div');
    },
  });

  const wrapper = mount(Host);

  return {
    api,
    gatewayId,
    isResourceAuthV2,
    isGatewayReady,
    route,
    router,
    replaceCalls,
    onQueryChange,
    wrapper,
  };
};

describe('views/resource-management/settings/use-resource-filters', () => {
  describe('纯函数转换与校验', () => {
    it('parseRouteQueryToFilterState 准确解析托管字段、按 V2 门控清洗 auth_type 并忽略编辑页 kind', () => {
      const parsedV2 = parseRouteQueryToFilterState(
        {
          keyword: '  hello ',
          name: 'get_user',
          path: '/users',
          method: 'GET, POST , GET',
          auth_type: 'personal,invalid,public,personal',
          backend_name: 'default',
          backend_id: '12',
          kind: 'standard',
        },
        { isResourceAuthV2: true },
      );

      expect(parsedV2).toEqual({
        keyword: 'hello',
        name: 'get_user',
        path: '/users',
        method: ['GET', 'POST'],
        auth_type: ['personal', 'public'],
        backend_name: 'default',
        backend_id: '12',
      });

      const parsedV1 = parseRouteQueryToFilterState(
        {
          auth_type: 'personal,public',
          method: ['GET', 'DELETE'],
        },
        { isResourceAuthV2: false },
      );
      expect(parsedV1.auth_type).toEqual([]);
      expect(parsedV1.method).toEqual(['GET', 'DELETE']);
    });

    it('buildNextRouteQuery 保留非托管字段、无变化返回 null，并在 syncAuthType=false 时不抹除 auth_type', () => {
      const baseState = {
        ...createEmptyResourceFilterState(),
        name: 'get_user',
        auth_type: ['none' as const],
      };

      expect(
        buildNextRouteQuery(
          {
            name: 'get_user',
            auth_type: 'none',
            kind: 'standard',
          },
          baseState,
          { syncAuthType: true },
        ),
      ).toBeNull();

      expect(
        buildNextRouteQuery(
          {
            name: 'get_user',
            method: 'GET',
            kind: 'standard',
          },
          baseState,
          { syncAuthType: true },
        ),
      ).toEqual({
        name: 'get_user',
        auth_type: 'none',
        kind: 'standard',
      });

      // 网关详情尚未就绪时（syncAuthType=false），不清除 URL 上原本携带的 auth_type
      expect(
        buildNextRouteQuery(
          { auth_type: 'personal' },
          createEmptyResourceFilterState(),
          { syncAuthType: false },
        ),
      ).toBeNull();
    });

    it('applySearchValueToFilterState 保留仅表头字段并安全处理空 values 与单项删除', () => {
      const current = {
        ...createEmptyResourceFilterState(),
        name: 'old_name',
        backend_id: '99',
        label_ids: [1, 2],
        kind: 'ai',
        order_by: '-updated_time' as const,
      };

      // 删除 backend_id，仅保留 name，同时混入空 values 项不应抛错
      const updated = applySearchValueToFilterState(
        current,
        [
          {
            id: 'name',
            name: '资源名称',
            values: [{
              id: 'new_name',
              name: 'new_name',
            }],
          },
          {
            id: 'path',
            name: '前端请求路径',
            values: [],
          },
          {
            id: 'auth_type',
            name: '认证方式',
            values: [
              {
                id: 'personal',
                name: '个人令牌',
              },
              {
                id: 'invalid',
                name: '无效项',
              },
            ],
          },
        ],
        { isResourceAuthV2: true },
      );

      expect(updated).toEqual({
        keyword: '',
        name: 'new_name',
        path: '',
        method: [],
        auth_type: ['personal'],
        backend_name: '',
        backend_id: '',
        label_ids: [1, 2],
        kind: 'ai',
        order_by: '-updated_time',
      });

      // 清空搜索框后仍完整保留 label_ids、kind、order_by
      const cleared = applySearchValueToFilterState(updated, [], { isResourceAuthV2: true });
      expect(cleared.label_ids).toEqual([1, 2]);
      expect(cleared.kind).toBe('ai');
      expect(cleared.order_by).toBe('-updated_time');
      expect(cleared.name).toBe('');
      expect(cleared.auth_type).toEqual([]);
    });

    it('表头筛选、排序与 API 查询参数的映射与派生准确一致', () => {
      let state = applyTableFilterChangeToFilterState(
        createEmptyResourceFilterState(),
        {
          auth_config: ['personal', 'none'],
          method: ['GET', 'POST'],
          label_ids: [3, '5'],
          kind: 'ai',
        },
        { isResourceAuthV2: true },
      );
      state = applyTableSortToFilterState(state, {
        sortBy: 'updated_time',
        descending: true,
      });

      expect(filterStateToTableFilterValue(state, { isResourceAuthV2: true })).toEqual({
        auth_config: ['personal', 'none'],
        method: ['GET', 'POST'],
        label_ids: [3, 5],
        kind: 'ai',
      });
      expect(filterStateToTableSort(state)).toEqual({
        sortBy: 'updated_time',
        descending: true,
      });
      expect(filterStateToApiQuery(state, { isResourceAuthV2: true })).toEqual({
        auth_type: 'personal,none',
        method: 'GET,POST',
        label_ids: '3,5',
        kind: 'ai',
        order_by: '-updated_time',
      });

      const searchItems = filterStateToSearchValue(state, {
        t,
        authOptions: getResourceAuthFilterOptions(t),
        isResourceAuthV2: true,
      });
      expect(searchItems.find(item => item.id === 'auth_type')?.values).toEqual([
        {
          id: 'personal',
          name: '用户认证-个人令牌',
        },
        {
          id: 'none',
          name: '不认证',
        },
      ]);
    });
  });

  describe('useResourceFilters 组合式行为', () => {
    it('表头筛选 auth_config 与 method 均只触发一次请求，且正确联动搜索框与 URL query', async () => {
      const { api, onQueryChange, replaceCalls, wrapper } = createFilterHarness({ asyncRouterReplace: true });

      api.startInitialFetch();
      expect(onQueryChange).toHaveBeenCalledTimes(1);
      expect(onQueryChange).toHaveBeenLastCalledWith({});

      onQueryChange.mockClear();
      replaceCalls.length = 0;

      // 表头勾选「不认证」
      api.handleFilterChange({ auth_config: ['none'] });
      await nextTick();
      await nextTick();

      expect(onQueryChange).toHaveBeenCalledTimes(1);
      expect(onQueryChange).toHaveBeenLastCalledWith({ auth_type: 'none' });
      expect(replaceCalls).toEqual([{ auth_type: 'none' }]);
      expect(api.tableFilterValue.value).toEqual({ auth_config: ['none'] });
      expect(api.searchValue.value).toEqual([
        {
          id: 'auth_type',
          name: '认证方式',
          values: [{
            id: 'none',
            name: '不认证',
          }],
        },
      ]);

      // 保持 auth_config 不变，新增仅表头筛选 label_ids，也只发一次请求且不触发多余 router.replace
      onQueryChange.mockClear();
      replaceCalls.length = 0;
      api.handleFilterChange({
        auth_config: ['none'],
        label_ids: [10],
      });
      await nextTick();
      await nextTick();

      expect(onQueryChange).toHaveBeenCalledTimes(1);
      expect(onQueryChange).toHaveBeenLastCalledWith({
        auth_type: 'none',
        label_ids: '10',
      });
      expect(replaceCalls).toEqual([]);

      // 在已有筛选下重置 auth_config，只发一次请求并清理 URL 中的 auth_type
      onQueryChange.mockClear();
      replaceCalls.length = 0;
      api.handleFilterChange({
        auth_config: [],
        label_ids: [10],
      });
      await nextTick();
      await nextTick();

      expect(onQueryChange).toHaveBeenCalledTimes(1);
      expect(onQueryChange).toHaveBeenLastCalledWith({ label_ids: '10' });
      expect(replaceCalls).toEqual([{}]);
      expect(api.searchValue.value).toEqual([]);

      // 对已为空的 auth_config 再次重置不发多余请求
      onQueryChange.mockClear();
      api.handleFilterChange({
        auth_config: [],
        label_ids: [10],
      });
      await nextTick();
      expect(onQueryChange).not.toHaveBeenCalled();

      wrapper.unmount();
    });

    it('在搜索框删除单个筛选条件（含 backend_id 与 method）时立刻清除对应 URL 参数且不再复活', async () => {
      const { api, onQueryChange, route, wrapper } = createFilterHarness({
        initialQuery: {
          name: 'users',
          method: 'GET',
          backend_id: '5',
          auth_type: 'personal',
        },
      });

      api.startInitialFetch();
      expect(onQueryChange).toHaveBeenCalledTimes(1);
      expect(onQueryChange).toHaveBeenLastCalledWith({
        name: 'users',
        method: 'GET',
        backend_id: 5,
        auth_type: 'personal',
      });

      onQueryChange.mockClear();
      // 删除 backend_id 和 method，仅保留 name 和 auth_type
      api.searchValue.value = api.searchValue.value.filter(
        item => item.id !== 'backend_id' && item.id !== 'method',
      );
      await nextTick();

      expect(onQueryChange).toHaveBeenCalledTimes(1);
      expect(onQueryChange).toHaveBeenLastCalledWith({
        name: 'users',
        auth_type: 'personal',
      });
      expect(route.query).toEqual({
        name: 'users',
        auth_type: 'personal',
      });

      wrapper.unmount();
    });

    it('清空筛选条件 handleClearQueries 同步清空表头、搜索框、排序与 URL，且只发一次请求', async () => {
      const { api, onQueryChange, route, wrapper } = createFilterHarness({
        initialQuery: { auth_type: 'public' },
      });

      api.startInitialFetch();
      api.handleFilterChange({
        auth_config: ['public'],
        label_ids: [1],
        kind: 'standard',
      });
      api.handleSortChange({
        sortBy: 'updated_time',
        descending: false,
      });
      await nextTick();

      onQueryChange.mockClear();
      api.handleClearQueries();
      await nextTick();

      expect(onQueryChange).toHaveBeenCalledTimes(1);
      expect(onQueryChange).toHaveBeenLastCalledWith({});
      expect(route.query).toEqual({});
      expect(api.searchValue.value).toEqual([]);
      expect(api.tableFilterValue.value).toEqual({});
      expect(api.tableSort.value).toBeUndefined();

      wrapper.unmount();
    });

    it('支持浏览器前进/后退更新 route.query、清洗非法 auth_type，以及 V2 详情异步就绪回填', async () => {
      // 场景 1：V2 网关详情尚未就绪时携带 ?auth_type=personal,invalid 进入
      const harness = createFilterHarness({
        initialQuery: { auth_type: 'personal,invalid' },
        isResourceAuthV2: false,
        isGatewayReady: false,
      });

      // 未就绪时不破坏 URL 上的 auth_type，也不把它发给后端
      expect(harness.route.query.auth_type).toBe('personal,invalid');
      harness.api.startInitialFetch();
      expect(harness.onQueryChange).toHaveBeenLastCalledWith({});

      // 网关详情就绪并确认是 V2 后，自动回填并清洗非法值
      harness.onQueryChange.mockClear();
      harness.isGatewayReady.value = true;
      harness.isResourceAuthV2.value = true;
      await nextTick();

      expect(harness.onQueryChange).toHaveBeenCalledTimes(1);
      expect(harness.onQueryChange).toHaveBeenLastCalledWith({ auth_type: 'personal' });
      expect(harness.route.query.auth_type).toBe('personal');
      expect(harness.api.searchData.value.some(item => item.id === 'auth_type')).toBe(true);

      // 模拟浏览器后退到 ?auth_type=oauth&name=demo
      harness.onQueryChange.mockClear();
      harness.route.query = {
        auth_type: 'oauth',
        name: 'demo',
      };
      await nextTick();

      expect(harness.onQueryChange).toHaveBeenCalledTimes(1);
      expect(harness.onQueryChange).toHaveBeenLastCalledWith({
        auth_type: 'oauth',
        name: 'demo',
      });
      expect(harness.api.tableFilterValue.value).toEqual({ auth_config: ['oauth'] });

      // 模拟浏览器再后退到无参数状态，搜索框和表头状态均同步清空
      harness.onQueryChange.mockClear();
      harness.route.query = {};
      await nextTick();

      expect(harness.onQueryChange).toHaveBeenCalledTimes(1);
      expect(harness.onQueryChange).toHaveBeenLastCalledWith({});
      expect(harness.api.searchValue.value).toEqual([]);
      expect(harness.api.tableFilterValue.value).toEqual({});

      harness.wrapper.unmount();
    });

    it('网关切换过渡期跳过旧 query 同步，参数对齐后自动清理旧网关残留 query', async () => {
      // 组件已按新网关 900 重建，但 route.params.id 仍处于旧网关 632
      const { route, router, api, wrapper } = createFilterHarness({
        gatewayId: 900,
        routeGatewayId: '632',
        initialQuery: { name: 'old_gateway_resource' },
      });

      expect(api.apiQuery.value).toEqual({});
      expect(router.replace).not.toHaveBeenCalled();

      // 路由导航完成，params.id 对齐到 900
      route.params.id = '900';
      route.query = { name: 'old_gateway_resource' };
      await nextTick();

      expect(router.replace).toHaveBeenCalledWith({ query: {} });
      expect(route.query).toEqual({});
      expect(api.apiQuery.value).toEqual({});

      wrapper.unmount();
    });
  });
});
