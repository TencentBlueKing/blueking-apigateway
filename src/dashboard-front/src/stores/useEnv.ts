import { defineStore } from 'pinia';

import { getEnv } from '@/services/source/basic';

export const useEnv = defineStore('useEnv', {
  state: () => ({
    app_code: '',
    bk_login_url: '',
    guide_doc_url: '',
    user_selector_api_url: '',
  }),
  actions: {
    /**
     * 查询环境变量信息
     */
    fetchEnviron() {
      getEnv().then((result) => {
        Object.assign(this, result);
      });
    },
  },
});
