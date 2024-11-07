<template>
  <top ref="topRef" @search-change="handleSearchChange" @refresh-change="handleRefreshChange" />
  <div class="statistics">
    <div class="requests line-container">
      <bk-loading :loading="chartLoading.requests_total">
        <div class="total-requests">
          <div class="title">
            {{ t('总请求数') }}
          </div>
          <div class="number">
            {{ statistics?.requests_total?.instant || 0 }}
          </div>
        </div>
      </bk-loading>
      <bk-loading :loading="chartLoading.health_rate">
        <div class="total-requests">
          <div class="title">
            {{ t('健康率') }}
          </div>
          <div class="number">
            {{ statistics?.health_rate?.instant || 0 }}%
          </div>
        </div>
      </bk-loading>

      <div class="success-requests">
        <bk-loading class="full-box" :loading="chartLoading.requests">
          <line-chart
            ref="requestsRef"
            :title="t('总请求数趋势')"
            :chart-data="chartData['requests']"
            @clear-params="handleClearParams"
            @report-init="handleReportInit"
            instance-id="requests" />
        </bk-loading>
      </div>
      <div class="error-requests">
        <bk-loading class="full-box" :loading="chartLoading.non_200_status">
          <line-chart
            ref="statusRef"
            :title="t('非 200 请求数趋势')"
            :chart-data="chartData['non_200_status']"
            @clear-params="handleClearParams"
            @report-init="handleReportInit"
            instance-id="non_200_status" />
        </bk-loading>
      </div>
    </div>

    <div class="secondary-panel line-container">
      <div class="secondary-lf">
        <bk-loading class="full-box" :loading="chartLoading.app_requests">
          <line-chart
            ref="appRequestsRef"
            :title="t('top10 app_code 请求数趋势')"
            :chart-data="chartData['app_requests']"
            @clear-params="handleClearParams"
            @report-init="handleReportInit"
            instance-id="app_requests" />
        </bk-loading>
      </div>

      <div class="secondary-rg">
        <bk-loading class="full-box" :loading="chartLoading.resource_requests">
          <line-chart
            ref="resourceRequestsRef"
            :title="t('top10 资源请求数趋势')"
            :chart-data="chartData['resource_requests']"
            @clear-params="handleClearParams"
            @report-init="handleReportInit"
            instance-id="resource_requests" />
        </bk-loading>
      </div>
    </div>

    <div class="secondary-panel line-container">
      <div class="secondary-lf">
        <bk-loading class="full-box" :loading="chartLoading.ingress">
          <line-chart
            ref="ingressRef"
            :title="t('top10 资源 ingress 带宽占用')"
            :chart-data="chartData['ingress']"
            @clear-params="handleClearParams"
            @report-init="handleReportInit"
            instance-id="ingress" />
        </bk-loading>
      </div>
      <div class="secondary-rg">
        <bk-loading class="full-box" :loading="chartLoading.egress">
          <line-chart
            ref="egressRef"
            :title="t('top10 资源 egress 带宽占用')"
            :chart-data="chartData['egress']"
            @clear-params="handleClearParams"
            @report-init="handleReportInit"
            instance-id="egress" />
        </bk-loading>
      </div>
    </div>

    <div class="full-line">
      <bk-loading class="full-box" :loading="chartLoading.response_time_90th">
        <line-chart
          ref="responseTimeRef"
          :title="t('资源 90th 响应耗时分布')"
          :chart-data="chartData['response_time_90th']"
          @clear-params="handleClearParams"
          @report-init="handleReportInit"
          instance-id="response_time_90th" />
      </bk-loading>
    </div>
  </div>
</template>

<script lang="ts" setup>
import { ref } from 'vue';
import { useCommon } from '@/store';
import { getApigwMetrics, getApigwMetricsInstant } from '@/http';
import { useI18n } from 'vue-i18n';
import { SearchParamsType, ChartDataType, StatisticsType, ChartDataLoading } from './type';
import Top from './components/top.vue';
import LineChart from './components/line-chart.vue';

const common = useCommon();
const { apigwId } = common;

const { t } = useI18n();

const metricsList = ref<string[]>([
  'requests', // 总请求数趋势
  'non_200_status', // 非 200 请求数趋势
  'app_requests', // app_code 维度请求数趋势
  'resource_requests', // 每个资源请求数趋势
  'ingress', // 每个资源的 ingress  带宽占用
  'egress', // 每个资源的 egress 带宽占用
  // 'response_time', // 每个资源的响应耗时分布50th 80th 90th取top10资源(response_time_50th response_time_80th response_time_90th)
  'response_time_90th',
]);
const statisticsTypes = ref<string[]>([
  'requests_total', // 请求总数
  'health_rate', // 健康率
]);
const chartData = ref<ChartDataType>({});
let timeId: NodeJS.Timeout | null = null;
let params: SearchParamsType = {};
const statistics = ref<StatisticsType>({});
const topRef = ref<InstanceType<typeof Top>>();
const requestsRef = ref<InstanceType<typeof LineChart>>();
const statusRef = ref<InstanceType<typeof LineChart>>();
const appRequestsRef = ref<InstanceType<typeof LineChart>>();
const resourceRequestsRef = ref<InstanceType<typeof LineChart>>();
const ingressRef = ref<InstanceType<typeof LineChart>>();
const egressRef = ref<InstanceType<typeof LineChart>>();
const responseTimeRef = ref<InstanceType<typeof LineChart>>();
const chartLoading = ref<ChartDataLoading>({});

