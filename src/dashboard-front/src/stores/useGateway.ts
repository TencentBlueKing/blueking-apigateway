/*
 * TencentBlueKing is pleased to support the open source community by making
 * 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
 * Copyright (C) Tencent. All rights reserved.
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

import { getGatewayDetail } from '@/services/source/gateway';

type GatewayDetailType = Awaited<ReturnType<typeof getGatewayDetail>>;

export const GATEWAY_DETAIL_TTL = 60_000;

interface IDetailRequests {
  version: number
  gatewayId?: number
  expiresAt: number
  pending: Map<number, Promise<GatewayDetailType>>
}

// Promise 不属于可序列化 state；按 Store 实例隔离，避免测试或多实例之间共享请求。
const detailRequests = new WeakMap<object, IDetailRequests>();
function getDetailRequests(store: object) {
  if (!detailRequests.has(store)) {
    detailRequests.set(store, {
      version: 0,
      expiresAt: 0,
      pending: new Map(),
    });
  }
  return detailRequests.get(store)!;
}

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
    // 网关是否为 AI 网关 kind === 2
    isAIGateway: state => state.currentGateway?.kind === 2,
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
      const requests = getDetailRequests(this);
      // 本地保存成功后的数据优先于先前发出的详情请求。
      requests.version += 1;
      requests.pending.clear();
      requests.gatewayId = gateway.id;
      requests.expiresAt = Date.now() + GATEWAY_DETAIL_TTL;
      this.currentGateway = gateway;
    },
    async fetchGatewayDetail(id: number) {
      const requests = getDetailRequests(this);
      requests.gatewayId = id;
      const pending = requests.pending.get(id);
      if (pending) {
        return pending;
      }
      const { version } = requests;
      requests.expiresAt = 0;
      const request = getGatewayDetail(id).then((data) => {
        if (data?.id !== id) {
          throw new Error('Unexpected gateway detail response');
        }
        if (requests.version === version && requests.gatewayId === id) {
          this.currentGateway = data;
          requests.expiresAt = Date.now() + GATEWAY_DETAIL_TTL;
        }
        return data;
      }).finally(() => {
        if (requests.pending.get(id) === request) {
          requests.pending.delete(id);
        }
      });
      requests.pending.set(id, request);
      return request;
    },
    // 结果缓存有时效；force 用于重新进入网关。在途请求合并与缓存有效期是两件事。
    async ensureGatewayDetail(id: number, force = false) {
      const requests = getDetailRequests(this);
      // 即使命中缓存，也要阻止另一网关的旧响应覆盖当前选择。
      requests.gatewayId = id;
      if (!force && this.currentGateway?.id === id && Date.now() < requests.expiresAt) {
        return this.currentGateway;
      }
      return this.fetchGatewayDetail(id);
    },
    clearCurrentGateway() {
      const requests = getDetailRequests(this);
      requests.version += 1;
      requests.pending.clear();
      requests.gatewayId = undefined;
      requests.expiresAt = 0;
      // 详情 Store 不隐式操作角色；成员变更/删除网关的调用方显式使角色失效。
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
