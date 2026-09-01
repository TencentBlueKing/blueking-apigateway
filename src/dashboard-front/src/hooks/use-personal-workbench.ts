/*
 * TencentBlueKing is pleased to support the open source community by making
 * 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
 * Copyright (C) 2026 Tencent. All rights reserved.
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

import type { ITabKey } from '@/services/types/query/personal-workbench.ts';
import { getGatewayPendingList, getMcpPendingList } from '@/services/source/personal-workbench.ts';

// tab切换选项
const personalWorkbenchTab = ref<ITabKey>('gateway');
// 我的待办是否存在需要审批数据
const isExistPending = ref(true);
// 初始待办数据是否已确定（getMyPendingData 完成后置 true，表格首次请求应在其后发出，避免用未定的 tab 调错接口）
const isWorkbenchDataReady = ref(false);

// 并行请求处理
const getParallelRequestResult = (payload: PromiseSettledResult<any>) => {
  return payload?.status === 'fulfilled'
    ? payload.value
    : {
      count: 0,
      results: [],
    };
};

// 处理个人工作台公共数据部分
export function usePersonalWorkbench() {
  // 获取我的待办需要审批数据
  const getMyPendingData = async () => {
    const results = await Promise.allSettled([getGatewayPendingList(), getMcpPendingList()]);
    const [gatewayData, mcpData] = results.map(getParallelRequestResult);
    isExistPending.value = gatewayData.count > 0 || mcpData.count > 0;
    if (gatewayData.count < 1 && mcpData.count > 0) {
      personalWorkbenchTab.value = 'mcp';
    }
    // 初始数据已确定，页面据此发起首次列表请求（此时 tab 为最终值）
    isWorkbenchDataReady.value = true;
  };

  //  重置到网关选项
  const resetPersonalWorkbenchTab = () => {
    personalWorkbenchTab.value = 'gateway';
  };

  return {
    isExistPending,
    personalWorkbenchTab,
    isWorkbenchDataReady,
    getMyPendingData,
    resetPersonalWorkbenchTab,
  };
}

// 表格刷新联动：初始数据就绪（getMyPendingData 完成）后才发首次列表请求，确保使用最终 tab 对应的接口；
// 手动/自动切换 tab 时同样统一触发刷新。三个列表页共用，避免重复书写 watch
export function usePersonalWorkbenchListRefresh(
  tableCom: Ref<{ handleClearFilter: () => void } | null>,
) {
  const { personalWorkbenchTab, isWorkbenchDataReady } = usePersonalWorkbench();

  watch(
    () => isWorkbenchDataReady.value && personalWorkbenchTab.value,
    (readyTab) => {
      if (!readyTab) {
        return;
      }
      nextTick(() => {
        tableCom.value?.handleClearFilter();
      });
    },
    { immediate: true },
  );
}
