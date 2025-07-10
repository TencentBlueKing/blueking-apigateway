import { defineStore } from 'pinia';

import type { Gateway } from '@/types/gateway';
import { METHODS_CONSTANTS } from '@/constants';

// 定义状态接口
interface State {
  // 网关ID
  apigwId: number
  // 网关名称
  apigwName: string
  // 方法列表
  methodList: {
    // 方法ID
    id: string
    // 方法名称
    name: string
  }[]
  // 当前网关数据
  curApigwData: Gateway
  // 网关标签
  gatewayLabels: any[]
  // 网站配置
  websiteConfig: any
  // 请求出错是否显示全局的错误消息
  noGlobalError: boolean
}

const { BK_DASHBOARD_URL } = window;

export const useCommon = defineStore('common', {
  state: (): State => ({
    // 网关id
    apigwId: 0,
    // 网关name
    apigwName: '',
    methodList: METHODS_CONSTANTS,
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
    // 请求出错是否显示全局的错误Message
    noGlobalError: false,
  }),
  getters: {
    // 网关是否为可编程网关 kind === 1
    isProgrammableGateway: state => state?.curApigwData?.kind === 1,
    aiCompletionAPI: state => `${BK_DASHBOARD_URL}/gateways/${state.apigwId}/ai/completion/`,
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
