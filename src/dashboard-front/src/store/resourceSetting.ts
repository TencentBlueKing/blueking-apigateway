import { defineStore } from 'pinia';

interface IPagination {
  current: number;
  offset: number;
}

export const useResourceSetting = defineStore('resourceSetting', {
  state: () => ({
    previousPagination: null as IPagination | null,
  }),
  actions: {
    setPagination(pagination: IPagination) {
      this.previousPagination = pagination;
    },
  },
});
