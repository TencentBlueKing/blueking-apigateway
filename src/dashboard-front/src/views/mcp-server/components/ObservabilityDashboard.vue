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
        :ref="(el: any) => setComponentRef(el, com.name)"
        v-model:search-params="searchParams"
        mode="Dashboard"
        :api-gateway-id="apigwId"
        :chart-loading="chartLoading"
        :chart-data="chartData"
        :statistics="statistics"
        @request="handleRequestDone"
        @clear-filter="handleClearFilter"
      />
    </div>
  </div>
</template>

<script lang="ts" setup>
import { useGateway } from '@/stores';
import { useObservabilityDashboard } from '@/hooks';
import DashboardBasicForm from '@/views/mcp-server/components/ObservabilityBasicForm.vue';
import DashboardQuestMonitor from '@/views/mcp-server/components/DashboardQuestMonitor.vue';

const dashboardFormCompMap = {
  Query: DashboardBasicForm,
  Request: DashboardQuestMonitor,
};

const gatewayStore = useGateway();
const {
  chartLoading,
  chartData,
  statistics,
  searchParams,
  fetchInitData,
  handleResetTime,
} = useObservabilityDashboard();

const componentRefs = reactive(new Map());

const componentList = shallowRef([
  { name: 'Query' },
  { name: 'Request' },
]);

const apigwId = computed(() => gatewayStore.apigwId);

// 设置仪表盘所有动态组件实例
const setComponentRef = (el: HTMLElement | null, name: string) => {
  if (el) {
    componentRefs?.set(name, el);
  }
  else {
    componentRefs?.delete(name);
  }
};

const handleRequestDone = async () => {
  await fetchInitData();
  componentRefs?.get('Request')?.syncParamsToCharts();
};

const handleClearFilter = () => {
  componentRefs?.get('Query')?.handleClearFilter();
  handleResetTime();
};

onMounted(() => {
  handleRequestDone();
});

onUnmounted(() => {
  componentRefs?.clear();
});
</script>

<style lang="scss" scoped>
.observability-dashboard-wrapper {
  box-sizing: border-box;

  .observability-basic-form {
    background-color: #ffffff;
    padding-left: 24px;

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
