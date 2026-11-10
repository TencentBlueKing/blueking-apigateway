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
        label-width="auto"
      >
        <BkFormItem :label="t('选择时间')">
          <DatePicker
            v-model="dateTime"
            :valid-date-range="['now-7d/d', 'now/d']"
            class="date-choose"
            format="YYYY-MM-DD HH:mm:ss"
            :need-timezone="false"
            style="min-width: 150px;background: #fff;"
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
        <BkFormItem
          v-show="!isAIGateway"
          :label="t('后端服务')"
        >
          <BkSelect
            v-model="backend_id"
            clearable
            style="max-width: 300px;"
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
        <BkFormItem
          v-show="isAIGateway"
          :label="t('后端/模型服务')"
        >
          <BkSelect
            v-model="backend_id"
            clearable
            style="max-width: 300px;"
            @change="handleBackendChange"
          >
            <BkOptionGroup
              :label="t('后端服务')"
              collapsible
            >
              <BkOption
                v-for="option in standardBackendList"
                :id="option.id"
                :key="option.id"
                :name="option.name"
              />
            </BkOptionGroup>
            <BkOptionGroup
              :label="t('模型服务')"
              collapsible
            >
              <BkOption
                v-for="option in aiBackendList"
                :id="option.id"
                :key="option.id"
                :name="option.name"
              />
            </BkOptionGroup>
          </BkSelect>
        </BkFormItem>
        <BkFormItem :label="t('资源')">
          <ResourceSearcher
            v-model="searchParams.resource_id"
            :list="resourceList"
            :need-prefix="false"
            :placeholder="t('请输入资源名称或资源URL链接')"
            style="min-width: 300px;"
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

      <template v-if="gatewayStore.isAIGateway">
        <div class="ai-metrics-title">
          {{ t('AI 模型代理') }}
        </div>
        <div class="full-line">
          <BkLoading
            :loading="chartLoading.llm_latency_95th"
            class="full-box"
          >
            <LineChart
              ref="llmLatency95thRef"
              :chart-data="chartData.llm_latency_95th"
              :title="t('LLM P95 延迟（非流式完整响应 / 流式首 Token）')"
              instance-id="llm_latency_95th"
              @clear-params="handleClearParams"
              @report-init="handleReportInit"
            />
          </BkLoading>
        </div>
        <div class="full-line">
          <BkLoading
            :loading="chartLoading.llm_token_95th"
            class="full-box"
          >
            <LineChart
              ref="llmToken95thRef"
              :chart-data="chartData.llm_token_95th"
              :title="t('单请求 Token P95')"
              instance-id="llm_token_95th"
              @clear-params="handleClearParams"
              @report-init="handleReportInit"
            />
          </BkLoading>
        </div>
        <div class="full-line">
          <BkLoading
            :loading="chartLoading.llm_latency_avg"
            class="full-box"
          >
            <LineChart
              ref="llmLatencyAvgRef"
              :chart-data="chartData.llm_latency_avg"
              :title="t('LLM 平均耗时趋势（非流式完整响应 / 流式首 Token）')"
              instance-id="llm_latency_avg"
              @clear-params="handleClearParams"
              @report-init="handleReportInit"
            />
          </BkLoading>
        </div>
        <div class="secondary-panel line-container">
          <div class="secondary-lf">
            <BkLoading
              :loading="chartLoading.llm_token_usage"
              class="full-box"
            >
              <LineChart
                ref="llmTokenUsageRef"
                :chart-data="chartData.llm_token_usage"
                :title="t('LLM Token 消耗趋势')"
                instance-id="llm_token_usage"
                @clear-params="handleClearParams"
                @report-init="handleReportInit"
              />
            </BkLoading>
          </div>
          <div class="secondary-rg">
            <BkLoading
              :loading="chartLoading.llm_active_connections"
              class="full-box"
            >
              <LineChart
                ref="llmActiveConnectionsRef"
                :chart-data="chartData.llm_active_connections"
                :title="t('LLM 活跃连接数趋势')"
                instance-id="llm_active_connections"
                @clear-params="handleClearParams"
                @report-init="handleReportInit"
              />
            </BkLoading>
          </div>
        </div>
      </template>
    </div>
  </div>
</template>

