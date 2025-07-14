import { defineStore } from 'pinia';

import { getEnv } from '@/services/source/basic';

export const useEnv = defineStore('useEnv', {
  state: () => ({
    env: {
      BK_API_RESOURCE_URL_TMPL: '',
      BK_APP_CODE: '',
      BK_COMPONENT_API_URL: '',
      BK_DASHBOARD_CSRF_COOKIE_NAME: '',
      BK_DASHBOARD_FE_URL: '',
      BK_DASHBOARD_URL: '',
      BK_DEFAULT_TEST_APP_CODE: '',
      BK_PAAS_APP_REPO_URL_TMPL: '',
      EDITION: '',
    },
  }),
  actions: {
    /**
     * 查询环境变量信息
     */
    fetchEnv() {
      getEnv().then((result) => {
        Object.assign(this.env, result);
      });
    },
  },
});
