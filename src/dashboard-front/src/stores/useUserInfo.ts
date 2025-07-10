import { defineStore } from 'pinia';

import { getUserInfo } from '@/services/source/basic';

type InfoType = Awaited<ReturnType<typeof getUserInfo>>;

export const useUserInfo = defineStore('useUserInfo', {
  state: (): Record<string, InfoType> => ({
    info: {
      avatar_url: '',
      chinese_name: '',
      display_name: '',
      tenant_id: null,
      username: '',
    },
  }),
  actions: {
    async fetchUserInfo() {
      this.info = await getUserInfo();
    },
  },
});
