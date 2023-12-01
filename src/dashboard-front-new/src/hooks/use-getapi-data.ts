// 获取网关列表的hooks, 多个地方用到
import { ref, watch } from 'vue';
import { getGatewaysList } from '@/http';
import { IPagination } from '@/types';

const initPagination: IPagination = {
  offset: 0,
  limit: 100,
  count: 0,
};
const pagination = ref<IPagination>(initPagination);

export const useGetApiList = (filter: any) => {
  const getGatewaysListData = async () => {
    try {
      const parmas = {
        limit: pagination.value.limit,
        offset: pagination.value.limit * pagination.value.offset,
        ...filter.value,
      };
      const res = await getGatewaysList(parmas);
      return res.results;
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
  };
};
