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
  <div class="page-wrapper-padding runtime-data-wrapper">
    <div class="top-header flex items-center m-b-16px">
      <strong
        class="text-[16px]"
        style=" font-weight: normal;color: #63656e"
      >
        {{ t("所有运营系统实时概况") }}
      </strong>
      <BkSelect
        v-model="timeRange"
        :clearable="false"
        :scroll-height="300"
        style=" right: 15px;width: 200px"
        @change="handleTimeChange"
      >
        <BkOption
          v-for="option in timeList"
          :id="option.id"
          :key="option.id"
          :name="option.name"
        />
      </BkSelect>
      <div class="flex m-r-16px">
        <div class="auto-refresh">
          <BkSwitcher
            v-model="autoEnable"
            class="m-r-10px"
            theme="primary"
          />
          <span class="vm text-[13px]">
            {{ t("每分钟自动刷新") }}
          </span>
        </div>
      </div>
    </div>
    <BkLoading :loading="isDataLoading">
      <div
        class="flex m-t-20px runtime-container"
        :style="{ height: containerHeight, position: 'relative' }"
      >
        <div class="chart-box">
          <template v-if="charts.length">
            <div
              v-for="(chart, index) of charts"
              :key="index"
              class="chart-card"
              @click="handleGoDetail(chart)"
            >
              <div class="card-content">
                <div class="header">
                  <p>
                    {{ chart.basic_info.description }}
                    <span
                      class="text-[12px]"
                      style="color: #979ba5"
                    >
                      ({{ chart.basic_info.name }})
                    </span>
                  </p>
                </div>
                <div class="wrapper">
                  <div class="detail-wrapper">
                    <div class="per_response_time">
                      <strong>
                        {{ chart.perc95_resp_time ? chart.perc95_resp_time.value : "0" }}
                      </strong>
                      ms
                    </div>
                    <div class="response_count">
                      {{ chart.requests ? chart.requests.count : "0" }} 次
                    </div>
                  </div>
                  <div class="ring-wrapper">
                    <AgRing
                      v-bk-tooltips="{
                        content: t('可用率低于100%'),
                        disabled: chart.rate_availability.value > 0
                      }"
                      :percent="chart.rate_availability.value_str"
                      :size="80"
                      :stroke-width="8"
                      :fill-width="8"
                      :fill-color="initRingColor(chart)"
                      :text-style="initRingTextStyle(chart)"
                    />
                  </div>
                </div>
              </div>
            </div>
          </template>
          <TableEmpty
            v-else
            :is-loading="isDataLoading"
            :empty-type="tableEmptyConfig.emptyType"
            :abnormal="tableEmptyConfig.isAbnormal"
            :style="exceptionStyle"
            @refresh="initData"
            @clear-filter="handleClearFilterKey"
          />
        </div>

        <div
          v-if="statusList.length"
          class="timeline-box"
        >
          <BkTimeline :list="statusList" />
        </div>
      </div>
    </BkLoading>
  </div>
</template>

<script lang="ts" setup>
import moment from 'moment';
import { getApigwRuntime, getApigwTimeline } from '@/services/source/runTime';
import type { ReturnRecordType } from '@/types/common';
import AgRing from '@/components/ag-ring/Index.vue';
import TableEmpty from '@/components/table-empty/Index.vue';

const { t } = useI18n();
const router = useRouter();

const timeList = shallowRef([
  {
    id: '1m',
    name: t('最近 1 分钟'),
  },
  {
    id: '10m',
    name: t('最近 10 分钟'),
  },
  {
    id: '30m',
    name: t('最近 30 分钟'),
  },
  {
    id: '1h',
    name: t('最近 1 小时'),
  },
  {
    id: '6h',
    name: t('最近 6 小时'),
  },
  {
    id: '12h',
    name: t('最近 12 小时'),
  },
  {
    id: '24h',
    name: t('最近 24 小时'),
  },
]);
const isDataLoading = ref(false);
const timer = ref(null);
const autoEnable = ref(true);
const timeRange = ref('1m');
const containerHeight = ref('100%');
const charts = ref([]);
const timeLines = ref([]);
const statusList = ref([]);
const tableEmptyConfig = ref({
  emptyType: '',
  isAbnormal: false,
});

const exceptionStyle = computed(() => {
  return {
    border: '1px solid #eee',
    borderRadius: '2px',
    background: '#ffffff',
    marginRight: '16px',
  };
});

const init = () => {
  initData();
  enableAutoRefresh();
};

const initData = () => {
  isDataLoading.value = true;
  Promise.all([getRuntime(), getTimeline()]).then(() => {
    isDataLoading.value = false;
  });
};

const initRingColor = (chart: Record<string, any>) => {
  if (chart.rate_availability.value < 0.97) {
    return '#ff5656';
  }
  if (chart.rate_availability.value < 1) {
    return '#ffb848';
  }
  return '#94f5a4';
};

const initRingTextStyle = (chart: Record<string, any>) => {
  if (chart.rate_availability.value < 0.97) {
    return {
      fontSize: '12px',
      color: '#ea3636',
    };
  }
  if (chart.rate_availability.value < 1) {
    return {
      fontSize: '12px',
      color: '#ff9c01',
    };
  }
  return {
    fontSize: '12px',
    color: '#2dcb56',
  };
};

const handleGoDetail = (chart: any) => {
  router.push({
    name: 'componentsRuntimeDetail',
    params: { system: chart.system_name },
    query: { systemName: chart.basic_info.description },
  });
};

