import { defineStore } from 'pinia';
import i18n from '@/language/i18n';

const { t } = i18n.global;

export const useOperateRecords = defineStore('operate-records', {
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
