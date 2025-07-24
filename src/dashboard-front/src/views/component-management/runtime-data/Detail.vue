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
  <div class="runtime-data-content">
    <div class="top-header m-b-16px">
      <div class="filter">
        <strong class="title">
          {{ systemName }}
          <span
            v-if="principalFlag"
            class="text-[12px]"
          >
            （{{ t('负责人：') }}{{ summaryData?.basic_info?.maintainers?.join(', ') }}）
          </span>
        </strong>
        <div class="auto-refresh">
          <BkSwitcher
            v-model="autoEnable"
            class="m-r-10px"
            theme="primary"
          />
          <span class="vm text-[13px]">
            {{ t('每分钟自动刷新') }}
          </span>
        </div>
      </div>
    </div>
    <div class="chart-box">
      <ChartView
        :start-time="dayStartTime"
        :end-time="endTime"
        @time-change="handleTimeChange"
      />
    </div>

    <BkLoading :loading="isSummaryDataLoading">
      <div class="card-box">
        <div class="card">
          <div class="value">
            {{ summaryData?.requests?.count_str || '--' }}
          </div>
          <div class="key">
            {{ t('请求数') }}
          </div>
        </div>
        <div class="card">
          <div class="value">
            {{ summaryData?.rate_availability?.value_str || '--' }}%
          </div>
          <div class="key">
            {{ t('可用率') }}
            <span
              v-if="summaryData?.rate_availability?.value < 1"
              v-bk-tooltips="t('该系统在指定时间范围内可用率低于100%')"
            >
              <i class="apigateway-icon icon-ag-info" />
            </span>
          </div>
        </div>
        <div class="card">
          <div class="value">
            {{ summaryData?.perc95_resp_time?.value_str || '--' }}ms
          </div>
          <div class="key">
            {{ t('统计响应时间') }}
            <span
              v-if="summaryData?.rate_availability?.value < 1"
              v-bk-tooltips="t('根据百分位计算出的响应时间，相比平均响应时间，更能反映问题')"
            >
              <i class="apigateway-icon icon-ag-help" />
            </span>
          </div>
        </div>
      </div>
    </BkLoading>

    <div class="runtime-container">
      <BkTab
        v-model:active="active"
        type="unborder-card"
        @tab-change="handleTabChange"
      >
        <BkTabPanel
          name="req_component_name"
          :label="t('按组件')"
        >
          <BkLoading :loading="isDataLoading">
            <BkTable
              size="small"
              :data="requests"
              :columns="getTableColumns"
              :border="false"
              :outer-border="false"
              header-border
            />
          </BkLoading>
        </BkTabPanel>

        <BkTabPanel
          name="req_app_code"
          :label="t('按APP')"
        >
          <BkLoading :loading="isDataLoading">
            <BkTable
              size="small"
              :data="requests"
              :columns="getTableColumns"
              :border="false"
              :outer-border="false"
              header-border
            />
          </BkLoading>
        </BkTabPanel>

        <BkTabPanel
          name="req_url"
          :label="t('按URL')"
        >
          <BkLoading :loading="isDataLoading">
            <BkTable
              size="small"
              :data="requests"
              :columns="getTableColumns"
              :border="false"
              :outer-border="false"
              header-border
            />
          </BkLoading>
        </BkTabPanel>
      </BkTab>
    </div>

    <BkDialog
      :is-show="detailDialog.visible"
      theme="primary"
      :width="900"
      :quick-close
      :header-align="'left'"
      :title="t('错误请求详情')"
      dialog-type="show"
      @closed="detailDialog.visible = false"
    >
      <BkLoading :loading="isErrorDataLoading">
        <div>
          <div class="m-b-10px">
            <strong>{{ detailDialog.name }}</strong>
          </div>
          <BkAlert
            class="m-b-10px"
            type="info"
            :title="t('此处最多展示最近 200 条错误信息')"
          />
          <BkTable
            :data="errorRequests"
            header-border
            :max-height="400"
            :size="'small'"
          >
            <BkTableColumn
              :label="t('时间')"
              prop="datetime"
              width="120"
            />
            <BkTableColumn
              :label="t('错误信息')"
              prop="message"
            />
            <BkTableColumn
              :label="t('耗时')"
              prop="time"
              width="120"
            />
            <BkTableColumn
              :label="t('响应状态')"
              prop="status"
              width="80"
            />
          </BkTable>
        </div>
      </BkLoading>
    </BkDialog>
  </div>
