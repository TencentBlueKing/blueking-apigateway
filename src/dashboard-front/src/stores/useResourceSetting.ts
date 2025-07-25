import { defineStore } from 'pinia';

// 定义分页接口
interface IPagination {
  current: number // 当前页码
  offset: number // 偏移量
}

// 定义一个名为 useResourceSetting 的 store
export const useResourceSetting = defineStore('useResourceSetting', {
  state: () => ({
    // 存储上一次的分页信息
    previousPagination: null as IPagination | null,
  }),
  actions: {
    // 设置分页信息
    setPagination(pagination: IPagination) {
      this.previousPagination = pagination;
    },
  },
});
