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
  <div class="page-wrapper-padding app-content">
    <div class="mb-24px">
      <BkForm
        class="search-form"
        label-width="auto"
      >
        <BkFormItem :label="t('选择时间')">
          <DatePicker
            v-model="dateTime"
            :valid-date-range="['now-180d', 'now/d']"
            format="YYYY-MM-DD HH:mm:ss"
            class="date-choose"
            :need-timezone="false"
            :common-use-list="accessLogStore.commonUseList"
            @update:model-value="handleValueChange"
          />
        </BkFormItem>
        <BkFormItem :label="t('环境')">
          <BkSelect
            v-model="searchParams.stage_id"
            :clearable="false"
            filterable
            :input-search="false"
            style="width: 150px;"
            @change="handleSearchChange()"
          >
            <BkOption
              v-for="option in stageList"
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
            style="min-width: 300px;"
            @change="handleSearchChange()"
          />
        </BkFormItem>
        <BkFormItem :label="t('蓝鲸应用')">
          <BkSelect
            v-model="searchParams.bk_app_code"
            filterable
            style="min-width: 300px;"
            @change="handleSearchChange()"
          >
            <BkOption
              v-for="option in callerOptions"
              :id="option"
              :key="option"
              :name="option"
            />
          </BkSelect>
        </BkFormItem>
        <BkFormItem label="">
          <BkButton
            :loading="downloading"
            @click="() => handleDownload()"
          >
            {{ t('导出') }}
            <AgIcon name="download" />
          </BkButton>
        </BkFormItem>
      </BkForm>
    </div>

    <div class="page-content">
      <div class="time-dimension">
        <div class="title">
          {{ t('显示方式') }}
          <span class="title-tips">{{ t('数据按 UTC 自然日统计') }}</span>
        </div>
        <BkRadioGroup
          v-model="searchParams.time_dimension"
          class="time-radio"
          @change="handleSearchChange()"
        >
          <BkRadioButton label="day">
            {{ t('按日') }}
          </BkRadioButton>
          <BkRadioButton label="week">
            {{ t('按周') }}
          </BkRadioButton>
          <BkRadioButton label="month">
            {{ t('按月') }}
          </BkRadioButton>
        </BkRadioGroup>
      </div>

      <div class="charts-wrapper">
        <div class="charts-item-outbox">
          <div class="charts-tools">
            <div
              class="tool refresh"
              @click="() => handleRefresh('requests_total')"
            >
              <AgIcon name="refresh-line" />
            </div>
          </div>
          <div class="charts-item">
            <BkLoading :loading="chartLoading['requests_total']">
              <Chart
                ref="requestsTotalRef"
                :title="t('请求总数')"
                :chart-data="chartData['requests_total']"
                instance-id="requests_total"
                @clear-params="handleClearParams"
                @report-init="handleClearParams"
              />
            </BkLoading>
          </div>
        </div>
        <div class="charts-item-outbox">
          <div class="charts-tools">
            <div
              class="tool refresh"
              @click="() => handleRefresh('requests_failed_total')"
            >
              <AgIcon name="refresh-line" />
            </div>
          </div>
          <div class="charts-item">
            <BkLoading :loading="chartLoading['requests_failed_total']">
              <Chart
                ref="requestsFailedTotalRef"
                :title="t('请求失败总数')"
                :chart-data="chartData['requests_failed_total']"
                instance-id="requests_failed_total"
                @clear-params="handleClearParams"
                @report-init="handleClearParams"
              />
            </BkLoading>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script lang="ts" setup>
import dayjs from 'dayjs';
import { Message } from 'bkui-vue';
import { useAccessLog, useGateway } from '@/stores';
import DatePicker, { type DateValue } from '@blueking/date-picker';
import '@blueking/date-picker/vue3/vue3.css';
import {
  exportMetricsSummary,
  getMetricsSummary,
  getMetricsSummaryCallers,
} from '@/services/source/gateway/metrics';
import { getResourceList } from '@/services/source/gateway/resource';
import { getStageList } from '@/services/source/gateway/stage';
import Chart from './components/Chart.vue';
import AgIcon from '@/components/base/ag-icon/Index.vue';
import ResourceSearcher from '@/views/operate-data/dashboard/components/ResourceSearcher.vue';
import {
  type TimeRangeSeconds,
  floorToUtcDay,
  getRecentRange,
} from '@/utils/time-range';
import { resolveDatePickerRange } from '@/utils/date-picker-range';

type SummaryMetrics = Parameters<typeof getMetricsSummary>[1]['metrics'];
type TimeDimension = Parameters<typeof getMetricsSummary>[1]['time_dimension'];

// 报表筛选状态；发送请求前由 getSummaryBaseParams 转为接口参数
interface IReportSearchParams {
  stage_id?: number
  // 资源选择器的选中值，未选择时为空字符串
  resource_id: number | string
  bk_app_code: string
  time_dimension: TimeDimension
  // 当前时间快照（Unix 秒），由 setSearchTimeRange 写入
  time_start: number
  time_end: number
}

