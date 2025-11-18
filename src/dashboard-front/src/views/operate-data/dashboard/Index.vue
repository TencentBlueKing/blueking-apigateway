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

<template>
  <div>
    <Top
      ref="topRef"
      @refresh-change="handleRefreshChange"
      @step-change="handleStepChange"
    />

    <div class="ag-top-header">
      <BkForm
        class="search-form"
        form-type="vertical"
      >
        <BkFormItem :label="t('选择时间')">
          <DatePicker
            v-model="dateTime"
            :valid-date-range="['now-7d/d', 'now/d']"
            class="date-choose"
            format="YYYY-MM-DD HH:mm:ss"
            style="min-width: 154px;background: #fff;"
            @update:model-value="handleValueChange"
          />
        </BkFormItem>
        <BkFormItem :label="t('环境')">
          <BkSelect
            v-model="searchParams.stage_id"
            :clearable="false"
            style="width: 150px;"
          >
            <BkOption
              v-for="option in stageList"
              :id="option.id"
              :key="option.id"
              :name="option.name"
            />
          </BkSelect>
        </BkFormItem>
        <BkFormItem :label="t('后端服务')">
          <BkSelect
            v-model="backend_id"
            clearable
            style="width: 150px;"
            @change="handleBackendChange"
          >
            <BkOption
              v-for="option in backendList"
              :id="option.id"
              :key="option.id"
              :name="option.name"
            />
          </BkSelect>
        </BkFormItem>
        <BkFormItem :label="t('资源')">
          <ResourceSearcher
            v-model="searchParams.resource_id"
            :list="resourceList"
            :need-prefix="false"
            :placeholder="t('请输入资源名称或资源URL链接')"
            style="min-width: 296.5px;"
          />
        </BkFormItem>
      </BkForm>
    </div>

    <div class="statistics">
      <div class="requests line-container">
        <BkLoading :loading="chartLoading.requests_total">
          <div class="total-requests">
            <div class="title">
              {{ t('总请求数') }}
            </div>
            <div class="number">
              {{ statistics?.requests_total?.instant || 0 }}
            </div>
          </div>
        </BkLoading>
        <BkLoading :loading="chartLoading.health_rate">
          <div class="total-requests">
            <div class="title">
              {{ t('健康率') }}
            </div>
            <div class="number">
              {{ statistics?.health_rate?.instant || 0 }}%
            </div>
          </div>
        </BkLoading>

        <div class="success-requests">
          <BkLoading
            :loading="chartLoading.requests"
            class="full-box"
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
        </div>
        <div class="error-requests">
          <BkLoading
            :loading="chartLoading.non_20x_status"
            class="full-box"
          >
            <LineChart
              ref="statusRef"
              :chart-data="chartData['non_20x_status']"
              :title="t('非 200 请求数趋势')"
              instance-id="non_20x_status"
              @clear-params="handleClearParams"
              @report-init="handleReportInit"
            />
          </BkLoading>
        </div>
      </div>

      <div class="secondary-panel line-container">
        <div class="secondary-lf">
          <BkLoading
            :loading="chartLoading.app_requests"
            class="full-box"
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
        </div>

        <div class="secondary-rg">
          <BkLoading
            :loading="chartLoading.resource_requests"
            class="full-box"
          >
            <LineChart
              ref="resourceRequestsRef"
              :chart-data="chartData['resource_requests']"
              :title="t('Top 资源请求数趋势')"
              instance-id="resource_requests"
              @clear-params="handleClearParams"
              @report-init="handleReportInit"
            />
          </BkLoading>
        </div>
      </div>

      <div class="secondary-panel line-container">
        <div class="secondary-lf">
          <BkLoading
            :loading="chartLoading.ingress"
            class="full-box"
          >
            <LineChart
              ref="ingressRef"
              :chart-data="chartData['ingress']"
              :title="t('Top 资源 ingress 带宽占用')"
              instance-id="ingress"
              @clear-params="handleClearParams"
              @report-init="handleReportInit"
            />
          </BkLoading>
        </div>
        <div class="secondary-rg">
          <BkLoading
            :loading="chartLoading.egress"
            class="full-box"
          >
            <LineChart
              ref="egressRef"
              :chart-data="chartData['egress']"
              :title="t('Top 资源 egress 带宽占用')"
              instance-id="egress"
              @clear-params="handleClearParams"
              @report-init="handleReportInit"
            />
          </BkLoading>
        </div>
      </div>

      <div class="full-line">
        <BkLoading
          :loading="chartLoading.response_time_50th"
          class="full-box"
        >
          <LineChart
            ref="responseTime50Ref"
            :chart-data="chartData['response_time_50th']"
            :title="t('资源 50th 响应耗时分布')"
            instance-id="response_time_50th"
            @clear-params="handleClearParams"
            @report-init="handleReportInit"
          />
        </BkLoading>
      </div>

      <!-- <div class="full-line">
        <BkLoading
        :loading="chartLoading.response_time_90th"
        class="full-box"
        >
        <LineChart
        ref="responseTimeRef"
        :chart-data="chartData['response_time_90th']"
        :title="t('资源 90th 响应耗时分布')"
        instance-id="response_time_90th"
        @clear-params="handleClearParams"
        @report-init="handleReportInit"
        />
        </BkLoading>
        </div> -->

      <div class="full-line">
        <BkLoading
          :loading="chartLoading.response_time_95th"
          class="full-box"
        >
          <LineChart
            ref="responseTime95Ref"
            :chart-data="chartData['response_time_95th']"
            :title="t('资源 95th 响应耗时分布')"
            instance-id="response_time_95th"
            @clear-params="handleClearParams"
            @report-init="handleReportInit"
          />
        </BkLoading>
      </div>

      <div class="full-line">
        <BkLoading
          :loading="chartLoading.response_time_99th"
          class="full-box"
        >
          <LineChart
            ref="responseTime99Ref"
            :chart-data="chartData['response_time_99th']"
            :title="t('资源 99th 响应耗时分布')"
            instance-id="response_time_99th"
            @clear-params="handleClearParams"
            @report-init="handleReportInit"
          />
        </BkLoading>
      </div>
    </div>
  </div>
