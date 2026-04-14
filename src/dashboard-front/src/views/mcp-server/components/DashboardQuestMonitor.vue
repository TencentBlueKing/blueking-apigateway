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
  <div class="dashboard-monitor-wrapper">
    <!-- 顶部指标卡片 -->
    <div class="metrics-cards">
      <BkLoading
        :loading="chartLoading.requests_total"
        class="metrics-card requests-total-card"
      >
        <div class="metrics-card-content">
          <div class="title">
            {{ t('总请求数') }}
          </div>
          <div class="number truncate requests-total-number">
            {{ statistics?.requests_total?.instant || 0 }}
          </div>
        </div>
      </BkLoading>

      <BkLoading
        :loading="chartLoading.health_rate"
        class="metrics-card max-w-200px"
      >
        <div class="metrics-card-content">
          <div class="title">
            {{ t('健康率 (成功/总数)') }}
          </div>
          <div class="number">
            {{ statistics?.health_rate?.instant || 0 }}%
          </div>
        </div>
      </BkLoading>

      <BkLoading
        :loading="chartLoading.requests"
        class="metrics-card"
      >
        <LineChart
          ref="requestsRef"
          :chart-data="chartData['requests']"
          :title="t('总请求数趋势')"
          instance-id="requests"
          @clear-params="handleClearParams"
          @report-init="handleReportInit"
        />
      </BkLoading>
      <BkLoading
        :loading="chartLoading.requests_2xx"
        class="metrics-card"
      >
        <LineChart
          ref="successRequestsRef"
          :chart-data="chartData['requests_2xx']"
          :title="t('200 请求数趋势')"
          instance-id="requests_2xx"
          @clear-params="handleClearParams"
          @report-init="handleReportInit"
        />
      </BkLoading>
    </div>

    <div class="chart-row">
      <BkLoading
        :loading="chartLoading.method_requests"
        class="chart-card"
      >
        <LineChart
          ref="methodRequestsRef"
          :chart-data="chartData['method_requests']"
          :title="t('Top MCP Server 请求数趋势')"
          instance-id="method_requests"
          @clear-params="handleClearParams"
          @report-init="handleReportInit"
        />
      </BkLoading>
      <BkLoading
        :loading="chartLoading.tool_requests"
        class="chart-card"
      >
        <LineChart
          ref="toolRequestsRef"
          :chart-data="chartData['tool_requests']"
          :title="t('Top Tool 调用数趋势')"
          instance-id="tool_requests"
          @clear-params="handleClearParams"
          @report-init="handleReportInit"
        />
      </BkLoading>
    </div>

    <div class="chart-row">
      <BkLoading
        :loading="chartLoading.app_requests"
        class="chart-card"
      >
        <LineChart
          ref="appRequestsRef"
          :chart-data="chartData['app_requests']"
          :title="t('Top app_code 请求数趋势')"
          instance-id="app_requests"
          @clear-params="handleClearParams"
          @report-init="handleReportInit"
        />
      </BkLoading>
      <BkLoading
        :loading="chartLoading.non_2xx_status"
        class="chart-card"
      >
        <LineChart
          ref="errorRequestsRef"
          :chart-data="chartData['non_2xx_status']"
          :title="t('非 200 请求数趋势')"
          instance-id="non_2xx_status"
          @clear-params="handleClearParams"
          @report-init="handleReportInit"
        />
      </BkLoading>
    </div>

    <div class="chart-row">
      <BkLoading
        :loading="chartLoading.request_body_size"
        class="chart-card"
      >
        <LineChart
          ref="requestBodySizeRef"
          :chart-data="chartData['request_body_size']"
          :title="t('请求体积趋势 (avg bytes)')"
          instance-id="request_body_size"
          @clear-params="handleClearParams"
          @report-init="handleReportInit"
        />
      </BkLoading>

      <BkLoading
        :loading="chartLoading.response_body_size"
        class="chart-card"
      >
        <LineChart
          ref="responseBodySizeRef"
          :chart-data="chartData['response_body_size']"
          :title="t('响应体积趋势 (avg bytes)')"
          instance-id="response_body_size"
          @clear-params="handleClearParams"
          @report-init="handleReportInit"
        />
      </BkLoading>
    </div>

    <div class="chart-row">
      <BkLoading
        :loading="chartLoading.response_time_50th"
        class="chart-card"
      >
        <LineChart
          ref="responseTime50Ref"
          :chart-data="chartData['response_time_50th']"
          :title="t('Tool 调用 P50 耗时')"
          instance-id="response_time_50th"
          @clear-params="handleClearParams"
          @report-init="handleReportInit"
        />
      </BkLoading>
    </div>

    <div class="chart-row">
      <BkLoading
        :loading="chartLoading.response_time_95th"
        class="chart-card"
      >
        <LineChart
          ref="responseTime95Ref"
          :chart-data="chartData['response_time_95th']"
          :title="t('Tool 调用 P95 耗时')"
          instance-id="response_time_95th"
          @clear-params="handleClearParams"
          @report-init="handleReportInit"
        />
      </BkLoading>
    </div>

    <div class="chart-row">
      <BkLoading
        :loading="chartLoading.response_time_99th"
        class="chart-card"
      >
        <LineChart
          ref="responseTime99Ref"
          :chart-data="chartData['response_time_99th']"
          :title="t('Tool 调用 P99 耗时')"
          instance-id="response_time_99th"
          @clear-params="handleClearParams"
          @report-init="handleReportInit"
        />
      </BkLoading>
    </div>
  </div>
