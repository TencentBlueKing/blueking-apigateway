import { defineStore } from 'pinia';

export const useStage = defineStore('stage', {
  state: () => ({
    stageList: [],
    curStageData: {
      id: null,
      name: '',
    },
    curStageId: -1,
    stageMainLoading: false,
  }),
  getters: {
    defaultStage(state) {
      return state.stageList[0] || {};
    },
    realStageMainLoading(state) {
      return state.stageMainLoading;
    },
  },
  actions: {
    setStageList(data: any[]) {
      this.stageList = data;
    },
    setStageMainLoading(loading: boolean) {
      this.stageMainLoading = loading;
    },
  },
});