</template>

<script lang="ts" setup>
import dayjs from 'dayjs';
import { useGateway } from '@/stores';
import {
  type IChartDataLoading,
  type IChartDataType,
  type ISearchParamsType,
  type IStatisticsType,
  getApigwMetrics,
  getApigwMetricsInstant,
  getApigwResources,
  getApigwStages,
} from '@/services/source/dashboard';
import Top from './components/Top.vue';
import LineChart from './components/LineChart.vue';
import { getBackendServiceList } from '@/services/source/backendServices';
import ResourceSearcher from '@/views/operate-data/dashboard/components/ResourceSearcher.vue';
import DatePicker from '@blueking/date-picker';
import '@blueking/date-picker/vue3/vue3.css';
// import { ResourcesItem } from '@/views/resource/setting/types';
// import { IStageData } from '@/views/stage/overview/types/stage';

type InfoTypeItem = {
  formatText: null | string
  dayjs: dayjs.Dayjs | null
};

const { t } = useI18n();
const gatewayStore = useGateway();
const route = useRoute();

const stageList = ref([]);
const resourceList = ref([]);
const backend_id = ref('');
const backendList = ref([]);
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
  // 'response_time_90th',
  'response_time_50th',
  'response_time_95th',
  'response_time_99th',
]);
const statisticsTypes = ref<string[]>([
  'requests_total', // 请求总数
  'health_rate', // 健康率
]);
const chartData = ref<IChartDataType>({});
const statistics = ref<IStatisticsType>({});
const topRef = ref<InstanceType<typeof Top>>();
const requestsRef = ref<InstanceType<typeof LineChart>>();
const statusRef = ref<InstanceType<typeof LineChart>>();
const appRequestsRef = ref<InstanceType<typeof LineChart>>();
const resourceRequestsRef = ref<InstanceType<typeof LineChart>>();
const ingressRef = ref<InstanceType<typeof LineChart>>();
const egressRef = ref<InstanceType<typeof LineChart>>();
// const responseTimeRef = ref<InstanceType<typeof LineChart>>();
const responseTime50Ref = ref<InstanceType<typeof LineChart>>();
const responseTime95Ref = ref<InstanceType<typeof LineChart>>();
const responseTime99Ref = ref<InstanceType<typeof LineChart>>();
const chartLoading = ref<IChartDataLoading>({});
const searchParams = ref<ISearchParamsType>({
  stage_id: 0,
  resource_id: '',
  time_start: dayjs(formatTime.value[0]).unix(),
  time_end: dayjs(formatTime.value[1]).unix(),
  metrics: '',
  backend_name: '',
});

