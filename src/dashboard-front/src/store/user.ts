import { defineStore } from 'pinia';
import type {
  IFeatureFlags,
  IUser,
} from '@/types/store';

const {
  // BK_API_URL_TMPL,
  BK_USER_WEB_API_URL,
} = window;

export const useUser = defineStore('user', {
  state: (): {
    user: IUser,
    featureFlags: IFeatureFlags,
  } => ({
    user: {
      username: '',
      display_name: '',
      avatar_url: '',
      tenant_id: '',
    },
    featureFlags: {},
  }),
  getters: {
    // apiBaseUrl: () => `${BK_API_URL_TMPL}/bk-user-web/prod`,
    apiBaseUrl: () => BK_USER_WEB_API_URL,
  },
  actions: {
    setUser(user: IUser) {
      this.user = user;
    },
    setFeatureFlags(data: IFeatureFlags) {
      this.featureFlags = data;
      // this.featureFlags.ENABLE_MULTI_TENANT_MODE = true;
    },
  },
});
