/*
 * 列表分页、查询hooks
 * 需要传入获取列表的方法名apiMethod、当前列表的过滤条件filterData
 */

import {
  onMounted,
  ref,
  Ref,
  watch,
} from 'vue';
import { IPagination } from '@/types';
import { useCommon } from '@/store';
import {
  sortBy,
  sortedUniq,
} from 'lodash';

export function useQueryList<T>(
  apiMethod: (...args: any[]) => Promise<unknown>,
  filterData?: Ref<Record<string, any>>,
  id?: number,
  filterNoResetPage?: boolean,
  initialPagination: Partial<IPagination> = {},
  immediate = true,
) {
  const common = useCommon();
  const { apigwId } = common;
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
  const getMethod = ref<any>(null);

  // 获取列表数据的方法
  const getList = async (fetchMethod = apiMethod, needLoading = true) => {
    getMethod.value = fetchMethod;
    // const method = fetchMethod;
    isLoading.value = needLoading;
    // 列表参数
    const paramsData = {
      offset: pagination.value.offset,
      limit: pagination.value.limit,
      ...filterData.value,
    };
    try {
      // const res = id ? await method(apigwId, id, paramsData) : await method(apigwId, paramsData);
      const res = id ? await getMethod.value(apigwId, id, paramsData) : await getMethod.value(apigwId, paramsData);
      tableData.value = res.results || res.data;
      pagination.value = Object.assign(pagination.value, {
        count: res.count || 0,
        abnormal: false,
      });
    } catch (error) {
      pagination.value.abnormal = true;
    } finally {
      isLoading.value = false;
    }
  };

  // 页码变化发生的事件
  const handlePageChange = (current: number) => {
    pagination.value.offset = pagination.value.limit * (current - 1);
    pagination.value.current = current;
    fetchList();
  };

  // 条数变化发生的事件
  const handlePageSizeChange = (limit: number) => {
    pagination.value.limit = limit;
    pagination.value.offset = limit * (pagination.value.current - 1);

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
    } else {
      await getList();
    }
  };

  onMounted(async () => {
    if (immediate) {
      await getList();
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
