import { ref } from 'vue';
import { getGatewaysList } from '@/http';
import { IPagination } from '@/types';

const initPagination: IPagination = {
  offset: 0,
  limit: 100,
  count: 0,
};
const pagination = ref<IPagination>(initPagination);

export function useGetApiList() {
  async function getGatewaysListData() {
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
}