const { t } = useI18n();
const gatewayStore = useGateway();
const accessLogStore = useAccessLog();

// 日期组件的选择值：相对表达式或绝对毫秒时间戳
const dateTime = ref<DateValue>(['now-30d', 'now']);
// 本轮查询使用的时间快照（秒），已对齐到报表的 UTC 日桶；汇总、调用方列表、导出共用
const timeRange = ref<TimeRangeSeconds>(getRecentRange(30, 'day'));
const searchParams = reactive<IReportSearchParams>({
  stage_id: undefined,
  resource_id: '',
  time_start: timeRange.value[0],
  time_end: timeRange.value[1],
  time_dimension: 'day',
  bk_app_code: '',
});
const stageList = ref<any>([]);
const resourceList = ref<any>([]);
const callerOptions = ref<any>([]);
const chartData = ref<Record<string, any>>({});
const downloading = ref(false);
const chartLoading = ref<Record<string, boolean>>({});
const requestsTotalRef = ref();
const requestsFailedTotalRef = ref();

const metricsList = ref<SummaryMetrics[]>([
  'requests_total', // 请求总数
  'requests_failed_total', // 请求失败总数
]);

const apigwId = computed(() => gatewayStore.apigwId);

watch(
  () => [
    timeRange.value,
    searchParams.stage_id,
  ],
  () => {
    setSearchTimeRange();
    getCallersData();
  },
);

const getStages = async () => {
  const pageParams: Parameters<typeof getStageList>[1] = {};

  try {
    const res = await getStageList(apigwId.value, pageParams);

    stageList.value = res;
    if (!searchParams.stage_id) {
      searchParams.stage_id = stageList.value[0]?.id;
    }
  }
  catch (err) {
    console.log(err);
  }
};

// 汇总、调用方、导出的公共参数：时间为当前快照（秒），须成对传；资源、应用为空时不传
const getSummaryBaseParams = () => ({
  resource_id: searchParams.resource_id ? Number(searchParams.resource_id) : undefined,
  bk_app_code: searchParams.bk_app_code || undefined,
  time_start: searchParams.time_start,
  time_end: searchParams.time_end,
});

const getCallersData = async () => {
  if (searchParams.stage_id === undefined) {
    return;
  }

  const pageParams = {
    stage_id: searchParams.stage_id,
    time_start: searchParams.time_start,
    time_end: searchParams.time_end,
  };

  try {
    const res = await getMetricsSummaryCallers(apigwId.value, pageParams);
    callerOptions.value = (res as any)?.app_codes || [];
  }
  catch (err) {
    console.log(err);
  }
};

const getResources = async () => {
  const pageParams: Parameters<typeof getResourceList>[1] = {
    no_page: true,
    order_by: 'path',
    offset: 0,
    limit: 10000,
  };

  try {
    const res = await getResourceList(apigwId.value, pageParams);
    resourceList.value = res.results;
  }
  catch (err) {
    console.log(err);
  }
};

// 单图刷新：先按当前时间重新解析；快照有变化时刷新全部，保证两张图与调用方列表的时间范围一致
const handleRefresh = async (metrics: SummaryMetrics) => {
  const previousRange = timeRange.value;
  if (!updateTimeRange()) {
    return;
  }
  if (timeRange.value !== previousRange) {
    loadCharts();
    return;
  }
  if (searchParams.stage_id === undefined) {
    return;
  }

  try {
    setSearchTimeRange();
    chartLoading.value[metrics] = true;

    const res = await getMetricsSummary(apigwId.value, {
      ...getSummaryBaseParams(),
      stage_id: searchParams.stage_id,
      time_dimension: searchParams.time_dimension,
      metrics,
    });

    chartData.value[metrics] = res;
  }
  catch (e) {
    console.log(e);
  }
  finally {
    chartLoading.value[metrics] = false;
  }
};

// 导出沿用当前快照，与页面展示的数据范围一致
const handleDownload = async () => {
  downloading.value = true;
  try {
    setSearchTimeRange();
    await exportMetricsSummary(apigwId.value, {
      ...getSummaryBaseParams(),
      stage_id: searchParams.stage_id,
    });

    Message({
      theme: 'success',
      message: t('导出成功'),
    });
  }
  catch (err) {
    console.log(err);
    Message({
      theme: 'error',
      message: t('导出失败'),
    });
  }
  finally {
    downloading.value = false;
  }
};

const getChartData = async () => {
  const stageId = searchParams.stage_id;
  if (stageId === undefined) {
    return;
  }

  metricsList.value?.forEach((metrics) => {
    chartLoading.value[metrics] = true;
  });

  setSearchTimeRange();

  const requests = metricsList.value?.map(metrics => getMetricsSummary(apigwId.value, {
    ...getSummaryBaseParams(),
    stage_id: stageId,
    time_dimension: searchParams.time_dimension,
    metrics,
  }));

  try {
    const res = await Promise.all(requests);
    chartData.value = {};
    metricsList.value?.forEach((metrics: string, index: number) => {
      chartData.value[metrics] = res[index];
    });
  }
  catch (err) {
    console.log(err);
  }
  finally {
    metricsList.value?.forEach((metrics: string) => {
      chartLoading.value[metrics] = false;
    });
  }
};