</template>

<script lang="tsx" setup>
import ChartView from './Chart';
import moment from 'moment';
import {
  type ITimeChartResponse,
  getApigwErrorRequest,
  getApigwRuntimeRequest,
  getApigwSystemSummary,
} from '@/services/source/runTime';

const route = useRoute();
const { t } = useI18n();

const active = ref('req_component_name');
const systemName = ref<string | string[]>();
const system = ref<string | string[]>();
const timer = ref(0);
const autoEnable = ref(true);
const detailDialog = reactive({
  name: '',
  visible: false,
});
const requests = ref([]);
const endTime = ref(Date.now());
const startTime = ref(Date.now() - 60 * 60 * 1000);
const dayStartTime = ref(Date.now() - 24 * 60 * 60 * 1000);
const isDataLoading = ref(true);
const isSummaryDataLoading = ref(true);
const summaryData = ref({
  avg_resp_time: { value: '' },
  perc95_resp_time: { value_str: '' },
  rate_availability: { value_str: '' },
  requests: { count_str: '' },
});
const isErrorDataLoading = ref(false);
const errorRequests = ref([]);
const initColumns = ref([
  {
    label: t('序列'),
    type: 'index',
    width: 60,
  },
  {
    label: t('错误 / 总次数'),
    field: 'error_count',
    sort: true,
    sortFn: handleSortCount,
    render: ({ row }: { row?: ITimeChartResponse }) => {
      return (
        <div>
          <span>
            { row?.requests?.error_count }
            /
          </span>
          <span>{ row?.requests?.count }</span>
          <BkButton
            v-if="row?.requests?.error_count"
            text
            class="m-l-5px"
            onClick={() => handleShowDetail(row)}
          >
            { t('详情') }
          </BkButton>
        </div>
      );
    },
  },
  {
    label: t('统计响应时间(ms)'),
    field: 'perc95_resp_time',
    sort: true,
    sortFn: handleSortRespTime,
    render: ({ row }: { row?: ITimeChartResponse }) => {
      return (
        <span>
          { row?.perc95_resp_time?.value }
        </span>
      );
    },
  },
  {
    label: t('平均响应时间(ms)'),
    field: 'avg_resp_time',
    sort: true,
    sortFn: handleSortAvgTime,
    render: ({ row }: { row?: ITimeChartResponse }) => {
      return (
        <span>
          { row?.avg_resp_time?.value }
        </span>
      );
    },
  },
  {
    label: t('可用率'),
    field: 'rate_availability',
    sort: true,
    sortFn: handleSortRate,
    render: ({ row }: { row?: ITimeChartResponse }) => {
      return (
        <span>
          { row?.rate_availability?.value_str }
          %
        </span>
      );
    },
  },
]);

const principalFlag = computed(() => {
  if (summaryData.value?.basic_info?.maintainers?.length) {
    return true;
  }
  return false;
});

const getTableColumns = computed(() => {
  const tabMap = {
    req_app_code: () => {
      const results = [...initColumns.values.slice(0, 1),
        [{
          label: 'app_code',
          field: 'req_app_code',
        }],
        ...initColumns.values.slice(1)];
      return results;
    },
    req_component_name: () => {
      const results = [...initColumns.values.slice(0, 1),
        [{
          label: t('组件名'),
          field: 'req_component_name',
        }],
        ...initColumns.values.slice(1)];
      return results;
    },
    req_url: () => {
      const results = [...initColumns.values.slice(0, 1),
        [{
          label: 'URL',
          field: 'req_url',
        }],
        ...initColumns.values.slice(1)];
      return results;
    },
  };
  return tabMap[active]?.() ?? tabMap['req_component_name']?.();
});

const init = () => {
  getRuntimeRequest();
  getSystemSummary();
  enableAutoRefresh();
};

const getRuntimeRequest = async () => {
  isDataLoading.value = true;
  try {
    const res = await getApigwRuntimeRequest({
      type: active.value,
      system: system.value,
      start: startTime.value,
      end: endTime.value,
    });
    requests.value = res;
  }
  catch (e) {
    console.log(e);
  }
  finally {
    isDataLoading.value = false;
  }
};

