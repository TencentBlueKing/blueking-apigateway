<template>
  <div class="page-wrapper-padding app-content">
    <div class="ag-top-header">
      <bk-form class="search-form" form-type="vertical">
        <bk-form-item :label="t('环境')">
          <bk-select
            style="width: 316px;"
            v-model="searchParams.stage_id"
            :clearable="false"
            filterable
            :input-search="false"
            @change="handleSearchChange()">
            <bk-option
              v-for="option in stageList"
              :key="option.id"
              :id="option.id"
              :name="option.name">
            </bk-option>
          </bk-select>
        </bk-form-item>
        <bk-form-item :label="t('调用方')">
          <bk-select
            style="width: 316px;"
            v-model="searchParams.bk_app_code"
            @change="handleSearchChange()">
            <bk-option
              v-for="option in callerOptions"
              :key="option"
              :id="option"
              :name="option">
            </bk-option>
          </bk-select>
        </bk-form-item>
        <bk-form-item :label="t('资源')">
          <ResourceSearcher
            v-model="searchParams.resource_id"
            :list="resourceList"
            :need-prefix="false"
            style="width: 316px;"
            @change="handleSearchChange()"
          />
        </bk-form-item>
        <bk-form-item :label="t('日期选择器')">
          <date-picker
            class="date-choose"
            v-model="dateTime"
            @update:model-value="handleValueChange"
            :valid-date-range="['now-6M', 'now/d']"
            format="YYYY-MM-DD HH:mm:ss" />
        </bk-form-item>
      </bk-form>
    </div>

    <div class="page-content">
      <div class="time-dimension">
        <div class="title">{{ t('显示方式') }}</div>
        <bk-radio-group v-model="searchParams.time_dimension" @change="handleSearchChange()" class="time-radio">
          <bk-radio-button label="day">{{ t('按日') }}</bk-radio-button>
          <bk-radio-button label="week">{{ t('按周') }}</bk-radio-button>
          <bk-radio-button label="month">{{ t('按月') }}</bk-radio-button>
        </bk-radio-group>
      </div>

      <div class="charts-wrapper">
        <div class="charts-item-outbox">
          <div class="charts-tools">
            <div class="tool refresh" @click="handleRefresh('requests_total')">
              <i class="apigateway-icon icon-ag-lishijilu"></i>
            </div>
            <div class="tool download" @click="handleDownload('requests_total')">
              <i class="apigateway-icon icon-ag-download"></i>
            </div>
          </div>
          <div class="charts-item">
            <bk-loading :loading="chartLoading['requests_total']">
              <chart
                ref="requestsTotalRef"
                :title="t('请求总数')"
                :chart-data="chartData['requests_total']"
                @clear-params="handleClearParams"
                @report-init="handleClearParams"
                instance-id="requests_total" />
            </bk-loading>
          </div>
        </div>
        <div class="charts-item-outbox">
          <div class="charts-tools">
            <div class="tool refresh" @click="handleRefresh('requests_failed_total')">
              <i class="apigateway-icon icon-ag-lishijilu"></i>
            </div>
            <div class="tool download" @click="handleDownload('requests_failed_total')">
              <i class="apigateway-icon icon-ag-download"></i>
            </div>
          </div>
          <div class="charts-item">
            <bk-loading :loading="chartLoading['requests_failed_total']">
              <chart
                ref="requestsFailedTotalRef"
                :title="t('请求失败总数')"
                :chart-data="chartData['requests_failed_total']"
                @clear-params="handleClearParams"
                @report-init="handleClearParams"
                instance-id="requests_failed_total" />
            </bk-loading>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script lang="ts" setup>
import { ref, reactive, watch } from 'vue';
import dayjs from 'dayjs';
import { Message } from 'bkui-vue';
import { useI18n } from 'vue-i18n';
import { useCommon } from '@/store';
import DatePicker from '@blueking/date-picker';
import '@blueking/date-picker/vue3/vue3.css';
import ResourceSearcher from '@/views/operate-data/dashboard/components/resource-searcher.vue';
import { getApigwStages, getApigwResources, getReportSummary, exportReportSummary, getCallers } from '@/http';
import Chart from './components/chart.vue';
import { ChartDataLoading } from './type';

type InfoTypeItem = {
  formatText: null | string;
  dayjs: dayjs.Dayjs | null;
};

const { t } = useI18n();
const common = useCommon();

const dateTime = ref(['now-30d', 'now']);
const formatTime = ref<string[]>([dayjs().subtract(30, 'day')
  .format('YYYY-MM-DD HH:mm:ss'), dayjs().format('YYYY-MM-DD HH:mm:ss')]);
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
const chartLoading = ref<ChartDataLoading>({});
const requestsTotalRef = ref();
const requestsFailedTotalRef = ref();

const metricsList = ref<string[]>([
  'requests_total', // 请求总数
  'requests_failed_total', // 请求失败总数
]);

const getStages = async () => {
  const { apigwId } = common;
  const pageParams = {
    no_page: true,
    order_by: 'name',
  };

  try {
    const res = await getApigwStages(apigwId, pageParams);

    stageList.value = res;
    searchParams.stage_id = stageList.value[0]?.id;
  } catch (e) {
    console.log(e);
  }
};

const getCallersData = async () => {
  const { apigwId } = common;
  const pageParams = {
    stage_id: searchParams.stage_id,
    time_start: searchParams.time_start,
    time_end: searchParams.time_end,
  };

  try {
    const res = await getCallers(apigwId, pageParams);
    callerOptions.value = res?.app_codes || [];
  } catch (e) {
    console.log(e);
  }
};

const getResources = async () => {
  const { apigwId } = common;
  const pageParams = {
    no_page: true,
    order_by: 'path',
    offset: 0,
    limit: 10000,
  };

  try {
    const res = await getApigwResources(apigwId, pageParams);
    resourceList.value = res.results;
  } catch (e) {
    console.log(e);
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

    const res = await getReportSummary(common.apigwId, params);

    chartData.value[metrics] = res;
  } catch (e) {
    console.log(e);
  } finally {
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

    await exportReportSummary(common.apigwId, params);

    Message({
      theme: 'success',
      message: t('导出成功'),
    });
  } catch (e) {
    console.log(e);
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

  const { apigwId } = common;
  setSearchTimeRange();

  const requests = metricsList.value?.map((metrics: string) => {
    const params = {
      ...searchParams,
      metrics,
    };

    return getReportSummary(apigwId, params);
  });

  try {
    const res = await Promise.all(requests);
    chartData.value = {};
    metricsList.value?.forEach((metrics: string, index: number) => {
      chartData.value[metrics] = res[index];
    });
  } catch (e) {
    console.log(e);
  } finally {
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
    .format('YYYY-MM-DD HH:mm:ss'), dayjs().format('YYYY-MM-DD HH:mm:ss')];
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

watch(
  () => [formatTime.value, searchParams.stage_id],
  () => {
    setSearchTimeRange();
    getCallersData();
  },
);
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
  :deep(.bk-form-item) {
    margin-right: 16px;
  }
  .date-choose {
    background: #FFFFFF;
  }
}
</style>
