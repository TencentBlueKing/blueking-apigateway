import { defineStore } from 'pinia';

import { getGatewayDetail } from '@/services/source/gateway.ts';

type GatewayDetailType = Awaited<ReturnType<typeof getGatewayDetail>>;

const { BK_DASHBOARD_URL } = window;

export const useGateway = defineStore('useGateway', {
  state: (): {
    currentGateway: Partial<GatewayDetailType> | null
    apigwId: number
    apigwName: string
  } => ({
    currentGateway: null,
    apigwId: 0,
    apigwName: '',
  }),
  getters: {
    // 网关是否为可编程网关 kind === 1
    isProgrammableGateway: state => state.currentGateway?.kind === 1,
    aiCompletionAPI: state => `${BK_DASHBOARD_URL}/gateways/${state.currentGateway?.id}/ai/completion/`,
  },
  actions: {
    // 设置网关id
    setApigwId(id: number) {
      this.apigwId = id;
    },
    // 设置网关名称
    setApigwName(name: string) {
      this.apigwName = name;
    },
    setCurrentGateway(gateway: Partial<GatewayDetailType>) {
      this.currentGateway = gateway;
    },
    async fetchGatewayDetail(id: number) {
      this.currentGateway = await getGatewayDetail(id) ?? {};
    },
    clearCurrentGateway() {
      this.currentGateway = null;
    },
  },
});