const handleSortCount = (a: Record<string, any>, b: Record<string, any>) => {
  if (a.requests.count < b.requests.count) {
    return -1;
  }
  if (a.requests.count > b.requests.count) {
    return 1;
  }
  return 0;
};

const handleSortRespTime = (a: Record<string, any>, b: Record<string, any>) => {
  if (a.perc95_resp_time.value < b.perc95_resp_time.value) {
    return -1;
  }
  if (a.perc95_resp_time.value > b.perc95_resp_time.value) {
    return 1;
  }
  return 0;
};

const handleSortAvgTime = (a: Record<string, any>, b: Record<string, any>) => {
  if (a.avg_resp_time.value < b.avg_resp_time.value) {
    return -1;
  }
  if (a.avg_resp_time.value > b.avg_resp_time.value) {
    return 1;
  }
  return 0;
};

const handleSortRate = (a: Record<string, any>, b: Record<string, any>) => {
  if (a.rate_availability.value < b.rate_availability.value) {
    return -1;
  }
  if (a.rate_availability.value > b.rate_availability.value) {
    return 1;
  }
  return 0;
};

const getSystemSummary = async () => {
  isSummaryDataLoading.value = true;
  try {
    const res = await getApigwSystemSummary({
      system: system.value,
      start: startTime.value,
      end: endTime.value,
    });
    summaryData.value = res;
  }
  finally {
    isSummaryDataLoading.value = false;
  }
};

const handleTimeChange = (start: number, end: number) => {
  startTime.value = start;
  endTime.value = end;
  init();
};

const handleTabChange = (name: string) => {
  active.value = name;
  getRuntimeRequest();
};

const enableAutoRefresh = () => {
  clearInterval(timer.value);
  if (!autoEnable.value) {
    return false;
  }
  timer.value = window.setInterval(() => {
    init();
  }, 1000 * 60);
};

const clearAutoRefresh = () => {
  clearInterval(timer.value);
};

const handleShowDetail = async (data: ITimeChartResponse) => {
  isErrorDataLoading.value = true;
  errorRequests.value = [];
  detailDialog.visible = true;
  detailDialog.name = data.req_app_code || data.req_component_name || data.req_url || '--';

  try {
    const res = await getApigwErrorRequest({
      system: system.value,
      appCode: data.req_app_code || '',
      componentName: data.req_component_name || '',
      requestUrl: data.req_url || '',
      start: startTime.value,
      end: endTime.value,
    });
    errorRequests.value = res.data.data_list.map((item) => {
      const datetime = moment(item.timestamp).format('MM-DD HH:mm');
      const endTime = moment(item.req_end_time).valueOf();
      const startTime = moment(item.req_start_time).valueOf();
      const time = endTime - startTime;
      return {
        datetime,
        message: item.req_exception,
        status: item.req_status,
        time: `${time}ms`,
      };
    });
  }
  finally {
    isErrorDataLoading.value = false;
  }
};

const getRouteData = () => {
  const { params, query } = route;
  system.value = params?.system;
  systemName.value = query?.systemName;
  route.meta.title = `${t('系统实时概况')}`;
};
getRouteData();

init();

watch(
  () => autoEnable.value,
  () => {
    enableAutoRefresh();
  },
);

watch(
  () => detailDialog.visible,
  (value) => {
    if (value) {
      clearAutoRefresh();
    }
    else {
      enableAutoRefresh();
    }
  },
);
</script>

<style lang="scss" scoped>
.runtime-data-content {
  padding: 24px;

  .chart-box {
    width: 100%;
    background-color: #ffffff;
    border: 1px solid #dcdee5;
    border-radius: 2px;
    margin-bottom: 20px;
    padding: 10px;
  }

  .title {
    color: #63656e;
    font-weight: normal;
  }

  .runtime-container {
    background-color: #ffffff;
    border: 1px solid #dcdee5;
    border-radius: 2px;
  }

  .auto-refresh  {
    float: right;
  }

  .card-box {
    background-color: #ffffff;
    border: 1px solid #dcdee5;
    border-radius: 2px;
    margin-bottom: 20px;
    display: flex;
    padding: 20px 0;

    .card {
      text-align: center;
      flex: 1;
      border-left: 1px solid #eee;

      .value {
        font-size: 40px;
        color: #63656e;
      }

      .key {
        font-size: 14px;
        color: #979ba5;
      }
    }
  }
}
</style>
