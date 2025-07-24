<template>
  <div class="page-wrapper-padding app-content">
    <div class="ag-top-header">
      <BkForm
        class="search-form"
        form-type="vertical"
      >
        <BkFormItem :label="t('日期选择器')">
          <DatePicker
            v-model="dateTime"
            :valid-date-range="['now-6M', 'now/d']"
            format="YYYY-MM-DD HH:mm:ss"
            class="date-choose"
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
            style="min-width: 296.5px;"
            @change="handleSearchChange()"
          />
        </BkFormItem>
        <BkFormItem :label="t('蓝鲸应用')">
          <BkSelect
            v-model="searchParams.bk_app_code"
            style="min-width: 296.5px;"
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
      </BkForm>
    </div>

    <div class="page-content">
      <div class="time-dimension">
        <div class="title">
          {{ t('显示方式') }}
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
            <div
              class="tool download"
              @click="() => handleDownload('requests_total')"
            >
              <AgIcon name="download" />
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
            <div
              class="tool download"
              @click="() => handleDownload('requests_failed_total')"
            >
              <AgIcon name="download" />
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
import DatePicker from '@blueking/date-picker';
import '@blueking/date-picker/vue3/vue3.css';
import {
  type IChartDataLoading,
  exportReportSummary,
  getCallers,
  getReportSummary,
} from '@/services/source/report';
import {
  getApigwResources,
  getApigwStages,
} from '@/services/source/dashboard';
import Chart from './components/Chart.vue';
import AgIcon from '@/components/ag-icon/Index.vue';
import ResourceSearcher from '@/views/operate-data/dashboard/components/ResourceSearcher.vue';

type InfoTypeItem = {
  formatText: null | string
  dayjs: dayjs.Dayjs | null
};

const { t } = useI18n();
const gatewayStore = useGateway();
const accessLogStore = useAccessLog();

const dateTime = ref(['now-30d', 'now']);
const formatTime = ref<string[]>([dayjs().subtract(30, 'day')
  .format('YYYY-MM-DD HH:mm:ss'),
dayjs().format('YYYY-MM-DD HH:mm:ss')]);
const searchParams = reactive<any>({
  stage_id: '',
  resource_id: '',
  time_start: '',
  time_end: '',
  time_dimension: 'day',
  bk_app_code: '',
  metrics: '',
});
const stageList = ref<any>([]);
const resourceList = ref<any>([]);
const callerOptions = ref<any>([]);
const chartData = ref<any>({});
const chartLoading = ref<IChartDataLoading>({});
const requestsTotalRef = ref();
const requestsFailedTotalRef = ref();

const metricsList = ref<string[]>([
  'requests_total', // 请求总数
  'requests_failed_total', // 请求失败总数
]);

const apigwId = computed(() => gatewayStore.apigwId);

watch(
  () => [
    formatTime.value,
    searchParams.stage_id,
  ],
  () => {
    setSearchTimeRange();
    getCallersData();
  },
);

const getStages = async () => {
  const pageParams = {
    no_page: true,
    order_by: 'name',
  };

  try {
    const res = await getApigwStages(apigwId.value, pageParams);

    stageList.value = res;
    if (!searchParams.stage_id) {
      searchParams.stage_id = stageList.value[0]?.id;
    }
  }
  catch (err) {
    console.log(err);
  }
};

const getCallersData = async () => {
  const pageParams = {
    stage_id: searchParams.stage_id,
    time_start: searchParams.time_start,
    time_end: searchParams.time_end,
  };

  try {
    const res = await getCallers(apigwId.value, pageParams);
    callerOptions.value = res?.app_codes || [];
  }
  catch (err) {
    console.log(err);
  }
};

const getResources = async () => {
  const pageParams = {
    no_page: true,
    order_by: 'path',
    offset: 0,
    limit: 10000,
  };

  try {
    const res = await getApigwResources(apigwId.value, pageParams);
    resourceList.value = res.results;
  }
  catch (err) {
    console.log(err);
  }
};

const handleRefresh = async (metrics: string) => {
  try {
    setSearchTimeRange();
    chartLoading.value[metrics] = true;

    const params = {
      ...searchParams,
      metrics,
    };

    const res = await getReportSummary(apigwId.value, params);

    chartData.value[metrics] = res;
  }
  catch (e) {
    console.log(e);
  }
  finally {
    chartLoading.value[metrics] = false;
  }
};

const handleDownload = async (metrics: string) => {
  try {
    setSearchTimeRange();
    const params = {
      ...searchParams,
      metrics,
    };

    await exportReportSummary(apigwId.value, params);

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
};

const getChartData = async () => {
  metricsList.value?.forEach((metrics: string) => {
    chartLoading.value[metrics] = true;
  });

  setSearchTimeRange();

  const requests = metricsList.value?.map((metrics: string) => {
    const params = {
      ...searchParams,
      metrics,
    };

    return getReportSummary(apigwId.value, params);
  });

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
  const [time_start, time_end] = formatTime.value;
  if (time_start && time_end) {
    searchParams.time_start = dayjs(time_start).unix();
    searchParams.time_end = dayjs(time_end).unix();
  }
};

const handleValueChange = (value: string[], info: InfoTypeItem[]) => {
  const [startTime, endTime] = info;
  formatTime.value = [startTime?.formatText, endTime?.formatText];
  handleSearchChange();
};

const syncParamsToCharts = () => {
  requestsTotalRef.value!.syncParams(searchParams);
  requestsFailedTotalRef.value!.syncParams(searchParams);
};

const handleSearchChange = () => {
  getChartData();
  syncParamsToCharts();
};

const resetParams = () => {
  searchParams.stage_id = stageList.value[0]?.id;
  searchParams.resource_id = '';
  searchParams.time_dimension = 'day';
  searchParams.bk_app_code = '';
  searchParams.metrics = '';

  searchParams.time_start = '';
  searchParams.time_end = '';
  dateTime.value = ['now-30d', 'now'];
  formatTime.value = [dayjs().subtract(30, 'day')
    .format('YYYY-MM-DD HH:mm:ss'),
  dayjs().format('YYYY-MM-DD HH:mm:ss')];
};

const handleClearParams = () => {
  resetParams();
  handleSearchChange();
};

const init = async () => {
  await getResources();
  await getStages();
  handleSearchChange();
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
      font-size: 14px;
      color: #4D4F56;
      margin-bottom: 8px;
    }
    .time-radio {
      background: #FFFFFF;
    }
  }
  .charts-wrapper {
    display: flex;
    .charts-item-outbox {
      height: 396px;
      padding-top: 16px;
      box-sizing: border-box;
      flex: 1;
      position: relative;
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
        display: flex;
        align-items: center;
        display: none;
        .tool {
          width: 28px;
          height: 28px;
          border-radius: 2px;
          background: #FAFBFD;
          border: 1px solid #DCDEE5;
          display: flex;
          align-items: center;
          justify-content: center;
          cursor: pointer;
          i {
            color: #979BA5;
            font-size: 16px;
          }
          &.download {
            i {
              font-size: 20px;
            }
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
      height: 380px;
      width: 100%;
      background: #FFFFFF;
      border-radius: 2px;
      box-shadow: 0 2px 4px 0 #1919290d;
    }
  }
}

.search-form {
  width: 100%;
  display: flex;
  flex-wrap: wrap;
  gap: 0 16px;
}

.date-choose {
  min-width: 154px;
  background: #fff;
  flex-shrink: 0;
}
</style>
