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

import type { Ref } from 'vue';
import { getReleasingStatus } from '@/services/source/gateway';
import { useUserInfo } from '@/stores/useUserInfo';

/** 只负责发布状态查询/轮询，角色权限仍由只读 useGatewayRole 提供。 */
export function useGatewayReleasingStatus(gatewayId: Ref<number>, canEdit: Ref<boolean>) {
  const userStore = useUserInfo();
  const releasingStatus = ref(false);
  let disposed = false;
  let version = 0;
  let timer: ReturnType<typeof setTimeout> | undefined;
  let pending: Promise<boolean | undefined> | undefined;

  const isCurrent = (requestVersion: number) => !disposed && requestVersion === version
    && canEdit.value && Number.isSafeInteger(gatewayId.value) && gatewayId.value > 0;

  const stopPolling = () => {
    clearTimeout(timer);
    timer = undefined;
  };

  // 同一身份/网关/权限周期内合并请求；失效结果返回 undefined，不能被当作“不在发布”执行启停。
  const refreshReleasingStatus = (): Promise<boolean | undefined> => {
    const requestVersion = version;
    if (!isCurrent(requestVersion)) {
      return Promise.resolve(undefined);
    }
    if (pending) {
      return pending;
    }
    const request = getReleasingStatus(gatewayId.value).then((data) => {
      if (!isCurrent(requestVersion)) {
        return undefined;
      }
      if (typeof data?.is_releasing !== 'boolean') {
        throw new Error('Unexpected releasing status response');
      }
      releasingStatus.value = data.is_releasing;
      return data.is_releasing;
    }).finally(() => {
      if (pending === request) {
        pending = undefined;
      }
    });
    pending = request;
    return request;
  };

  const startReleasingStatusPolling = () => {
    stopPolling();
    const requestVersion = version;
    if (!isCurrent(requestVersion)) {
      return;
    }
    // 使用串行 timeout：慢请求完成后才安排下一次，避免 setInterval 重叠查询。
    timer = setTimeout(async () => {
      try {
        const releasing = await refreshReleasingStatus();
        if (isCurrent(requestVersion) && releasing) {
          startReleasingStatusPolling();
        }
      }
      catch {
        // 旧周期的失败不能停止新周期的轮询；当前失败由 HTTP 层提示并停止自动重试。
        if (isCurrent(requestVersion)) {
          stopPolling();
        }
      }
    }, 5000);
  };

  watch(
    [gatewayId, canEdit, () => userStore.info.username, () => userStore.info.tenant_id],
    () => {
      version += 1;
      const requestVersion = version;
      stopPolling();
      pending = undefined;
      releasingStatus.value = false;
      // 同步撤销旧回调，但延迟到微任务再查询，合并同一轮路由/身份更新。
      void Promise.resolve().then(async () => {
        if (!isCurrent(requestVersion)) {
          return;
        }
        try {
          if (await refreshReleasingStatus() && isCurrent(requestVersion)) {
            startReleasingStatusPolling();
          }
        }
        catch {
          // 初始化与权限变化使用同一错误路径，不产生未处理的 Promise 拒绝。
          if (isCurrent(requestVersion)) {
            stopPolling();
          }
        }
      });
    },
    {
      immediate: true,
      flush: 'sync',
    },
  );

  onScopeDispose(() => {
    disposed = true;
    version += 1;
    pending = undefined;
    stopPolling();
  });

  return {
    releasingStatus,
    refreshReleasingStatus,
    startReleasingStatusPolling,
  };
}
