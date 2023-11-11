// 获取网关列表的hooks, 多个地方用到
import { ref } from 'vue';
import { getGatewaysList } from '@/http';
import { IPagination } from '@/types';

const initPagination: IPagination = {
  offset: 0,
  limit: 100,
  count: 0,
};
const pagination = ref<IPagination>(initPagination);

export const useGetApiList = () => {
  const getGatewaysListData = async () => {
    try {
      const res = await getGatewaysList({
        limit: pagination.value.limit,
        offset: pagination.value.limit * pagination.value.offset,
      });
      return res.results;
    } catch (error) {}
  };

  return {
    getGatewaysListData,
  };
};
