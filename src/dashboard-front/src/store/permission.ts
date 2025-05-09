import { defineStore } from 'pinia';

// 定义一个名为 'permission' 的 store
export const usePermission = defineStore('permission', {
  // state 定义了 store 的状态
  state: () => ({
    // 待审批的数量
    count: 0,
  }),
  // actions 定义了可以修改状态的方法
  actions: {
    /**
     * 设置待审批的数量
     * @param {number} count - 新的待审批数量
     */
    setCount(count: number) {
      this.count = count;
    },
  },
});
