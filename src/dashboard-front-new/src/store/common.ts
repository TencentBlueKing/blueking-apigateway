import { defineStore } from 'pinia';

export const useCommon = defineStore('common', {
  state: () => ({
    // 网关id
    apigwId: 0,
    // 网关对象
    apigwName: {},
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
    // 网关标签
    gatewayLabels: [],
  }),
  actions: {
    setApigwId(apigwId: number) {
      this.apigwId = apigwId;
    },
    setApigwName(name: any) {
      this.apigwName = name;
    },
    setCurApigwData(data: any) {
      this.curApigwData = data;
    },
    setGatewayLabels(data: any) {
      this.gatewayLabels = data;
    },
  },
});
