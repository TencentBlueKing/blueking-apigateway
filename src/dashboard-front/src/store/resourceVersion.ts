import { defineStore } from 'pinia';

export const useResourceVersion = defineStore('resourceVersion', {
  state: () => ({
    tabActive: 'edition',
    resourceFilter: {},
  }),
  getters: {
    getTabActive(state) {
      return state.tabActive;
    },
    getResourceFilter(state) {
      return state.resourceFilter;
    },
  },
  actions: {
    setTabActive(key: string) {
      this.tabActive = key;
    },
    setResourceFilter(value: any) {
      this.resourceFilter = value;
    },
  },
});
