<template>
  <div class="app-content">
    <div class="top-header mb15">
      <div class="filter" style="overflow: hidden;">
        <strong
          class="title"
          style="color: #63656e; font-weight: normal;">
          {{ systemName }}
          <span class="f12" v-if="principalFlag">
            （{{ t('负责人：') }}{{summaryData.basic_info.maintainers.join(', ')}}）
          </span>
        </strong>
        <div class="auto-refresh fr">
          <bk-switcher
            class="mr10"
            v-model="autoEnable"
            theme="primary">
          </bk-switcher>
          <span class="vm f13">
            {{ t('每分钟自动刷新') }}
          </span>
        </div>
      </div>
    </div>
    <div class="chart-box">
      <chart-view @time-change="handlTimeChnage" :start-time="dayStartTime" :end-time="endTime"></chart-view>
    </div>

    <div class="card-box" v-bkloading="{ isLoading: isSummaryDataLoading }">
      <div class="card">
        <div class="value">{{summaryData.requests.count_str || '--'}}</div>
        <div class="key"> {{ t('请求数') }} </div>
      </div>
      <div class="card">
        <div class="value">{{summaryData.rate_availability.value_str || '--'}}%</div>
        <div class="key">
          {{ t('可用率') }}
          <span v-bk-tooltips="t('该系统在指定时间范围内可用率低于100%')" v-if="summaryData.rate_availability.value < 1">
            <i class="apigateway-icon icon-ag-info"></i>
          </span>
        </div>
      </div>
      <div class="card">
        <div class="value">{{summaryData.perc95_resp_time.value_str || '--'}}ms</div>
        <div class="key">
          {{ t('统计响应时间') }}
          <span v-bk-tooltips="t('根据百分位计算出的响应时间，相比平均响应时间，更能反映问题')" v-if="summaryData.rate_availability.value < 1">
            <i class="apigateway-icon icon-ag-help"></i>
          </span>
        </div>
      </div>
    </div>

    <div class="runtime-container">
      <bk-tab v-model:active="active" type="unborder-card" @tab-change="handleTabChange">
        <bk-tab-panel name="req_component_name" :label="t('按组件')">
          <bk-table
            :data="requests"
            :border="false"
            :outer-border="false"
            :header-border="true"
            v-bkloading="{ isLoading: isDataLoading, opacity: 1, delay: 1000 }"
            :size="'small'">
            <!-- <div slot="empty">
              <table-empty empty />
            </div> -->
            <bk-table-column type="index" :label="t('序列')" width="60"></bk-table-column>
            <bk-table-column :label="t('组件名')" prop="req_component_name"></bk-table-column>
            <bk-table-column :label="t('错误 / 总次数')" prop="req_component_name" sortable :sort-method="handleSortCount">
              <template #default="props">
                <span v-if="props.row.requests.error_count">
                  {{props.row.requests.error_count}} /
                </span>
                <span>{{props.row.requests.count}}</span>
                <bk-button
                  v-if="props.row.requests.error_count"
                  :text="true"
                  @click="handleShowDetail(props.row)"
                  class="ml5">
                  {{ t('详情') }}
                </bk-button>
              </template>
            </bk-table-column>
            <bk-table-column
              :label="t('统计响应时间(ms)')"
              prop="req_component_name"
              sortable
              :sort-method="handleSortRespTime">
              <template #default="props">
                {{props.row.perc95_resp_time.value}}
              </template>
            </bk-table-column>
            <bk-table-column
              :label="t('平均响应时间(ms)')"
              prop="req_component_name"
              sortable
              :sort-method="handleSortAvgTime">
              <template #default="props">
                {{props.row.avg_resp_time.value}}
              </template>
            </bk-table-column>
            <bk-table-column :label="t('可用率')" prop="req_component_name" sortable :sort-method="handleSortRate">
              <template #default="props">
                {{props.row.rate_availability.value_str}}%
              </template>
            </bk-table-column>
          </bk-table>
        </bk-tab-panel>

        <bk-tab-panel name="req_app_code" :label="t('按APP')">
          <bk-table
            :data="requests"
            :border="false"
            :outer-border="false"
            :header-border="true"
            v-bkloading="{ isLoading: isDataLoading, opacity: 1, delay: 1000 }"
            :size="'small'">
            <!-- <div slot="empty">
              <table-empty empty />
            </div> -->
            <bk-table-column type="index" :label="t('序列')" width="60"></bk-table-column>
            <bk-table-column label="app_code" prop="req_app_code"></bk-table-column>
            <bk-table-column :label="t('错误 / 总次数')" prop="req_component_name" sortable :sort-method="handleSortCount">
              <template #default="props">
                <span v-if="props.row.requests.error_count">
                  {{props.row.requests.error_count}} /
                </span>
                <span>{{props.row.requests.count}}</span>
                <bk-button
                  v-if="props.row.requests.error_count"
                  :text="true"
                  @click="handleShowDetail(props.row)"
                  class="ml5">
                  {{ t('详情') }}
                </bk-button>
              </template>
            </bk-table-column>
            <bk-table-column
              :label="t('统计响应时间(ms)')"
              prop="req_component_name"
              sortable
              :sort-method="handleSortRespTime">
              <template #default="props">
                {{props.row.perc95_resp_time.value}}
              </template>
            </bk-table-column>
            <bk-table-column
              :label="t('平均响应时间(ms)')"
              prop="req_component_name"
              sortable
              :sort-method="handleSortAvgTime">
              <template #default="props">
                {{props.row.avg_resp_time.value}}
              </template>
            </bk-table-column>
            <bk-table-column :label="t('可用率')" prop="req_component_name" sortable :sort-method="handleSortRate">
              <template #default="props">
                {{props.row.rate_availability.value_str}}%
              </template>
            </bk-table-column>
          </bk-table>
        </bk-tab-panel>

        <bk-tab-panel name="req_url" :label="t('按URL')">
          <bk-table
            :data="requests"
            :border="false"
            :outer-border="false"
            :header-border="true"
            v-bkloading="{ isLoading: isDataLoading, opacity: 1, delay: 1000 }"
            :size="'small'">
            <!-- <div slot="empty">
              <table-empty empty />
            </div> -->
            <bk-table-column type="index" :label="t('序列')" width="60"></bk-table-column>
            <bk-table-column label="URL" prop="req_url" :min-width="200"></bk-table-column>
            <bk-table-column :label="t('错误 / 总次数')" prop="req_component_name" sortable :sort-method="handleSortCount">
              <template #default="props">
                <span v-if="props.row.requests.error_count">
                  {{props.row.requests.error_count}} /
                </span>
                <span>{{props.row.requests.count}}</span>
                <bk-button
                  v-if="props.row.requests.error_count"
                  :text="true"
                  @click="handleShowDetail(props.row)"
                  class="ml5">
                  {{ t('详情') }}
                </bk-button>
              </template>
            </bk-table-column>
            <bk-table-column
              :label="t('统计响应时间(ms)')"
              prop="req_component_name"
              :sortable="true"
              :sort-method="handleSortRespTime">
              <template #default="props">
                {{props.row.perc95_resp_time.value}}
              </template>
            </bk-table-column>
            <bk-table-column
              :label="t('平均响应时间(ms)')"
              prop="req_component_name"
              :sortable="true"
              :sort-method="handleSortAvgTime">
              <template #default="props">
                {{props.row.avg_resp_time.value}}
              </template>
            </bk-table-column>
            <bk-table-column
              :label="t('可用率')"
              prop="req_component_name"
              :sortable="true"
              :sort-method="handleSortRate">
              <template #default="props">
                {{props.row.rate_availability.value_str}}%
              </template>
            </bk-table-column>
          </bk-table>
        </bk-tab-panel>
      </bk-tab>
    </div>

    <bk-dialog
      v-model="detailDialog.visiable"
      theme="primary"
      :width="900"
      :mask-close="true"
      :header-position="'left'"
      :title="t('错误请求详情')"
      :show-footer="false">
      <div v-bkloading="{ isLoading: isErrorDataLoading, opacity: 1, delay: 1000 }">
        <div class="mb10">
          <strong>{{detailDialog.name}}</strong>
        </div>
        <bk-alert class="mb10" type="info" :title="t('此处最多展示最近 200 条错误信息')"></bk-alert>
        <bk-table
          :data="errorRequests"
          :header-border="true"
          :max-height="400"
          :size="'small'">
          <!-- <div slot="empty">
            <table-empty empty />
          </div> -->
          <bk-table-column :label="t('时间')" prop="datetime" width="120"></bk-table-column>
          <bk-table-column :label="t('错误信息')" prop="message"></bk-table-column>
          <bk-table-column :label="t('耗时')" prop="time" width="120"></bk-table-column>
          <bk-table-column :label="t('响应状态')" prop="status" width="80"></bk-table-column>
        </bk-table>
      </div>
    </bk-dialog>
  </div>