<script lang="ts" setup>
import { Message } from 'bkui-vue';
import { useGateway } from '@/stores';
import { queryMetricsInstant, queryMetricsRange } from '@/services/source/gateway/metrics';
import type {
  IChartDataLoading,
  IChartDataType,
  ISearchParamsType,
  IStatisticsType,
} from '@/types/metrics';
import { getResourceList } from '@/services/source/gateway/resource';
import { getStageList } from '@/services/source/gateway/stage';
import { getBackendServiceList } from '@/services/source/gateway/backend';
import Top from './components/Top.vue';
import LineChart from './components/LineChart.vue';
import ResourceSearcher from '@/views/operate-data/dashboard/components/ResourceSearcher.vue';
import DatePicker, { type DateValue } from '@blueking/date-picker';
import '@blueking/date-picker/vue3/vue3.css';
import type {
  IExtractApiReturn,
  IExtractListApiResults,
} from '@/services/types/utils.ts';
import { type TimeRangeSeconds, getRecentRange } from '@/utils/time-range';
import { resolveDatePickerRange } from '@/utils/date-picker-range';

type IStageItem = IExtractApiReturn<typeof getStageList>[number];
type IBackendItem = IExtractListApiResults<typeof getBackendServiceList>;
type IResourceItem = IExtractListApiResults<typeof getResourceList>;
type MetricsType = Parameters<typeof queryMetricsRange>[1]['metrics'];
type InstantMetricsType = Parameters<typeof queryMetricsInstant>[1]['metrics'];
type MetricsStep = NonNullable<Parameters<typeof queryMetricsRange>[1]['step']>;

const { t } = useI18n();
const gatewayStore = useGateway();
const route = useRoute();

const stageList = ref<IStageItem[]>([]);
const resourceList = ref<IResourceItem[]>([]);
const backend_id = ref('');
const backendList = ref<IBackendItem[]>([]);
const isAIGateway = computed(() => gatewayStore.isAIGateway);
const standardBackendList = computed(() => backendList.value.filter(item => item?.kind === 'standard'));
const aiBackendList = computed(() => backendList.value.filter(item => item?.kind === 'ai'));
// 日期组件的选择值：相对表达式或绝对毫秒时间戳，每轮查询按当前时间解析
const dateTime = ref<DateValue>([
  'now-10m',
  'now',
]);
const commonMetricsList = [
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
] as const;
const aiMetricsList = [
  'llm_latency_95th',
  'llm_token_95th',
  'llm_latency_avg',
  'llm_token_usage',
  'llm_active_connections',
] as const;
const metricsList = computed(() => gatewayStore.isAIGateway
  ? [...commonMetricsList, ...aiMetricsList]
  : commonMetricsList);
const statisticsTypes = ref<InstantMetricsType[]>([
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
const llmLatency95thRef = ref<InstanceType<typeof LineChart>>();
const llmToken95thRef = ref<InstanceType<typeof LineChart>>();
const llmLatencyAvgRef = ref<InstanceType<typeof LineChart>>();
const llmTokenUsageRef = ref<InstanceType<typeof LineChart>>();
const llmActiveConnectionsRef = ref<InstanceType<typeof LineChart>>();
const chartLoading = ref<IChartDataLoading>({});
// 时序图采样粒度，只用于区间指标请求；与 searchParams 分开保存，切换时不重复请求瞬时统计
const step = shallowRef<MetricsStep>('auto');
const initialRange: TimeRangeSeconds = resolveDatePickerRange(dateTime.value) ?? getRecentRange(10, 'minute');
// 查询参数；time_start/time_end 为本轮查询的时间快照（秒）
const searchParams = ref<ISearchParamsType>({
  stage_id: 0,
  resource_id: '',
  time_start: initialRange[0],
  time_end: initialRange[1],
  metrics: '' as ISearchParamsType['metrics'],
  backend_name: '',
});

let timeId: ReturnType<typeof setInterval> | null = null;
// 初始化期间查询参数的变化不触发请求，由 init 结束时统一请求一次
let isInitializing = false;

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
    const range = resolveDatePickerRange(dateTime.value);
    if (range) {
      [searchParams.value.time_start, searchParams.value.time_end] = range;
    }
  }
}, {
  deep: true,
  immediate: true,
});