</template>

<script lang="ts" setup>
import { t } from '@/locales';
import {
  type IChartDataLoading,
  type IChartDataType,
  type IObservabilitySearchParams,
  type IStatisticsType,
} from '@/services/source/observability';
import LineChart from '@/views/mcp-server/components/DashboardLineChart.vue';

interface IProps {
  chartLoading?: IChartDataLoading
  chartData?: IChartDataType
  statistics: IStatisticsType
}

interface IEmits {
  'clear-filter': [void]
  'request': [void]
}

const searchParams = defineModel<IObservabilitySearchParams>('searchParams', { type: Object });

const { chartLoading = {}, chartData = {}, statistics } = defineProps<IProps>();

const emit = defineEmits<IEmits>();

const requestsRef = ref<InstanceType<typeof LineChart>>();
const successRequestsRef = ref<InstanceType<typeof LineChart>>();
const errorRequestsRef = ref<InstanceType<typeof LineChart>>();
const appRequestsRef = ref<InstanceType<typeof LineChart>>();
const toolRequestsRef = ref<InstanceType<typeof LineChart>>();
const methodRequestsRef = ref<InstanceType<typeof LineChart>>();
const requestBodySizeRef = ref<InstanceType<typeof LineChart>>();
const responseBodySizeRef = ref<InstanceType<typeof LineChart>>();
const responseTime50Ref = ref<InstanceType<typeof LineChart>>();
const responseTime95Ref = ref<InstanceType<typeof LineChart>>();
const responseTime99Ref = ref<InstanceType<typeof LineChart>>();

const syncParamsToCharts = () => {
  const params = { ...searchParams.value };
  requestsRef.value?.syncParams(params);
  successRequestsRef.value?.syncParams(params);
  errorRequestsRef.value?.syncParams(params);
  methodRequestsRef.value?.syncParams(params);
  appRequestsRef.value?.syncParams(params);
  toolRequestsRef.value?.syncParams(params);
  requestBodySizeRef.value?.syncParams(params);
  responseBodySizeRef.value?.syncParams(params);
  responseTime50Ref.value?.syncParams(params);
  responseTime95Ref.value?.syncParams(params);
  responseTime99Ref.value?.syncParams(params);
};

const handleClearParams = () => {
  emit('clear-filter');
};

const handleReportInit = () => {
  emit('request');
};

watch(() => searchParams.value.step, () => {
  emit('request');
});

defineExpose({ syncParamsToCharts });
</script>

<style lang="scss" scoped>
.dashboard-monitor-wrapper {
  box-sizing: border-box;

  // 指标卡片行
  .metrics-cards {
    display: flex;
    flex-wrap: wrap;
    gap: 16px;
    margin-bottom: 16px;

    .metrics-card {
      flex: 1;
      display: flex;
      align-items: center;
      justify-content: center;
      border-radius: 2px;
      background-color: #ffffff;
      box-shadow: 0 2px 4px 0 #1919290d;

      .metrics-card-content {
        width: 100%;
        color: #4d4f56;
        text-align: center;

        .title {
          font-size: 13px;
          margin-bottom: 24px;
        }

        .number {
          font-size: 32px;
        }
      }

      &.requests-total-card {
        min-width: 200px;
        width: fit-content;
        padding: 8px 24px;
        flex: none;

        .requests-total-number {
          width: 100%;
          max-width: 100%;
          display: inline-block;
          word-break: break-all;
        }
      }
    }
  }

  // 图表行容器
  .chart-row {
    display: flex;
    gap: 16px;
    margin-bottom: 16px;
    flex-wrap: wrap;

    // 图表卡片
    .chart-card {
      flex: 1;
      min-width: 300px;
      background-color: #ffffff;
      border-radius: 2px;
      box-shadow: 0 2px 4px 0 #1919290d;
      box-sizing: border-box;
    }
  }

  // 全屏容器样式
  .full-line {
    padding-bottom: 12px;
    margin-bottom: 16px;
    background-color: #ffffff;
    border-radius: 2px;
    box-shadow: 0 2px 4px 0 #1919290d;

    .full-box {
      width: 100%;
      height: 100%;
    }
  }
}

// 响应式适配
@media (max-width: 768px) {
  .dashboard-monitor-wrapper {

    .metrics-cards,
    .chart-row {
      flex-direction: column;

      .metrics-card,
      .chart-card {
        width: 100%;
        min-width: unset;
      }

      .requests-total-card {
        width: 100%;
        flex: 1;
      }
    }
  }
}

@media (min-width: 769px) and (max-width: 1200px) {
  .dashboard-monitor-wrapper {

    .chart-card {
      min-width: 350px;
    }
  }
}
</style>
