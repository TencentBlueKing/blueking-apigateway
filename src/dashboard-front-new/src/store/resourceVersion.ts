import { defineStore } from 'pinia';

export const useResourceVersion = defineStore('resourceVersion', {
  state: () => ({
    tabActive: 'edition',
  }),
  getters: {
    getTabActive(state) {
      return state.tabActive;
    },
  },
  actions: {
    setTabActive(key: string) {
      this.tabActive = key;
    },
  },
});
