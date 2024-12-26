import { defineStore } from 'pinia';
import type { IUser, IFeatureFlags } from '@/types/store';

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
