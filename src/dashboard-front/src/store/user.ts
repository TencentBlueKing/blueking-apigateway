import { defineStore } from 'pinia';
import type { IUser, IFeatureFlags } from '@/types/store';

export const useUser = defineStore('user', {
  state: (): {
    user: IUser,
    featureFlags: IFeatureFlags,
  } => ({
    user: {
      username: '',
      avatar_url: '',
    },
    featureFlags: {},
  }),
  actions: {
    setUser(user: IUser) {
      this.user = user;
    },
    setFeatureFlags(data: IFeatureFlags) {
      console.log(data, '调用了配置接口');
      this.featureFlags = data;
    },
  },
});
