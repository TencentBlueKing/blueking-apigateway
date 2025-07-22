import { defineStore } from 'pinia';

// 定义一个名为useResourceVersion的Pinia store
export const useResourceVersion = defineStore('useResourceVersion', {
  // state定义了store的初始状态
  state: () => ({
    tabActive: 'edition', // 当前激活的标签页
    resourceFilter: {}, // 资源过滤器
    pageStatus: {
      isDetail: false, // 是否显示详情
      isShowLeft: true, // 是否显示左侧栏
    },
  }),
  // getters定义了获取state的方法
  getters: {
    // 获取当前激活的标签页
    getTabActive(state) {
      return state.tabActive;
    },
    // 获取资源过滤器
    getResourceFilter(state) {
      return state.resourceFilter;
    },
    // 获取页面状态
    getPageStatus(state) {
      return state.pageStatus;
    },
  },
  // actions定义了修改state的方法
  actions: {
    // 设置当前激活的标签页
    setTabActive(key: string) {
      this.tabActive = key;
    },
    // 设置资源过滤器
    setResourceFilter(value: any) {
      this.resourceFilter = value;
    },
    // 设置页面状态
    setPageStatus(value: any) {
      this.pageStatus = value;
    },
  },
});
