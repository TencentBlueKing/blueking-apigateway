import {
  ref,
  onMounted,
} from 'vue';
import { useRoute } from 'vue-router';
import { IPagination } from '@/types';


export function useQueryList(apiMethod: Function, filterData?: any) {
  const route = useRoute();
  console.log('filterData', filterData);
  const initPagination: IPagination = {
    offset: 0,
    limit: 10,
    count: 0,
  };
  const pagination = ref<IPagination>(initPagination);
  // 查询列表相关状态
  const isLoading = ref(false);

  const tableData = ref([]);

  const apigwId = route.params.id;

  const getList = async () => {
    const method = apiMethod;
    console.log('apiMethod', apiMethod, apigwId);
    const res = await method(apigwId, { offset: 0, limit: 10 });
    tableData.value = res.results;
    pagination.value.count = res.count;
  };

  // 页码变化发生的事件
  const handlePageChange = (current: number) => {
    pagination.value.offset = current;
    getList();
  };

  // 条数变化发生的事件
  const handlePageSizeChange = (limit: number) => {
    pagination.value.limit = limit;
    getList();
  };

  onMounted(getList);


  return {
    tableData,
    pagination,
    isLoading,
    handlePageChange,
    handlePageSizeChange,
    getList,
  };
}
