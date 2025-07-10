import { defineStore } from 'pinia';

import { getGatewayDetail } from '@/services/source/gateway.ts';

type GatewayDetailType = Awaited<ReturnType<typeof getGatewayDetail>>;

export const useGateway = defineStore('useGateway', {
  state: (): { currentGateway: Partial<GatewayDetailType> | null } => ({ currentGateway: null }),
  getters: {
    // 网关是否为可编程网关 kind === 1
    isProgrammableGateway: state => state.currentGateway?.kind === 1,
    // aiCompletionAPI: state => `${BK_DASHBOARD_URL}/gateways/${state.apigwId}/ai/completion/`,
    aiCompletionAPI: () => '',
  },
  actions: {
    setCurrentGateway(gateway: Partial<GatewayDetailType>) {
      this.currentGateway = gateway;
    },
    async fetchGatewayDetail(id: number) {
      this.currentGateway = await getGatewayDetail(id);
    },
    clearCurrentGateway() {
      this.currentGateway = null;
    },
  },
});
