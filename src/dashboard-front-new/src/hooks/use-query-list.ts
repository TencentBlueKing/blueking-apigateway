/*
 * 列表分页、查询hooks
 * 需要传入获取列表的方法名apiMethod、当前列表的过滤条件filterData
 */

import {
  ref,
  onMounted,
  watch,
} from 'vue';
import { IPagination } from '@/types';
import { useCommon } from '@/store';
const getMethod = ref<any>(null);

export function useQueryList(apiMethod: Function, filterData?: any, id?: number) {
  const common = useCommon();
  const { apigwId } = common;
  const initPagination: IPagination = {
    offset: 0,
    limit: 10,
    count: 0,
  };

  const pagination = ref<IPagination>({ ...initPagination });
  const isLoading = ref(false);
  const tableData = ref([]);

  // 获取列表数据的方法
  const getList = async (fetchMethod = apiMethod) => {
    getMethod.value = fetchMethod;
    const method = fetchMethod;
    isLoading.value = true;
    // 列表参数
    const paramsData = {
      offset: pagination.value.offset,
      limit: pagination.value.limit,
      ...filterData.value,
    };
    try {
      const res = id ? await method(apigwId, id, paramsData) : await method(apigwId, paramsData);
      tableData.value = res.results || res.data;
      pagination.value.count = res.count;
    } catch (error) {

    } finally {
      isLoading.value = false;
    }
  };

  // 页码变化发生的事件
  const handlePageChange = (current: number) => {
    pagination.value.offset = pagination.value.limit * (current - 1);
    fetchList();
  };

  // 条数变化发生的事件
  const handlePageSizeChange = (limit: number) => {
    pagination.value.limit = limit;
    fetchList();
  };

  // 监听筛选条件的变化
  watch(
    () => filterData,
    () => {
      pagination.value = { ...initPagination };
      fetchList();
    },
    { deep: true },
  );

  const fetchList = () => {
    if (getMethod.value) {
      getList(getMethod.value);
    } else {
      getList();
    }
  };

  onMounted(() => {
    getList();
  });


  return {
    tableData,
    pagination,
    isLoading,
    handlePageChange,
    handlePageSizeChange,
    getList,
    fetchList,
  };
}
