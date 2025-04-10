import { defineStore } from 'pinia';

import type { Gateway } from '@/types/gateway';

interface State {
  apigwId: number;
  apigwName: string;
  methodList: {
    id: string,
    name: string,
  }[];
  curApigwData: Gateway;
  gatewayLabels: any[];
  websiteConfig: any;
  noGlobalError: boolean;
}

export const useCommon = defineStore('common', {
  state: (): State => ({
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
    // curApigwData: { allow_update_gateway_auth: false },
    curApigwData: {
      id: 0,
      name: '',
      description: '',
      maintainers: [],
      doc_maintainers: {
        type: '',
        contacts: [],
        service_account: {
          name: '',
          link: '',
        },
      },
      developers: [],
      status: 0,
      kind: 0,
      is_public: false,
      created_by: '',
      created_time: '',
      updated_time: '',
      public_key: '',
      is_official: false,
      allow_update_gateway_auth: false,
      api_domain: '',
      docs_url: '',
      public_key_fingerprint: '',
      bk_app_codes: [],
      related_app_codes: [],
      extra_info: {},
      links: {},
    },
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
    setCurApigwData(data: Gateway) {
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
