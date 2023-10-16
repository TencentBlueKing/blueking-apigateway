import { defineStore } from 'pinia';

export const useCommon = defineStore('common', {
  state: () => ({
    apigwId: 0,
    methodList: [
      {
        id: 'GET',
        name: 'GET',
      },
      {
        id: 'POST',
        name: 'POST',
      },
      {
        id: 'PUT',
        name: 'PUT',
      },
      {
        id: 'PATCH',
        name: 'PATCH',
      },
      {
        id: 'DELETE',
        name: 'DELETE',
      },

      {
        id: 'HEAD',
        name: 'HEAD',
      },
      {
        id: 'OPTIONS',
        name: 'OPTIONS',
      },
      {
        id: 'ANY',
        name: 'ANY',
      },
    ],
  }),
  actions: {
    setApigwId(apigwId: number) {
      this.apigwId = apigwId;
    },
  },
});
