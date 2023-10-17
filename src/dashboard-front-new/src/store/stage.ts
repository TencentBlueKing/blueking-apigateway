import { defineStore } from 'pinia';

export const useStage = defineStore('stage', {
  state: () => ({
    stageList: [],
    curStageData: {
      id: null,
    },
    curStageId: 0,
  }),
  getters: {
    defaultStage(state) {
      return state.stageList[0] || {};
    },
  },
  actions: {
    setStageList(data: any[]) {
      this.stageList = data;
    },
  },
});
