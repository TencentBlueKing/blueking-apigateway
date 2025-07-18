import { defineStore } from 'pinia';
import { t } from '@/locales';

export const useAuditLog = defineStore('useAuditLog', {
  state: () => ({
    operateStatus: [
      {
        name: t('成功'),
        value: 'success',
      },
      // {
      //   name: t('失败'),
      //   value: 'failure',
      // },
      // {
      //   name: t('未知'),
      //   value: 'unknown',
      // },
    ],
  }),
  getters: {
    geOperateStatus(state) {
      return state.operateStatus;
    },
  },
});
