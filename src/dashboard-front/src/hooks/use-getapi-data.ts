// 获取网关列表的hooks, 多个地方用到
import {
  ref,
  watch,
} from 'vue';
import { getGatewaysList } from '@/http';
import { IPagination } from '@/types';

// 初始化分页信息
const initPagination: IPagination = {
  offset: 0,
  limit: 10000,
  count: 0,
};
const pagination = ref<IPagination>(initPagination);
const dataList = ref<any[]>([]);

// 自定义hook，用于获取API列表
export const useGetApiList = (filter: any) => {
  // 异步获取网关列表数据
  const getGatewaysListData = async () => {
    try {
      const parmas = {
        limit: pagination.value.limit,
        offset: pagination.value.limit * pagination.value.offset,
        ...filter.value,
      };
      if (parmas.kind === 'all') {
        parmas.kind = '';
      }
      const res = await getGatewaysList(parmas);
      dataList.value = res.results;
      return dataList.value;
    } catch (error) {}
  };

  // 监听输入框改变
  watch(
    () => filter,
    () => {
      getGatewaysListData();
    },
    { deep: true },
  );

  return {
    getGatewaysListData,
    dataList,
    pagination,
  };
};
