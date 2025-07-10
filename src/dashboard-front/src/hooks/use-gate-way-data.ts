// 获取网关列表的hooks, 多个地方用到
import { getGatewayList } from '@/services/source/gateway';
import type { IPagination } from '@/types/common';
import type { IApiGateway } from '@/types/gateway';

// 初始化分页信息
const initPagination: IPagination = {
  offset: 0,
  limit: 10000,
  count: 0,
};
const pagination = ref<IPagination>(initPagination);
const dataList = ref<IApiGateway[]>([]);

// 自定义hook，用于获取API列表
export function useGatewaysList(filter: Ref) {
  // 异步获取网关列表数据
  const getGatewaysListData = async () => {
    try {
      const params = {
        limit: pagination.value.limit,
        offset: pagination.value.limit * pagination.value.offset,
        ...filter.value,
      };
      if (['all'].includes(params.kind)) {
        params.kind = '';
      }
      const res = await getGatewayList(params);
      dataList.value = res.results;
      return dataList.value;
    }
    catch (error) {
      console.error(error);
    }
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
