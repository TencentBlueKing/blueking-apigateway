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

<template>
  <div class="observability-dashboard-wrapper">
    <div
      v-for="com of componentList"
      :key="com.name"
      :class="`p-24px pb-0 box-border ${com.name?.toLowerCase()}_wrapper`"
    >
      <Component
        :is="dashboardFormCompMap[com.name as keyof typeof dashboardFormCompMap]"
        :ref="(el) => setComponentRef(el as MethodsComponent | null, com.name)"
        v-model:search-params="searchParams"
        mode="Dashboard"
        :api-gateway-id="apigwId"
        :chart-loading="chartLoading"
        :chart-data="chartData"
        :statistics="statistics"
        @request="refreshDashboard"
        @clear-filter="handleClearFilter"
      />
    </div>
  </div>
</template>

<script lang="ts" setup>
import type { ComponentPublicInstance } from 'vue';
import { useGateway } from '@/stores';
import { parseIntervalValue, useObservabilityDashboard } from '@/hooks';
import DashboardBasicForm from '@/views/mcp-server/components/ObservabilityBasicForm.vue';
import DashboardQuestMonitor from '@/views/mcp-server/components/DashboardQuestMonitor.vue';

type MethodsComponent = ComponentPublicInstance<{
  syncParamsToCharts: () => void
  handleClearFilter: () => void
  handleSearchTimeRange: () => boolean
}>;

const dashboardFormCompMap = {
  Query: DashboardBasicForm,
  Request: DashboardQuestMonitor,
};

const gatewayStore = useGateway();
const {
  interval,
  chartLoading,
  chartData,
  statistics,
  searchParams,
  fetchInitData,
  handleResetTime,
  resetDashboard,
} = useObservabilityDashboard();

const componentRefs = shallowRef<Map<string, MethodsComponent> | null>(new Map());

const componentList = shallowRef([
  { name: 'Query' },
  { name: 'Request' },
]);

// 自动刷新定时器：本组件是唯一的调度者，工具栏只修改 interval
let timeId: ReturnType<typeof setInterval> | null = null;

const apigwId = computed(() => gatewayStore.apigwId);

// 设置仪表盘所有动态组件实例
const setComponentRef = (el: Element | MethodsComponent | null, name: string) => {
  if (el) {
    componentRefs.value?.set(name, el as MethodsComponent);
  }
  else {
    componentRefs.value?.delete(name);
  }
};

// 一轮查询：先按当前时间重新解析时间范围（相对快捷项随时间推进），再请求全部数据；时间无效时不请求
const refreshDashboard = async () => {
  const queryForm = componentRefs.value?.get('Query');
  if (queryForm && !queryForm.handleSearchTimeRange()) {
    return;
  }
  await fetchInitData();
  componentRefs.value?.get('Request')?.syncParamsToCharts();
};

const stopAutoRefresh = () => {
  if (timeId) {
    clearInterval(timeId);
    timeId = null;
  }
};

const handleClearFilter = () => {
  componentRefs.value?.get('Query')?.handleClearFilter();
  handleResetTime();
};

// 任何入口修改刷新间隔（工具栏、重置）都只改 interval，由这里统一启停唯一的定时器
watch(interval, (value) => {
  stopAutoRefresh();
  const intervalTime = parseIntervalValue(value);
  if (intervalTime > 0) {
    timeId = setInterval(refreshDashboard, intervalTime);
  }
}, { immediate: true });

onMounted(() => {
  refreshDashboard();
});

// 离开仪表盘时停止自动刷新并恢复初始状态，再次进入时不显示旧数据
onBeforeUnmount(() => {
  stopAutoRefresh();
  resetDashboard();
});

onUnmounted(() => {
  componentRefs.value?.clear();
});
</script>

<style lang="scss" scoped>
.observability-dashboard-wrapper {
  box-sizing: border-box;

  .observability-basic-form {
    padding-left: 24px;
    background-color: #fff;

    :deep(.collapse-panel-form) {
      padding: 24px 0;

      .bk-form-item {
        margin-bottom: 0;

        &:nth-child(3),
        &:nth-child(5),
        &:nth-child(6),
        &:last-child {
          display: none;
        }

      }
    }
  }
}
</style>
