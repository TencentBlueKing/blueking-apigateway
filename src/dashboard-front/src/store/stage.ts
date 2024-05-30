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
    notUpdatedStages: [], // 当前网关下未更新的环境列表
    exist2: false, // 当前网关下是否有schema_version = 2.0 的资源
  }),
  getters: {
    defaultStage(state) {
      return state.stageList[0] || {};
    },
    realStageMainLoading(state) {
      return state.stageMainLoading;
    },
    getNotUpdatedStages(state) {
      return state.notUpdatedStages;
    },
    getExist2(state) {
      return state.exist2;
    },
  },
  actions: {
    setStageList(data: any[]) {
      this.stageList = data;
    },
    setStageMainLoading(loading: boolean) {
      this.stageMainLoading = loading;
    },
    setNotUpdatedStages(data: any[]) {
      this.notUpdatedStages = data;
    },
    setExist2(data: boolean) {
      this.exist2 = data;
    },
  },
});
