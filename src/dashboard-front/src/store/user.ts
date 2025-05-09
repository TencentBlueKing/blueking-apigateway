import { defineStore } from 'pinia';
import type {
  IFeatureFlags,
  IUser,
} from '@/types/store';

// 定义一个名为useUser的Pinia store
export const useUser = defineStore('user', {
  // 定义store的状态
  state: (): {
    user: IUser,
    featureFlags: IFeatureFlags,
  } => ({
    // 用户信息
    user: {
      username: '',
      avatar_url: '',
    },
    // 功能标志
    featureFlags: {},
  }),
  actions: {
    // 设置用户信息
    setUser(user: IUser) {
      this.user = user;
    },
    // 设置功能标志
    setFeatureFlags(data: IFeatureFlags) {
      this.featureFlags = data;
    },
  },
});