// 请求数据
const getData = async (searchParams: SearchParamsType, type: string) => {
  searchParams.metrics = type;
  chartLoading.value[type] = true;
  try {
    const data = await getApigwMetrics(apigwId, searchParams);
    chartData.value[type] = data;
  } finally {
    chartLoading.value[type] = false;
  }
};

const getPageData = () => {
  metricsList.value.forEach((type: string) => {
    getData(params, type);
  });
};

const getInstantData = () => {
  statisticsTypes.value.forEach(async (type: string) => {
    chartLoading.value[type] = true;
    try {
      const response = await getApigwMetricsInstant(apigwId, { ...params, metrics: type });
      statistics.value[type] = response;
    } finally {
      chartLoading.value[type] = false;
    }
  });
};

const setIntervalFn = (interval: string) => {
  if (interval === 'off') {
    return;
  }

  const unit = interval?.substr(-1);
  let time = 0;
  switch (unit) {
    case 's':
      time = Number(interval.replace('s', '')) * 1000;
      break;
    case 'm':
      time = Number(interval.replace('m', '')) * 60 * 1000;
      break;
    case 'h':
      time = Number(interval.replace('h', '')) * 60 * 60 * 1000;
      break;
    case 'd':
      time = Number(interval.replace('d', '')) * 24 * 60 * 60 * 1000;
      break;
  };

  timeId = setInterval(() => {
    getPageData();
    getInstantData();
  }, time);
};

const syncParamsToCharts = () => {
  requestsRef.value!.syncParams(params);
  statusRef.value!.syncParams(params);
  appRequestsRef.value!.syncParams(params);
  resourceRequestsRef.value!.syncParams(params);
  ingressRef.value!.syncParams(params);
  egressRef.value!.syncParams(params);
  responseTimeRef.value!.syncParams(params);
};

const handleSearchChange = (searchParams: SearchParamsType) => {
  params = searchParams;
  getPageData();
  getInstantData();
  syncParamsToCharts();
};

const handleRefreshChange = (interval: string) => {
  clearInterval(timeId);
  timeId = null;
  setIntervalFn(interval);
};

const handleClearParams = () => {
  topRef.value?.reset();
};

const handleReportInit = () => {
  topRef.value?.init();
};

</script>

<style lang="scss" scoped>
.statistics {
  padding: 20px 24px 32px;
  .line-container {
    display: flex;
    align-items: center;
    margin-bottom: 16px;
  }
  .requests {
    .total-requests {
      width: 200px;
      height: 320px;
      background: #FFFFFF;
      box-shadow: 0 1px 2px 0 #0000001a;
      border-radius: 2px;
      margin-right: 16px;
      display: flex;
      flex-direction: column;
      justify-content: center;
      align-items: center;
      .title {
        font-size: 14px;
        color: #63656E;
        line-height: 18px;
        margin-bottom: 24px;
      }
      .number {
        font-weight: Bold;
        font-size: 32px;
        color: #313238;
        line-height: 32px;
      }
    }
    .success-requests {
      width: 673px;
      background: #FFFFFF;
      box-shadow: 0 2px 4px 0 #1919290d;
      border-radius: 2px;
      margin-right: 16px;
    }
    .error-requests {
      width: 673px;
      background: #FFFFFF;
      box-shadow: 0 2px 4px 0 #1919290d;
      border-radius: 2px;
    }
  }
  .secondary-panel {
    .secondary-lf {
      width: 808px;
      background: #FFFFFF;
      box-shadow: 0 2px 4px 0 #1919290d;
      border-radius: 2px;
      margin-right: 16px;
      padding-bottom: 6px;
    }
    .secondary-rg {
      width: 808px;
      background: #FFFFFF;
      box-shadow: 0 2px 4px 0 #1919290d;
      border-radius: 2px;
      padding-bottom: 6px;
    }
  }
  .full-line {
    background: #FFFFFF;
    box-shadow: 0 2px 4px 0 #1919290d;
    border-radius: 2px;
    padding-bottom: 12px;
  }
}
.full-box {
  width: 100%;
  height: 100%;
}
</style>