</template>

<script lang="ts" setup>
import { ref, reactive, computed, watch } from 'vue';
import { useRoute } from 'vue-router';
import ChartView from './chart.vue';
import moment from 'moment';
import { useI18n } from 'vue-i18n';
import { getApigwErrorRequest, getApigwRuntimeRequest, getApigwSystemSummary } from '@/http';

const route = useRoute();

const { t } = useI18n();

const systemName = ref<string | string[]>();
const system = ref<string | string[]>();
const timer = ref<number>(0);
const autoEnable = ref<boolean>(true);
const detailDialog = reactive<any>({
  name: '',
  visiable: false,
});
const active = ref<string>('req_component_name');
const requests = ref<any>([]);
const endTime = ref(Date.now());
const startTime = ref(Date.now() - 60 * 60 * 1000);
const dayStartTime = ref(Date.now() - 24 * 60 * 60 * 1000);
const isDataLoading = ref<boolean>(true);
const isSummaryDataLoading = ref<boolean>(true);
const summaryData = ref<any>({
  avg_resp_time: {
    value: '',
  },
  perc95_resp_time: {
    value_str: '',
  },
  rate_availability: {
    value_str: '',
  },
  requests: {
    count_str: '',
  },
});
const isErrorDataLoading = ref<boolean>(false);
const errorRequests = ref<any>([]);

