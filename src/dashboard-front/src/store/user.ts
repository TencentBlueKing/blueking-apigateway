import { defineStore } from 'pinia';
import type {
  IFeatureFlags,
  IUser,
} from '@/types/store';

const {
  // BK_API_URL_TMPL,
  BK_USER_WEB_API_URL,
} = window;

const {
  // BK_API_URL_TMPL,
  BK_USER_WEB_API_URL,
} = window;

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
      display_name: '',
      avatar_url: '',
      tenant_id: '',
    },
    // 功能标志
    featureFlags: {},
  }),
  getters: {
    // apiBaseUrl: () => `${BK_API_URL_TMPL}/bk-user-web/prod`,
    apiBaseUrl: () => BK_USER_WEB_API_URL,
    // 是否开启了多租户模式
    isTenantMode: state => !!state?.featureFlags?.ENABLE_MULTI_TENANT_MODE,
    // 是否启用了 ai 问答功能
    isAIEnabled: state => state.featureFlags?.ENABLE_AI_COMPLETION,
  },
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
