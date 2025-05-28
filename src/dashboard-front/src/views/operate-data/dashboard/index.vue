<template>
  <div>
    <top ref="topRef" @refresh-change="handleRefreshChange" />

    <div class="ag-top-header">
      <bk-form class="search-form" form-type="vertical">
        <bk-form-item :label="t('时间选择器')">
          <date-picker
            v-model="dateTime"
            :valid-date-range="['now-2d', 'now/d']"
            class="date-choose"
            format="YYYY-MM-DD HH:mm:ss"
            style="min-width: 154px;background: #fff;"
            @update:model-value="handleValueChange"
          />
        </bk-form-item>
        <bk-form-item :label="t('环境')">
          <bk-select
            v-model="searchParams.stage_id"
            :clearable="false"
            :input-search="false"
            filterable
            style="width: 150px;"
          >
            <bk-option
              v-for="option in stageList"
              :id="option.id"
              :key="option.id"
              :name="option.name"
            >
            </bk-option>
          </bk-select>
        </bk-form-item>
        <bk-form-item :label="t('资源')">
          <ResourceSearcher
            v-model="searchParams.resource_id"
            :list="resourceList"
            :need-prefix="false"
            :placeholder="t('请输入资源名称或资源URL链接')"
            style="min-width: 296.5px;"
          />
        </bk-form-item>
      </bk-form>
    </div>

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
          <bk-loading :loading="chartLoading.requests" class="full-box">
            <line-chart
              ref="requestsRef"
              :chart-data="chartData['requests']"
              :title="t('总请求数趋势')"
              instance-id="requests"
              @clear-params="handleClearParams"
              @report-init="handleReportInit"
            />
          </bk-loading>
        </div>
        <div class="error-requests">
          <bk-loading :loading="chartLoading.non_20x_status" class="full-box">
            <line-chart
              ref="statusRef"
              :chart-data="chartData['non_20x_status']"
              :title="t('非 200 请求数趋势')"
              instance-id="non_20x_status"
              @clear-params="handleClearParams"
              @report-init="handleReportInit"
            />
          </bk-loading>
        </div>
      </div>

      <div class="secondary-panel line-container">
        <div class="secondary-lf">
          <bk-loading :loading="chartLoading.app_requests" class="full-box">
            <line-chart
              ref="appRequestsRef"
              :chart-data="chartData['app_requests']"
              :title="t('top10 app_code 请求数趋势')"
              instance-id="app_requests"
              @clear-params="handleClearParams"
              @report-init="handleReportInit"
            />
          </bk-loading>
        </div>

        <div class="secondary-rg">
          <bk-loading :loading="chartLoading.resource_requests" class="full-box">
            <line-chart
              ref="resourceRequestsRef"
              :chart-data="chartData['resource_requests']"
              :title="t('top10 资源请求数趋势')"
              instance-id="resource_requests"
              @clear-params="handleClearParams"
              @report-init="handleReportInit"
            />
          </bk-loading>
        </div>
      </div>

      <div class="secondary-panel line-container">
        <div class="secondary-lf">
          <bk-loading :loading="chartLoading.ingress" class="full-box">
            <line-chart
              ref="ingressRef"
              :chart-data="chartData['ingress']"
              :title="t('top10 资源 ingress 带宽占用')"
              instance-id="ingress"
              @clear-params="handleClearParams"
              @report-init="handleReportInit"
            />
          </bk-loading>
        </div>
        <div class="secondary-rg">
          <bk-loading :loading="chartLoading.egress" class="full-box">
            <line-chart
              ref="egressRef"
              :chart-data="chartData['egress']"
              :title="t('top10 资源 egress 带宽占用')"
              instance-id="egress"
              @clear-params="handleClearParams"
              @report-init="handleReportInit"
            />
          </bk-loading>
        </div>
      </div>

      <div class="full-line">
        <bk-loading :loading="chartLoading.response_time_90th" class="full-box">
          <line-chart
            ref="responseTimeRef"
            :chart-data="chartData['response_time_90th']"
            :title="t('资源 90th 响应耗时分布')"
            instance-id="response_time_90th"
            @clear-params="handleClearParams"
            @report-init="handleReportInit"
          />
        </bk-loading>
      </div>
    </div>
  </div>
</template>

<script lang="ts" setup>
import {
  onMounted,
  ref,
  watch,
} from 'vue';
import { useCommon } from '@/store';
import {
  getApigwMetrics,
  getApigwMetricsInstant,
  getApigwResources,
  getApigwStages,
} from '@/http';
import { useI18n } from 'vue-i18n';
import {
  ChartDataLoading,
  ChartDataType,
  SearchParamsType,
  StatisticsType,
} from './type';
import Top from './components/top.vue';
import LineChart from './components/line-chart.vue';
import { IStageData } from '@/views/stage/overview/types/stage';
import DatePicker from '@blueking/date-picker';
import dayjs from 'dayjs';
import ResourceSearcher from '@/views/operate-data/dashboard/components/resource-searcher.vue';
import { ResourcesItem } from '@/views/resource/setting/types';
import { useRoute } from 'vue-router';