const principalFlag = computed(() => {
  if (summaryData.value.basic_info?.maintainers.length) {
    return true;
  }
  return false;
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
      type: active,
      system: system.value,
      start: startTime,
      end: endTime,
    });
    requests.value = res.data;
  } catch (e) {
    console.log(e);
  } finally {
    isDataLoading.value = false;
  }
};

const handleSortCount = (a: any, b: any) => {
  if (a.requests.count < b.requests.count) {
    return -1;
  }
  if (a.requests.count > b.requests.count) {
    return 1;
  }
  return 0;
};

const handleSortRespTime = (a: any, b: any) => {
  if (a.perc95_resp_time.value < b.perc95_resp_time.value) {
    return -1;
  }
  if (a.perc95_resp_time.value > b.perc95_resp_time.value) {
    return 1;
  }
  return 0;
};

const handleSortAvgTime = (a: any, b: any) => {
  if (a.avg_resp_time.value < b.avg_resp_time.value) {
    return -1;
  }
  if (a.avg_resp_time.value > b.avg_resp_time.value) {
    return 1;
  }
  return 0;
};

const handleSortRate = (a: any, b: any) => {
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
      start: startTime,
      end: endTime,
    });
    summaryData.value = res.data;
  } catch (e) {
    console.log(e);
  } finally {
    isSummaryDataLoading.value = false;
  }
};

const handlTimeChnage = (start: number, end: number) => {
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

const handleShowDetail = async (data: any) => {
  isErrorDataLoading.value = true;
  errorRequests.value = [];
  detailDialog.visiable = true;
  detailDialog.name = data.req_app_code || data.req_component_name || data.req_url || '--';

  try {
    const res = await getApigwErrorRequest({
      system: system.value,
      appCode: data.req_app_code || '',
      componentName: data.req_component_name || '',
      requestUrl: data.req_url || '',
      start: startTime,
      end: endTime,
    });
    errorRequests.value = res.data.data.data_list.map((item: any) => {
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
  } catch (e) {
    console.log(e);
  } finally {
    isErrorDataLoading.value = false;
  }
};

system.value = route.params?.system;
systemName.value = route.query?.systemName;
route.meta.title = `${t('系统实时概况')}`;
init();

watch(
  () => autoEnable.value,
  () => {
    enableAutoRefresh();
  },
);

watch(
  () => detailDialog.visiable,
  (value) => {
    if (value) {
      clearAutoRefresh();
    } else {
      enableAutoRefresh();
    }
  },
);
</script>

<style lang="scss" scoped>
.chart-box {
  width: 100%;
  background: #FFF;
  border: 1px solid #dcdee5;
  border-radius: 2px;
  margin-bottom: 20px;
  padding: 10px;
}
.runtime-container {
  background: #FFF;
  border: 1px solid #dcdee5;
  border-radius: 2px;
}
.card-box {
  background: #FFF;
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
</style>
