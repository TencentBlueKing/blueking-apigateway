<template>
  <div class="page-wrapper-padding runtime-data-wrapper">
    <div class="top-header mb15">
      <strong class="f16" style="color: #63656e; font-weight: normal">
        {{ t("所有运营系统实时概况") }}
      </strong>
      <bk-select
        v-model="timeRange" :clearable="false" :scroll-height="300" style="width: 200px; right: 15px"
        @change="handleTimeChange">
        <bk-option v-for="option in timeList" :key="option.id" :id="option.id" :name="option.name">
        </bk-option>
      </bk-select>
      <div class="filter">
        <div class="auto-refresh">
          <bk-switcher class="mr10" v-model="autoEnable" theme="primary" />
          <span class="vm f13">
            {{t("每分钟自动刷新") }}
          </span>
        </div>
      </div>
    </div>
    <div
      class="runtime-container mt20" :style="{ height: containerHeight, position: 'relative' }"
      v-bkloading="{ isLoading: isDataLoading, opacity: 1 }">
      <div class="chart-box" style="position: relative">
        <template v-if="charts.length">
          <div class="chart-card" v-for="(chart, index) of charts" :key="index" @click="handleGoDetail(chart)">
            <div class="card-content">
              <div class="header">
                <p>
                  {{ chart.basic_info.description }}
                  <span class="f12" style="color: #979ba5">
                    ({{ chart.basic_info.name }})
                  </span>
                </p>
              </div>
              <div class="wrapper">
                <div class="detail-wrapper">
                  <div class="per_response_time">
                    <strong>{{
                      chart.perc95_resp_time ? chart.perc95_resp_time.value : "0"
                    }}</strong>
                    ms
                  </div>
                  <div class="response_count">
                    {{ chart.requests ? chart.requests.count : "0" }} 次
                  </div>
                </div>
                <div class="ring-wrapper">
                  <Ring
                    v-if="chart.rate_availability.value < 1" v-bk-tooltips="t('可用率低于100%')"
                    :percent="chart.rate_availability.value_str" :size="80" :stroke-width="8" :fill-width="8"
                    :fill-color="initRingColor(chart)" :text-style="initRingTextStyle(chart)">
                  </Ring>
                  <Ring
                    v-else :percent="chart.rate_availability.value_str" :size="80" :stroke-width="8" :fill-width="8"
                    :fill-color="initRingColor(chart)" :text-style="initRingTextStyle(chart)">
                  </Ring>
                </div>
              </div>
            </div>
          </div>
        </template>
        <bk-exception
          v-else type="empty" scene="part" style="
            border: 1px solid #eee;
            border-raidus: 2px;
            background: #fff;
            margin-right: 15px;
          ">
          <span>{{ t("暂无数据") }}</span>
        </bk-exception>
      </div>

      <div class="timeline-box" v-if="statusList.length">
        <bk-timeline :list="statusList" />
      </div>
    </div>
  </div>
</template>

<script lang="ts" setup>
import { ref, shallowRef, watch, onMounted, onUnmounted } from 'vue';
import Ring from '@/components/ring/index.vue';
import moment from 'moment';
import i18n from '@/language/i18n';
import { useCommon } from '@/store';
import { useRouter } from 'vue-router';
import { getApigwRuntime, getApigwTimeline } from '@/http';

const { t } = i18n.global;
const router = useRouter();
const commonStore = useCommon();

const isDataLoading = ref(false);
const timeList = shallowRef([
  { id: '1m', name: t('最近 1 分钟') },
  { id: '10m', name: t('最近 10 分钟') },
  { id: '30m', name: t('最近 30 分钟') },
  { id: '1h', name: t('最近 1 小时') },
  { id: '6h', name: t('最近 6 小时') },
  { id: '12h', name: t('最近 12 小时') },
  { id: '24h', name: t('最近 24 小时') },
]);
console.log(commonStore.apigwId);
const apigwId = ref(commonStore.apigwId);
const timer = ref(null);
const autoEnable = ref(true);
const timeRange = ref('1m');
const containerHeight = ref('100%');
const charts = ref([]);
const timeLines = ref([]);
const statusList = ref([]);

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
    name: 'runtimeDetail',
    params: {
      system: chart.system_name,
    },
    query: {
      systemName: chart.basic_info.description,
    },
  });
};

const getRuntime = async () => {
  try {
    const res = await getApigwRuntime({
      timeRange: timeRange.value,
    });
    charts.value = res || [];
  } catch (e) {
    console.log(e);
  }
};

const getTimeline = async () => {
  try {
    console.log(apigwId.value);
    const res = await getApigwTimeline();
    timeLines.value = res || [];
    initTimeline();
  } catch (e) {
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
    const typeMap: Record<string, Function> = {
      errors_occurred: () => {
        data.type = 'warning';
        data.content = t(`偶发 ${requests.error_count || 0} 次请求错误`, {
          errorCount: requests.error_count,
        });
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
    display: flex;
    height: 32px;
    line-height: 32px;
    color: #63656e;
    align-items: center;

    strong {
      flex: 1;
      font-size: 14px;
    }

    .filter {
      display: flex;
      margin-right: 15px;
    }

    .auto-refresh {
      margin-left: 40px;
      text-align: left;
    }
  }

  .runtime-container {
    min-height: 300px;
    display: flex;

    .chart-box {
      flex: 1;
      display: flex;
      flex-wrap: wrap;
      align-content: flex-start;

      .chart-card {
        flex: 1;
        width: 20%;
        min-width: 20%;
        max-width: 20%;
        height: 155px;

        .card-content {
          background: #fff;
          border-radius: 2px;
          margin: 0 15px 15px 0;
          box-shadow: 0px 1px 2px 0px rgba(0, 0, 0, 0.16);
          display: inline-block;
          cursor: pointer;
          display: block;
        }

        .header {
          font-size: 14px;
          color: #313238;
          line-height: 18px;
          padding: 15px 20px 10px 20px;
          border-bottom: 1px solid #eee;

          p {
            white-space: nowrap;
            text-overflow: ellipsis;
            overflow: hidden;
          }
        }

        .per_response_time {
          font-size: 16px;
          text-align: left;
          color: #63656e;
          line-height: 32px;
          margin: 15px 0 5px 0;

          strong {
            font-size: 24px;
            font-weight: bold;
            color: #63656e;
          }
        }

        .response_count {
          font-size: 12px;
          color: #63656e;
          line-height: 1;
        }
      }

      .wrapper {
        display: flex;
        padding: 5px 20px 5px 20px;

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
      overflow: auto;
      padding: 0 20px;

      &::-webkit-scrollbar {
        width: 5px;
      }

      &::-webkit-scrollbar-thumb {
        height: 5px;
        border-radius: 2px;
        background-color: #ccc;
      }
    }

    :deep(.bk-exception) {
      height: 280px;
      display: flex;
      align-items: center;
      justify-content: center;
    }

    :deep(.bk-exception-img) {
      height: 130px;
    }
  }
}

@media screen and (max-width: 1920px) {
  .runtime-container .chart-box .chart-card {
    width: 25%;
    min-width: 25%;
    max-width: 25%;
  }

  .timeline-box {
    width: 300px !important;
  }
}

@media screen and (max-width: 1680px) {
  .runtime-container .chart-box .chart-card {
    width: 33.3%;
    min-width: 33.3%;
    max-width: 33.3%;
  }

  .timeline-box {
    width: 250px !important;
  }
}
</style>
