import { defineStore } from 'pinia';

export const useCommon = defineStore('common', {
  state: () => ({
    apigwId: 0,
    // 网关名
    apigwName: '',
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
    curApigwData: { allow_update_gateway_auth: false },
  }),
  actions: {
    setApigwId(apigwId: number) {
      this.apigwId = apigwId;
    },
    setApigwName(name: string) {
      this.apigwName = name;
    },
    setCurApigwData(data: any) {
      this.curApigwData = data;
      console.log('this.curApigwData', this.curApigwData);
    },
  },
});
