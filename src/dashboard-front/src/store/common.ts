import { defineStore } from 'pinia';

import type { Gateway } from '@/types/gateway';

// 定义状态接口
interface State {
  apigwId: number; // 网关ID
  apigwName: string; // 网关名称
  methodList: {
    id: string; // 方法ID
    name: string; // 方法名称
  }[]; // 方法列表
  curApigwData: Gateway; // 当前网关数据
  gatewayLabels: any[]; // 网关标签
  websiteConfig: any; // 网站配置
  noGlobalError: boolean; // 请求出错是否显示全局的错误消息
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
  getters: {
    // 网关是否为可编程网关 kind === 1
    isProgrammableGateway: state => state?.curApigwData?.kind === 1,
  },
  actions: {
    // 设置网关id
    setApigwId(apigwId: number) {
      this.apigwId = apigwId;
    },
    // 设置网关名称
    setApigwName(name: string) {
      this.apigwName = name;
    },
    // 设置当前网关数据
    setCurApigwData(data: Gateway) {
      this.curApigwData = data;
    },
    // 设置网关标签
    setGatewayLabels(data: any) {
      this.gatewayLabels = data;
    },
    // 设置网站配置
    setWebsiteConfig(data: any) {
      this.websiteConfig = data;
    },
    // 设置是否显示全局错误消息
    setNoGlobalError(val: boolean) {
      this.noGlobalError = val;
    },
  },
});
