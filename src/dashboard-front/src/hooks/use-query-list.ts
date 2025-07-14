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
/*
 * 列表分页、查询hooks
 * 需要传入获取列表的方法名apiMethod、当前列表的过滤条件filterData
 */
import { useGateway } from '@/stores';
import {
  sortBy,
  sortedUniq,
} from 'lodash-es';

// 分页接口
export interface IPagination {
  // 是否使用小型分页样式
  small?: boolean
  // 数据偏移量
  offset: number
  // 每页显示的数据条数
  limit: number
  // 数据总条数;
  count: number
  // 是否存在异常
  abnormal?: boolean
  // 可选的每页显示条数列表
  limitList?: number[]
  // 当前页码
  current?: number
}

export function useQueryList<T>({
  apiMethod,
  filterData,
  id,
  filterNoResetPage = false,
  initialPagination = {},
  immediate = true,
}: {
  apiMethod: (...args: any[]) => Promise<unknown>
  filterData?: Ref<Record<string, any>>
  id?: number
  filterNoResetPage?: boolean
  initialPagination: Partial<IPagination>
  immediate?: boolean
}) {
  const { apigwId } = useGateway();

  const initPagination: IPagination = {
    offset: 0,
    limit: 10,
    count: 0,
    small: false,
    // 获取接口是否异常
    abnormal: false,
    // 每页页数选项，这个也是 table 组件的默认值
    limitList: [10, 20, 50, 100],
    // 当前页码
    current: 1,
    ...initialPagination,
  };
  initPagination.limitList = sortedUniq(sortBy(initPagination.limitList));

  const pagination = ref<IPagination>({ ...initPagination });
  const isLoading = ref(false);
  const tableData = ref<T[]>([]);
  const getMethod = ref<Ref | null>(null);
  // 获取列表数据的方法
  const getList = async (fetchMethod = apiMethod, needLoading = true) => {
    isLoading.value = needLoading;
    getMethod.value = fetchMethod;
    // 列表参数
    const paramsData = {
      offset: pagination.value.offset,
      limit: pagination.value.limit,
      ...filterData?.value,
    };
    try {
      const res = id
        ? await getMethod.value(apigwId, id, paramsData)
        : await getMethod.value(apigwId, paramsData);
      tableData.value = res.results || res.data;
      pagination.value = Object.assign(pagination.value, {
        count: res.count || 0,
        abnormal: false,
      });
    }
    catch {
      pagination.value.abnormal = true;
    }
    finally {
      // 延迟loading展示时间，实现对空状态占位符
      setTimeout(() => {
        isLoading.value = false;
      }, 500);
    }
  };

  // 页码变化发生的事件
  const handlePageChange = (current: number) => {
    Object.assign(pagination.value, {
      current,
      offset: pagination.value.limit * (current - 1),
    });
    fetchList();
  };

  // 条数变化发生的事件
  const handlePageSizeChange = (limit: number) => {
    Object.assign(pagination.value, {
      limit,
      offset: limit * ((pagination?.value.current ?? 1) - 1),
    });
    // 页码没变化的情况下需要手动请求一次数据
    if (pagination.value.offset <= pagination.value.count) {
      fetchList();
    }
  };

  // 监听筛选条件的变化
  watch(
    () => filterData,
    async () => {
      if (!filterNoResetPage) {
        pagination.value = { ...initPagination };
      }
      await fetchList();
    },
    { deep: true },
  );

  const fetchList = async () => {
    if (getMethod.value) {
      await getList(getMethod.value);
    }
    else {
      await getList();
    }
  };

  onMounted(() => {
    if (immediate) {
      getList();
    }
  });

  return {
    tableData,
    pagination,
    isLoading,
    handlePageChange,
    handlePageSizeChange,
    getList,
    fetchList,
    getMethod,
  };
}