type InfoTypeItem = {
  formatText: null | string;
  dayjs: dayjs.Dayjs | null;
};

const { t } = useI18n();
const common = useCommon();
const route = useRoute();
const { apigwId } = common;

const stageList = ref<IStageData[]>([]);
const resourceList = ref<ResourcesItem[]>([]);
const dateTime = ref([
  'now-10m',
  'now',
]);
const formatTime = ref<string[]>([
  dayjs().subtract(10, 'minute')
    .format('YYYY-MM-DD HH:mm:ss'),
  dayjs().format('YYYY-MM-DD HH:mm:ss'),
]);
const metricsList = ref<string[]>([
  'requests', // 总请求数趋势
  'non_20x_status', // 非 200 请求数趋势
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
const searchParams = ref<SearchParamsType>({
  stage_id: 0,
  resource_id: '',
  time_start: dayjs(formatTime.value[0]).unix(),
  time_end: dayjs(formatTime.value[1]).unix(),
  metrics: '',
});

let timeId: NodeJS.Timeout | null = null;

watch(() => route.query, () => {
  const span = route.query?.time_span;
  const stageId = route.query?.stage_id;

  if (span && span === 'now-6h' && stageId) {
    searchParams.value.stage_id = Number(stageId);
    dateTime.value = [
      'now-6h',
      'now',
    ];
    const now = dayjs();
    const sixHoursAgo = now.subtract(6, 'hours');
    formatTime.value = [
      sixHoursAgo.format('YYYY-MM-DD HH:mm:ss'),
      now.format('YYYY-MM-DD HH:mm:ss'),
    ];
  }
}, { deep: true, immediate: true });

watch(searchParams, () => {
  getPageData();
  getInstantData();
  syncParamsToCharts();
}, { deep: true });

const getStages = async () => {
  const { apigwId } = common;
  const pageParams = {
    no_page: true,
    order_by: 'name',
  };
  const res = await getApigwStages(apigwId, pageParams);

  stageList.value = res || [];
  if (!searchParams.value.stage_id) {
    searchParams.value.stage_id = stageList.value[0]?.id;
  }
};

const getResources = async () => {
  const pageParams = {
    no_page: true,
    order_by: 'path',
    offset: 0,
    limit: 10000,
  };
  const response = await getApigwResources(apigwId, pageParams);
  resourceList.value = response.results;
};

// 请求数据
const getData = async (searchParams: SearchParamsType, type: string) => {
  chartLoading.value[type as keyof ChartDataLoading] = true;
  try {
    chartData.value[type as keyof ChartDataType] = await getApigwMetrics(
      apigwId,
      { ...searchParams, metrics: type },
    );
  } finally {
    chartLoading.value[type as keyof ChartDataLoading] = false;
  }
};

const getPageData = () => {
  metricsList.value.forEach((type: string) => {
    getData(searchParams.value, type);
  });
};

const getInstantData = () => {
  statisticsTypes.value.forEach(async (type: string) => {
    chartLoading.value[type as keyof ChartDataLoading] = true;
    try {
      statistics.value[type as keyof StatisticsType] = await getApigwMetricsInstant(
        apigwId,
        { ...searchParams.value, metrics: type },
      );
    } finally {
      chartLoading.value[type as keyof ChartDataLoading] = false;
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
  const params = { ...searchParams.value };
  requestsRef.value!.syncParams(params);
  statusRef.value!.syncParams(params);
  appRequestsRef.value!.syncParams(params);
  resourceRequestsRef.value!.syncParams(params);
  ingressRef.value!.syncParams(params);
  egressRef.value!.syncParams(params);
  responseTimeRef.value!.syncParams(params);
};

const handleRefreshChange = (interval: string) => {
  clearInterval(timeId);
  timeId = null;
  setIntervalFn(interval);
};

const handleClearParams = () => {
  searchParams.value = {
    stage_id: stageList.value[0].id,
    resource_id: '',
    time_start: dayjs(formatTime.value[0]).unix(),
    time_end: dayjs(formatTime.value[1]).unix(),
    metrics: '',
  };
  topRef.value?.reset();
};

const handleReportInit = () => {
  init();
};

const handleValueChange = (value: string[], info: InfoTypeItem[]) => {
  const [startTime, endTime] = info;
  formatTime.value = [
    startTime?.formatText,
    endTime?.formatText,
  ];
  const [time_start, time_end] = formatTime.value;
  if (time_start && time_end) {
    searchParams.value.time_start = dayjs(time_start).unix();
    searchParams.value.time_end = dayjs(time_end).unix();
  }
};

const init = async () => {
  await Promise.all([
    getStages(),
    getResources(),
  ]);
  const [time_start, time_end] = formatTime.value;
  if (time_start && time_end) {
    searchParams.value.time_start = dayjs(time_start).unix();
    searchParams.value.time_end = dayjs(time_end).unix();
  }
};

onMounted(() => {
  init();
});

</script>

<style lang="scss" scoped>

.ag-top-header {
  padding: 20px 24px 0;
}

.search-form {
  width: 100%;
  display: flex;

  :deep(.bk-form-item) {
    margin-right: 16px;
  }
}

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
