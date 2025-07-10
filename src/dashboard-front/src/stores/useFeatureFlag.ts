import { defineStore } from 'pinia';

import { getFeatureFlags } from '@/services/source/basic';

type FlagType = Awaited<ReturnType<typeof getFeatureFlags>>;

export const useFeatureFlag = defineStore('useFeatureFlag', {
  state: (): Record<string, FlagType> => ({
    flags: {
      ALLOW_CREATE_APPCHAT: false,
      ALLOW_UPLOAD_SDK_TO_REPOSITORY: false,
      ENABLE_AI_COMPLETION: false,
      ENABLE_BK_NOTICE: false,
      ENABLE_MONITOR: false,
      ENABLE_MULTI_TENANT_MODE: false,
      ENABLE_RUN_DATA: false,
      ENABLE_RUN_DATA_METRICS: false,
      ENABLE_SDK: false,
      GATEWAY_APP_BINDING_ENABLED: false,
      MENU_ITEM_ESB_API: false,
      MENU_ITEM_ESB_API_DOC: false,
      SYNC_ESB_TO_APIGW_ENABLED: false,
    },
  }),
  getters: {
    // 是否开启了多租户模式
    isTenantMode: state => !!state.flags?.ENABLE_MULTI_TENANT_MODE,
    // 是否启用了 ai 问答功能
    isAIEnabled: state => state.flags?.ENABLE_AI_COMPLETION,
  },
  actions: {
    async fetchFlags() {
      this.info = await getFeatureFlags({
        limit: 10000,
        offset: 0,
      });
    },
  },
});