const setSearchTimeRange = () => {
  [searchParams.time_start, searchParams.time_end] = timeRange.value;
};

/**
 * 对齐到报表的日桶。后端按 UTC 自然日统计，按桶起点过滤，且起点不得早于服务器时间的半年前：
 * - 起点向下取整到 UTC 0 点，使“近 N 天”包含完整的日桶
 * - 起点再与“当前时间 - 6 个月 + 1 小时”取较晚者，为客户端时钟偏差留出余量
 * @returns 对齐后为空区间时返回 null
 */
const alignToDailyBuckets = (range: TimeRangeSeconds): TimeRangeSeconds | null => {
  const earliestStart = dayjs().subtract(6, 'month')
    .add(1, 'hour')
    .unix();
  const start = Math.max(floorToUtcDay(range[0]), earliestStart);
  return start <= range[1] ? [start, range[1]] : null;
};

/**
 * 按当前时间解析所选范围并更新时间快照；选择无效时提示并保留原快照
 * @returns 快照是否有效
 */
const updateTimeRange = (value: DateValue | undefined = dateTime.value) => {
  const resolved = resolveDatePickerRange(value);
  const range = resolved ? alignToDailyBuckets(resolved) : null;
  if (!range) {
    Message({
      theme: 'error',
      message: t('时间范围无效，请重新选择'),
    });
    return false;
  }
  // 值未变化时保留原数组，避免触发 timeRange 的 watch 重复请求调用方列表
  if (range[0] !== timeRange.value[0] || range[1] !== timeRange.value[1]) {
    timeRange.value = range;
  }
  return true;
};

// 选择变化：解析组件给出的选择值，不使用随显示格式变化的 formatText
const handleValueChange = (value: DateValue | undefined) => {
  if (!updateTimeRange(value)) {
    return;
  }
  loadCharts();
};

const syncParamsToCharts = () => {
  requestsTotalRef.value!.syncParams(searchParams);
  requestsFailedTotalRef.value!.syncParams(searchParams);
};

// 按当前快照请求图表
const loadCharts = () => {
  getChartData();
  syncParamsToCharts();
};

// 查询条件变化：相对范围按当前时间重新解析后再请求
const handleSearchChange = () => {
  if (!updateTimeRange()) {
    return;
  }
  loadCharts();
};

const resetParams = () => {
  searchParams.stage_id = stageList.value[0]?.id;
  searchParams.resource_id = '';
  searchParams.time_dimension = 'day';
  searchParams.bk_app_code = '';

  dateTime.value = ['now-30d', 'now'];
  updateTimeRange();
  setSearchTimeRange();
};

const handleClearParams = () => {
  resetParams();
  loadCharts();
};

const init = async () => {
  // 先确定时间快照，避免获取环境后触发的调用方列表请求使用未对齐的初始范围
  updateTimeRange();
  setSearchTimeRange();
  await getResources();
  await getStages();
  loadCharts();
};

init();

</script>

<style lang="scss" scoped>
.app-content {
  padding-bottom: 24px;
}

.page-content {
  min-height: calc(100vh - 268px);

  .time-dimension {
    // margin-bottom: -16px;

    .title {
      margin-bottom: 8px;
      font-size: 14px;
      color: #4D4F56;

      .title-tips {
        margin-left: 8px;
        font-size: 12px;
        color: #979BA5;
      }
    }

    .time-radio {
      background: #FFF;
    }
  }

  .charts-wrapper {
    display: flex;

    .charts-item-outbox {
      position: relative;
      height: 396px;
      padding-top: 16px;
      box-sizing: border-box;
      flex: 1;

      &:not(:nth-last-child(1)) {
        margin-right: 16px;
      }

      &:hover {

        .charts-tools {
          display: flex;
        }
      }

      .charts-tools {
        position: absolute;
        top: -16px;
        right: 0;
        align-items: center;
        display: none;

        .tool {
          display: flex;
          width: 28px;
          height: 28px;
          cursor: pointer;
          background: #FAFBFD;
          border: 1px solid #DCDEE5;
          border-radius: 2px;
          align-items: center;
          justify-content: center;

          i {
            font-size: 16px;
            color: #979BA5;
          }

          &:not(:nth-last-child(1)) {
            margin-right: 4px;
          }

          &:hover {
            background: #E1ECFF;
            border: 1px solid #3A84FF;

            i {
              color: #3A84FF;
            }
          }
        }
      }
    }

    .charts-item {
      width: 100%;
      height: 380px;
      background: #FFF;
      border-radius: 2px;
      box-shadow: 0 2px 4px 0 #1919290d;
    }
  }
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

.date-choose {
  min-width: 154px;
  background: #fff;
  flex-shrink: 0;
}
</style>