let timeId: NodeJS.Timeout | null = null;

const apigwId = computed(() => gatewayStore.apigwId);

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
}, {
  deep: true,
  immediate: true,
});

watch(searchParams, () => {
  getPageData();
  getInstantData();
  syncParamsToCharts();
}, { deep: true });

const getStages = async () => {
  const pageParams = {
    no_page: true,
    order_by: 'name',
  };
  const res = await getApigwStages(apigwId.value, pageParams);

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
    backend_id: backend_id.value,
  };
  const response = await getApigwResources(apigwId.value, pageParams);
  resourceList.value = response.results;
};

const getBackendServices = async () => {
  const pageParams = {
    offset: 0,
    limit: 10000,
  };
  const res = await getBackendServiceList(apigwId.value, pageParams);
  backendList.value = res?.results || [];
};

const handleBackendChange = async () => {
  searchParams.value.backend_name = backendList.value.find((item: any) => item.id === backend_id.value)?.name || '';
  searchParams.value.resource_id = '';
  await getResources();
};

// 请求数据
const getData = async (searchParams: ISearchParamsType, type: string) => {
  chartLoading.value[type as keyof IChartDataLoading] = true;
  try {
    chartData.value[type as keyof IChartDataType] = await getApigwMetrics(
      apigwId.value,
      {
        ...searchParams,
        metrics: type,
      },
    );
  }
  finally {
    chartLoading.value[type as keyof IChartDataLoading] = false;
  }
};

const getPageData = (step?: string) => {
  metricsList.value.forEach((type: string) => {
    getData({
      ...searchParams.value,
      step,
    }, type);
  });
};

const getInstantData = () => {
  statisticsTypes.value.forEach(async (type: string) => {
    chartLoading.value[type as keyof IChartDataLoading] = true;
    try {
      statistics.value[type as keyof IStatisticsType] = await getApigwMetricsInstant(
        apigwId.value,
        {
          ...searchParams.value,
          metrics: type,
        },
      );
    }
    finally {
      chartLoading.value[type as keyof IChartDataLoading] = false;
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
  // responseTimeRef.value!.syncParams(params);
  responseTime50Ref.value!.syncParams(params);
  responseTime95Ref.value!.syncParams(params);
  responseTime99Ref.value!.syncParams(params);
};

const handleRefreshChange = (interval: string) => {
  clearInterval(timeId);
  timeId = null;
  setIntervalFn(interval);
};

const handleStepChange = (step: string) => {
  getPageData(step);
};

const handleClearParams = () => {
  searchParams.value = {
    stage_id: stageList.value[0].id,
    resource_id: '',
    time_start: dayjs(formatTime.value[0]).unix(),
    time_end: dayjs(formatTime.value[1]).unix(),
    metrics: '',
    backend_name: '',
  };
  backend_id.value = '';
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
    getBackendServices(),
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
    margin-bottom: 16px;
  }
}
.full-box {
  width: 100%;
  height: 100%;
}
</style>
