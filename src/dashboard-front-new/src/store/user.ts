import { defineStore } from 'pinia';
import type { IUser } from '@/types/store';

export const useUser = defineStore('user', {
  state: () => ({
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
    setFeatureFlags(data: any) {
      this.featureFlags = data;
    },
  },
});
