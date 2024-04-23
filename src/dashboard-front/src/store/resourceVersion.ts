import { defineStore } from 'pinia';

export const useResourceVersion = defineStore('resourceVersion', {
  state: () => ({
    tabActive: 'edition',
    resourceFilter: {},
    pageStatus: {
      isDetail: false,
      isShowLeft: true,
    },
  }),
  getters: {
    getTabActive(state) {
      return state.tabActive;
    },
    getResourceFilter(state) {
      return state.resourceFilter;
    },
    getPageStatus(state) {
      return state.pageStatus;
    },
  },
  actions: {
    setTabActive(key: string) {
      this.tabActive = key;
    },
    setResourceFilter(value: any) {
      this.resourceFilter = value;
    },
    setPageStatus(value: any) {
      this.pageStatus = value;
    },
  },
});
