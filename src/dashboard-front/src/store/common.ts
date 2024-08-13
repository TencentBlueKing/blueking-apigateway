import { defineStore } from 'pinia';

export const useCommon = defineStore('common', {
  state: () => ({
    // 网关id
    apigwId: 0,
    // 网关name
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
    // 网关标签
    gatewayLabels: [],
    websiteConfig: {},
    noGlobalError: false, // 请求出错是否显示全局的错误Message
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
    },
    setGatewayLabels(data: any) {
      this.gatewayLabels = data;
    },
    setWebsiteConfig(data: any) {
      this.websiteConfig = data;
    },
    setNoGlobalError(val: boolean) {
      this.noGlobalError = val;
    },
  },
});