watch(searchParams, () => {
  if (isInitializing) {
    return;
  }
  loadAll();
}, { deep: true });

const getStages = async () => {
  const pageParams: Parameters<typeof getStageList>[1] = {};
  const res = await getStageList(apigwId.value, pageParams);

  stageList.value = res || [];
  if (!searchParams.value.stage_id) {
    searchParams.value.stage_id = stageList.value[0]?.id;
  }
};

const getResources = async () => {
  const pageParams: Parameters<typeof getResourceList>[1] = {
    no_page: true,
    order_by: 'path',
    offset: 0,
    limit: 10000,
    backend_id: (backend_id.value || undefined) as number | undefined,
  };
  const response = await getResourceList(apigwId.value, pageParams);
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

// 区间、瞬时指标的公共查询参数：时间为本轮快照（秒），须成对传；资源为空时不传
const getMetricsBaseParams = () => {
  const {
    stage_id = 0,
    resource_id,
    backend_name,
    time_start,
    time_end,
  } = searchParams.value;
  return {
    stage_id,
    resource_id: resource_id ? Number(resource_id) : undefined,
    backend_name,
    time_start,
    time_end,
  };
};

// 请求数据：区间指标始终带上当前选择的粒度
const getData = async (type: MetricsType) => {
  chartLoading.value[type as keyof IChartDataLoading] = true;
  try {
    chartData.value[type as keyof IChartDataType] = await queryMetricsRange(
      apigwId.value,
      {
        ...getMetricsBaseParams(),
        step: step.value,
        metrics: type,
      },
    ) as any;
  }
  finally {
    chartLoading.value[type as keyof IChartDataLoading] = false;
  }
};

const getPageData = () => {
  metricsList.value.forEach((type) => {
    getData(type);
  });
};

const getInstantData = () => {
  statisticsTypes.value.forEach(async (type) => {
    chartLoading.value[type as keyof IChartDataLoading] = true;
    try {
      statistics.value[type as keyof IStatisticsType] = await queryMetricsInstant(
        apigwId.value,
        {
          ...getMetricsBaseParams(),
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
  }

  timeId = setInterval(refreshData, time);
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
  if (gatewayStore.isAIGateway) {
    syncAIParamsToCharts();
  }
};

const syncAIParamsToCharts = () => {
  const params = { ...searchParams.value };
  llmLatency95thRef.value?.syncParams(params);
  llmToken95thRef.value?.syncParams(params);
  llmLatencyAvgRef.value?.syncParams(params);
  llmTokenUsageRef.value?.syncParams(params);
  llmActiveConnectionsRef.value?.syncParams(params);
};

watch(() => gatewayStore.isAIGateway, async (isAIGateway) => {
  if (!isAIGateway || !searchParams.value.stage_id) {
    return;
  }

  await nextTick();
  syncAIParamsToCharts();
  aiMetricsList.forEach((type) => {
    getData(type);
  });
});

// 按当前时间解析所选范围：绝对范围固定不变，相对范围（最近 N 分钟、今天等）随时间推进
const resolveTimeRange = () => resolveDatePickerRange(dateTime.value);

// 写入本轮查询的时间快照；值有变化时由 searchParams 的 watch 统一请求全部数据并同步到子图
const applyTimeRange = (range: TimeRangeSeconds) => {
  searchParams.value.time_start = range[0];
  searchParams.value.time_end = range[1];
};

// 自动刷新：先重新解析时间；快照未变化（如绝对范围）时直接重新请求
const refreshData = () => {
  const range = resolveTimeRange();
  if (range && (range[0] !== searchParams.value.time_start || range[1] !== searchParams.value.time_end)) {
    applyTimeRange(range);
    return;
  }
  getPageData();
  getInstantData();
};

const stopAutoRefresh = () => {
  if (timeId) {
    clearInterval(timeId);
    timeId = null;
  }
};

const handleRefreshChange = (interval: string) => {
  stopAutoRefresh();
  setIntervalFn(interval);
};

const handleStepChange = (value: MetricsStep) => {
  step.value = value;
  getPageData();
};

const handleClearParams = () => {
  const range = resolveTimeRange();
  searchParams.value = {
    stage_id: stageList.value[0]?.id,
    resource_id: '',
    time_start: range?.[0] ?? searchParams.value.time_start,
    time_end: range?.[1] ?? searchParams.value.time_end,
    metrics: '' as ISearchParamsType['metrics'],
    backend_name: '',
  };
  backend_id.value = '';
  topRef.value?.reset();
};

const handleReportInit = () => {
  init();
};

// 选择变化：解析组件给出的选择值，不使用随显示格式变化的 formatText
const handleValueChange = (value: DateValue | undefined) => {
  const range = resolveDatePickerRange(value);
  if (!range) {
    Message({
      theme: 'error',
      message: t('时间范围无效，请重新选择'),
    });
    return;
  }
  applyTimeRange(range);
};

// 按当前查询参数请求全部指标，并同步到子图
const loadAll = () => {
  getPageData();
  getInstantData();
  syncParamsToCharts();
};

// 首次加载必须显式请求：带环境参数进入时环境已预先写入，同一秒内重新解析的时间也可能与初始值相同，
// 查询参数没有变化就不会触发 watch
const init = async () => {
  isInitializing = true;
  try {
    await Promise.all([
      getStages(),
      getResources(),
      getBackendServices(),
    ]);
    const range = resolveTimeRange();
    if (range) {
      applyTimeRange(range);
    }
    // 等待初始化期间排队的 watch 回调执行完（会被跳过）
    await nextTick();
  }
  finally {
    isInitializing = false;
  }
  loadAll();
};

onMounted(() => {
  init();
});

// 离开页面时停止自动刷新，避免旧定时器继续请求
onBeforeUnmount(() => {
  stopAutoRefresh();
});

</script>

<style lang="scss" scoped>

.ag-top-header {
  padding: 24px 24px 0;
}

.search-form {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 16px;
  flex: 1;
  min-width: 0;

  :deep(.bk-form-item) {
    display: flex;
    max-width: fit-content;
    min-width: auto;
    margin: 0;
    align-items: center;
    flex: 1;

    .bk-form-label {
      width: auto;
      padding-right: 8px !important;
      text-align: right;
      white-space: nowrap;
    }

    .bk-form-content {
      line-height: normal;

      .bk-input,
      .bk-user-selector,
      .member-selector {
        width: 100%;
      }
    }
  }
}

.statistics {
  padding: 24px 24px 32px;

  .ai-metrics-title {
    margin: 24px 0 16px;
    font-size: 16px;
    font-weight: 700;
    line-height: 24px;
    color: #313238;
  }

  .line-container {
    display: flex;
    margin-bottom: 16px;
    align-items: stretch;
  }

  .requests {

    .total-requests {
      display: flex;
      width: 200px;
      height: 320px;
      margin-right: 16px;
      background: #FFF;
      border-radius: 2px;
      box-shadow: 0 1px 2px 0 #0000001a;
      flex-direction: column;
      justify-content: center;
      align-items: center;

      .title {
        margin-bottom: 24px;
        font-size: 14px;
        line-height: 18px;
        color: #63656E;
      }

      .number {
        font-size: 32px;
        font-weight: bold;
        line-height: 32px;
        color: #313238;
      }
    }

    .success-requests {
      flex: 1;
      min-width: 0;
      margin-right: 16px;
      background: #FFF;
      border-radius: 2px;
      box-shadow: 0 2px 4px 0 #1919290d;
    }

    .error-requests {
      flex: 1;
      min-width: 0;
      background: #FFF;
      border-radius: 2px;
      box-shadow: 0 2px 4px 0 #1919290d;
    }
  }

  .secondary-panel {

    .secondary-lf {
      flex: 1;
      min-width: 0;
      padding-bottom: 6px;
      margin-right: 16px;
      background: #FFF;
      border-radius: 2px;
      box-shadow: 0 2px 4px 0 #1919290d;
    }

    .secondary-rg {
      flex: 1;
      min-width: 0;
      padding-bottom: 6px;
      background: #FFF;
      border-radius: 2px;
      box-shadow: 0 2px 4px 0 #1919290d;
    }
  }

  .full-line {
    padding-bottom: 12px;
    margin-bottom: 16px;
    background: #FFF;
    border-radius: 2px;
    box-shadow: 0 2px 4px 0 #1919290d;
  }
}

.full-box {
  width: 100%;
  height: 100%;
}
</style>
