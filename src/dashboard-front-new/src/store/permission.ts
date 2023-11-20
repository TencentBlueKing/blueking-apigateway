import { defineStore } from 'pinia';

export const usePermission = defineStore('permission', {
  state: () => ({
    // 待审批的数量
    count: 0,
  }),
  actions: {
    setCount(count: number) {
      this.count = count;
    },
  },
});