const getRuntime = async () => {
  try {
    const res = await getApigwRuntime({ timeRange: timeRange.value });
    charts.value = res || [];
    tableEmptyConfig.value.isAbnormal = false;
  }
  catch {
    tableEmptyConfig.value = Object.assign({}, {
      emptyType: 'empty',
      isAbnormal: true,
    });
  }
};

const getTimeline = async () => {
  try {
    const res = await getApigwTimeline();
    timeLines.value = res || [];
    initTimeline();
  }
  catch (e) {
    console.error(e);
  }
};

const initTimeline = () => {
  timeLines.value.forEach((item) => {
    const time = moment(item.data.mts).fromNow();
    const data = {
      tag: `${item.system_name} ${time}`,
      content: '',
      filled: false,
      type: '',
    };
    const { rate_availability, requests } = item.data;
    const typeMap: ReturnRecordType<string, string> = {
      errors_occurred: () => {
        data.type = 'warning';
        data.content = t(`偶发 ${requests.error_count || 0} 次请求错误`, { errorCount: requests.error_count });
      },
      availability_restored: () => {
        data.type = 'success';
        const start = moment(item.mts);
        const end = moment(item.mts_end);
        const timeSpan = end.from(start, true);
        data.content = t(
          `<div>可用率恢复至 ${rate_availability.value_str}%, 低可用持续时间: <strong> ${timeSpan}</strong></div>`,
          {
            value_str: rate_availability.value_str,
            time: timeSpan,
          },
        );
      },
      availability_dropped: () => {
        data.type = 'danger';
        data.content = t(
          `<div>可用率下降至 <strong>${rate_availability.value_str}%</strong>, 调用错误数/总次数: <strong> ${requests.error_count || 0}/${requests.count || 0}</strong></div>`,
          {
            value_str: rate_availability.value_str,
            error_count: requests.error_count,
            count: requests.count,
          },
        );
      },
    };
    typeMap[item.type]();
    statusList.value.push(data);
  });
};

const handleTimeChange = (value: string) => {
  timeRange.value = value;
  tableEmptyConfig.value.emptyType = 'searchEmpty';
  initData();
};

const enableAutoRefresh = () => {
  clearInterval(timer.value);
  if (!autoEnable.value) {
    return false;
  }
  timer.value = setInterval(() => {
    initData();
  }, 1000 * 60);
};

const clearAutoRefresh = () => {
  clearInterval(timer.value);
};

const handleClearFilterKey = () => {
  timeRange.value = '1m';
  tableEmptyConfig.value.emptyType = Object.assign({}, {
    empType: '',
    isAbnormal: false,
  });
};

watch(
  () => autoEnable.value,
  () => {
    enableAutoRefresh();
  },
);

onMounted(() => {
  const winHeight = window.innerHeight - 250;
  containerHeight.value = `${winHeight}px`;
  init();
});

onUnmounted(() => {
  clearAutoRefresh();
});
</script>

<style lang="scss" scoped>
.runtime-data-wrapper {

  .top-header {
    height: 32px;
    line-height: 32px;
    color: #63656e;

    strong {
      flex: 1;
      font-size: 14px;
    }

    .auto-refresh {
      margin-left: 40px;
      text-align: left;
    }
  }

  .runtime-container {
    display: flex;
    min-height: 300px;

    .chart-box {
      width: 100%;

      .chart-card {
        width: 20%;
        height: 155px;
        max-width: 20%;
        min-width: 20%;
        flex: 1;

        .card-content {
          display: inline-block;
          display: block;
          margin: 0 15px 15px 0;
          cursor: pointer;
          background: #fff;
          border-radius: 2px;
          box-shadow: 0 1px 2px 0 rgb(0 0 0 / 16%);
        }

        .header {
          padding: 15px 20px 10px;
          font-size: 14px;
          line-height: 18px;
          color: #313238;
          border-bottom: 1px solid #eee;

          p {
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
          }
        }

        .per_response_time {
          margin: 15px 0 5px;
          font-size: 16px;
          line-height: 32px;
          color: #63656e;
          text-align: left;

          strong {
            font-size: 24px;
            font-weight: bold;
            color: #63656e;
          }
        }

        .response_count {
          font-size: 12px;
          line-height: 1;
          color: #63656e;
        }
      }

      .wrapper {
        display: flex;
        padding: 5px 20px;

        .ring-wrapper {
          width: 80px;
        }

        .detail-wrapper {
          flex: 1;
        }
      }
    }

    .timeline-box {
      width: 300px;
      height: 100%;
      padding: 0 20px;
      overflow: auto;

      &::-webkit-scrollbar {
        width: 5px;
      }

      &::-webkit-scrollbar-thumb {
        height: 5px;
        background-color: #ccc;
        border-radius: 2px;
      }
    }

    :deep(.BkException) {
      display: flex;
      height: 280px;
      align-items: center;
      justify-content: center;
    }

    :deep(.BkException-img) {
      height: 130px;
    }
  }
}

@media screen and (max-width: 1920px) {

  .runtime-container .chart-box .chart-card {
    width: 25%;
    max-width: 25%;
    min-width: 25%;
  }

  .timeline-box {
    width: 300px !important;
  }
}

@media screen and (max-width: 1680px) {

  .runtime-container .chart-box .chart-card {
    width: 33.3%;
    max-width: 33.3%;
    min-width: 33.3%;
  }

  .timeline-box {
    width: 250px !important;
  }
}
</style>
