/*
 * TencentBlueKing is pleased to support the open source community by making
 * 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
 * Copyright (C) 2025 Tencent. All rights reserved.
 * Licensed under the MIT License (the "License"); you may not use this file except
 * in compliance with the License. You may obtain a copy of the License at
 *
 *     http://opensource.org/licenses/MIT
 *
 * Unless required by applicable law or agreed to in writing, software distributed under
 * the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND,
 * either express or implied. See the License for the specific language governing permissions and
 * limitations under the License.
 *
 * We undertake not to change the open source license (MIT license) applicable
 * to the current version of the project delivered to anyone in the future.
 */
import { defineStore } from 'pinia';

import { getGatewayDetail } from '@/services/source/gateway.ts';

type GatewayDetailType = Awaited<ReturnType<typeof getGatewayDetail>>;

const { BK_DASHBOARD_URL } = window;

export const useGateway = defineStore('useGateway', {
  state: (): {
    currentGateway: Partial<GatewayDetailType> | null
    apigwId: number
    apigwName: string
    labels: {
      id: number
      name: string
    }[]
  } => ({
    currentGateway: null,
    apigwId: 0,
    apigwName: '',
    // 网关标签
    labels: [],
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
    setGatewayLabels(labels: {
      id: number
      name: string
    }[]) {
      this.labels = labels;
    },
  },
});
