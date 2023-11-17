<template>
  <div class="access-log-wrapper">
    <div class="ag-top-header">
      <bk-form class="search-form" form-type="vertical">
        <bk-form-item :label="t('选择时间')" class="ag-form-item-datepicker">
          <bk-date-picker
            ref="datePickerRef"
            type="datetimerange"
            style="width: 320px;"
            v-model="dateTimeRange"
            :placeholder="t('选择日期时间范围')"
            :shortcuts="AccessLogStore.datepickerShortcuts"
            :shortcut-close="true"
            :use-shortcut-text="true"
            :clearable="false"
            :shortcut-selected-index="shortcutSelectedIndex"
            @shortcut-change="handleShortcutChange"
            @pick-success="handleTimeChange"
          />
        </bk-form-item>
        <bk-form-item :label="t('环境')">
          <bk-select
            style="width: 150px;" v-model="searchParams.stage_id" :clearable="false" searchable
            @selected="handleStageSelected">
            <bk-option v-for="option in stageList" :key="option.id" :id="option.id" :name="option.name">
            </bk-option>
          </bk-select>
        </bk-form-item>
        <bk-form-item :label="t('查询条件')" class="ag-form-item-inline">
          <SearchInput
            v-model="keyword"
            @search="handleSearch"
            :class="['top-search-input', localLanguage === 'en' ? 'top-search-input-en' : '']" />
          <span v-bk-tooltips="searchUsage.config" class="search-usage">
            {{ `${searchUsage.showed ? t('隐藏示例') : t('显示示例')}` }}
          </span>
        </bk-form-item>
      </bk-form>
    </div>
    <div v-bkloading="{ isLoading: !isPageLoading && isDataLoading }">
      <div class="chart">
        <div class="chart-container">
          <div class="chart-title"> {{ t('请求数') }}</div>
          <div v-show="isShowChart" ref="chartContainer" class="chart-el"></div>
          <div v-show="!isShowChart && !isPageLoading" class="no-data-chart">
            <slot name="empty">
              <TableEmpty
                :keyword="tableEmptyConf.keyword"
                :abnormal="tableEmptyConf.isAbnormal"
                @reacquire="getSearchData"
                @clear-filter="clearFilterKey"
              />
            </slot>
          </div>
        </div>
      </div>
      <div class="list">
        <bk-table
          ref="tableRef"
          :data="table.list"
          :size="'small'"
          :pagination="pagination"
          :row-style="{ cursor: 'pointer' }"
          :row-class-name="getRowClassName"
          @row-click="handleRowClick"
          @page-change="handlePageChange"
          @page-limit-change="handlePageLimitChange">
          <template #empty>
            <TableEmpty
              :keyword="tableEmptyConf.keyword"
              :abnormal="tableEmptyConf.isAbnormal"
              @reacquire="getSearchData"
              @clear-filter="clearFilterKey"
            />
          </template>
          <bk-table-column type="expand" width="30" align="center">
            <template #default="{ row }">
              <dl class="details">
                <div class="item" v-for="({ label, field, is_filter: showCopy }, index) in table.fields" :key="index">
                  <dt class="label">
                    {{ label }}
                    <i
                      v-bk-tooltips="t('复制字段名')" v-if="showCopy" class="apigateway-icon icon-ag-clipboard copy-btn"
                      @click="copy(field)">
                    </i>
                  </dt>
                  <!-- <dd class="value">{{ row[field] | formatValue(null, field) }}</dd> -->
                </div>
                <bk-button class="share-btn" theme="primary" outline @click="copy(row)" :loading="isShareLoading">
                  {{ t('复制分享链接') }}
                </bk-button>
              </dl>
            </template>
          </bk-table-column>
          <template v-if="table.headers.length">
            <bk-table-column
              v-for="({ field, label, width, formatter }, index) in table.headers"
              :show-overflow-tooltip="true"
              :key="index"
              :width="width"
              :formatter="formatter"
              :label="label"
              :class-name="field"
              :prop="field"
            />
          </template>
          <template v-else>
            <bk-table-column label="" />
          </template>
        </bk-table>
      </div>
    </div>

    <div id="access-log-search-usage-content">
      <div class="sample">
        <p>
          <span class="mode">{{ t('匹配包含某个关键字') }}: </span>
          <span class="value" @click="handleClickUsageValue">request_id: b3e2497532e54f518b3d1267fb67c83a</span>
        </p>
        <p>
          <span class="mode">{{ t('多个关键字匹配') }}: </span>
          <span class="value" @click="handleClickUsageValue">(app_code: "app-template" AND client_ip: "1.0.0.1") OR
            resource_name: get_user</span>
        </p>
        <p>
          <span class="mode">{{ t('不包含关键字') }}: </span>
          <span class="value" @click="handleClickUsageValue">-status: 200</span>
        </p>
        <p>
          <span class="mode">{{ t('范围匹配') }}: </span>
          <span class="value" @click="handleClickUsageValue">duration: [5000 TO 30000]</span>
        </p>
      </div>
      <div class="more">
        {{ t('更多示例请参阅') }} <a class="link" target="_blank" :href="GLOBAL_CONFIG.DOC.QUERY_USE"> {{ t('“请求流水查询规则”') }}
        </a>
      </div>
    </div>
  </div>
</template>

<script lang="ts" setup>
import dayjs from 'dayjs';
import i18n from '@/language/i18n';
import SearchInput from './components/search-input.vue';
import TableEmpty from '@/components/table-empty.vue';
import echarts from 'echarts';
import 'echarts/lib/chart/bar';
import 'echarts/lib/component/tooltip';
import { ref, nextTick, watch, onMounted, computed } from 'vue';
import { merge } from 'lodash';
// import { bus } from '@/common/bus';
import { copy } from '@/common/util';
import { SearchParamsInterface } from './common/type';
import { useRoute } from 'vue-router';
import { useAccessLog } from '@/store';
import { useGetGlobalProperties, userChartIntervalOption } from '@/hooks';
import {
  fetchApigwAccessLogList,
  fetchApigwAccessLogChart,
  fetchApigwStages,
} from '@/http';
// import { catchErrorHandler } from '@/common/util';
// import chartMixin from '@/mixins/chart';

const {
  getChartIntervalOption,
} = userChartIntervalOption();

const { t } = i18n.global;
const route = useRoute();
const AccessLogStore = useAccessLog();
const globalProperties = useGetGlobalProperties();
const { GLOBAL_CONFIG } = globalProperties;
console.log(AccessLogStore, 555);

const chartInstance = ref(null);
const chartContainer = ref(null);
const tableRef = ref(null);
const datePickerRef = ref(null);
const keyword = ref('');
const isPageLoading = ref(false);
const isDataLoading = ref(false);
const isShareLoading = ref(false);
const shortcutSelectedIndex = ref(1);
const dateTimeRange = ref([]);
const apigwId = ref(Number(route.params.id));
const pagination = ref({
  current: 1,
  count: 0,
  limit: 10,
});
const searchParams = ref<SearchParamsInterface>({
  stage_id: 0,
  time_start: '',
  time_end: '',
  query: '',
});
const tableEmptyConf = ref({
  keyword: '',
  isAbnormal: false,
});
const table = ref({
  list: [],
  fields: [],
  headers: [],
});
const searchUsage = ref({
  showed: false,
  config: {
    allowHtml: true,
    trigger: 'click',
    theme: 'light',
    content: '#access-log-search-usage-content',
    onShow: () => {
      searchUsage.value.showed = true;
      console.log(document.getElementById('#access-log-search-usage-content'));
    },
    onHide: () => {
      searchUsage.value.showed = false;
    },
  },
});
const chartData: any = ref({});
const stageList = ref([]);

const isShowChart = computed(() => {
  console.log(chartData.value, 555);
  return chartData.value?.series?.length;
});

const formatterValue = (params: any) => {
  return t('{value} 次', { value: params.value.toLocaleString() });
};

const localLanguage = computed(() => {
  return 'zh-cn';
});

const formatValue = (value?: any, field?: string) => {
  if (value && field === 'timestamp') {
    return dayjs.unix(value).format('YYYY-MM-DD HH:mm:ss ZZ');
  }
  return value || '--';
};

const formatDatetime = (timeRange: number[]) => {
  return [
    (+new Date(`${timeRange[0]}`)) / 1000,
    (+new Date(`${timeRange[1]}`)) / 1000,
  ];
};

const setSearchTimeRange = () => {
  let timeRange = dateTimeRange.value;

  // 选择的是时间快捷项，需要实时计算时间值
  if (shortcutSelectedIndex.value !== -1) {
    timeRange = AccessLogStore.datepickerShortcuts[shortcutSelectedIndex.value].value();
  }
  const formatTimeRange = formatDatetime(timeRange);
  searchParams.value = Object.assign(searchParams.value, {
    time_start: formatTimeRange[0],
    time_end: formatTimeRange[1],
  });
};

const renderChart = (data: any) => {
  const { timeline } = data;
  const xAxisData = timeline.map((time: number) => dayjs.unix(time).format('MM-DD\nHH:mm:ss'));
  const options = {
    grid: {
      left: 20,
      right: 20,
      top: 16,
      bottom: 16,
      containLabel: true,
    },
    xAxis: {
      type: 'category',
      data: xAxisData,
      axisLabel: {
        color: '#A0A4AA',
      },
      axisLine: {
        lineStyle: {
          color: '#e9edf0',
        },
      },
      axisTick: {
        alignWithLabel: true,
        lineStyle: {
          color: '#BDC8D3',
        },
      },
    },
    yAxis: {
      type: 'value',
      axisLabel: {
        color: '#A0A4AA',
      },
      splitLine: {
        lineStyle: {
          color: '#e9edf0',
        },
      },
      axisLine: {
        show: false,
      },
      axisTick: {
        show: false,
      },
    },
    series: [{
      type: 'bar',
      data: data.series,
      barMaxWidth: 60,
      itemStyle: {
        color: '#5B8FF9',
      },
    }],
    tooltip: {
      trigger: 'item',
      backgroundColor: 'rgba(0, 0, 0, 0.7)',
      textStyle: {
        fontSize: 12,
      },
      formatter(params: any) {
        return `${formatterValue(params)}<br />${params.name}`;
      },
    },
  };
  const timeDuration = timeline[timeline.length - 1] - timeline[0];
  const intervalOption = getChartIntervalOption(timeDuration, 'time', 'xAxis');
  chartInstance.value.setOption(merge(options, intervalOption));
  console.log(intervalOption, 1111);
  chartResize();
};

const setTableHeader = () => {
  const columns = [
    {
      field: 'timestamp',
      width: 220,
      label: t('请求时间'),
      formatter: (row: any, column: any, cellValue: string) => {
        return formatValue(cellValue, column.property);
      },
    },
    { field: 'method', width: 160, label: t('请求方法') },
    { field: 'http_path', label: t('请求路径') },
    { field: 'status', width: 160, label: t('状态码') },
    { field: 'backend_duration', width: 160, label: t('耗时(毫秒)') },
    {
      field: 'error',
      width: 200,
      label: t('错误'),
      formatter: (row: any, column: any, cellValue: string) => {
        return formatValue(cellValue, column.property);
      },
    },
  ];
  table.value.headers = columns;
};

const getApigwStages = async () => {
  const pageParams = {
    no_page: true,
    order_by: 'name',
  };
  try {
    const res = await fetchApigwStages(apigwId.value, pageParams);
    stageList.value = res || [];
    if (stageList.value.length) {
      searchParams.value.stage_id = stageList.value[0].id;
    }
  } catch (e) {
    console.error(e);
  }
};

const getApigwAccessLogList = () => {
  const params = {
    ...searchParams.value,
    query: keyword.value,
    offset: (pagination.value.current - 1) * pagination.value.limit,
    limit: pagination.value.limit,
  };
  return fetchApigwAccessLogList(apigwId.value, params);
};

const getApigwAccessLogChart = () => {
  const params = {
    ...searchParams.value,
    query: keyword.value,
    no_page: true,
  };
  fetchApigwAccessLogChart(apigwId.value, params);
};

const getSearchData = async () => {
  isDataLoading.value = true;
  try {
    setSearchTimeRange();
    const [listRes, chartRes]: any = await Promise.all([getApigwAccessLogList(), getApigwAccessLogChart()]);
    chartData.value = chartRes?.data;
    renderChart(chartData.value);
    table.value.list = listRes?.data.results;
    table.value.fields = listRes?.data.fields;
    // 根据接口要求最大显示10000条以内数据，但总条数仍然显示为实际值
    pagination.value.count = Math.min(listRes?.data.count, 10000);
    nextTick(() => {
      const countDom = document.querySelector('.bk-page-total-count .stress');
      if (countDom) {
        // countDom?.innerText = listRes?.data.count;
      }
    });
    setTableHeader();
    updateTableEmptyConfig();
    tableEmptyConf.value.isAbnormal = false;
  } catch (e) {
    tableEmptyConf.value.isAbnormal = true;
  } finally {
    isPageLoading.value = false;
    isDataLoading.value = false;
    setTableHeader();
  }
};

const handleShortcutChange = (value: any, index: number) => {
  shortcutSelectedIndex.value = index;
  updateTableEmptyConfig();
};

const handleTimeChange = () => {
  nextTick(() => {
    pagination.value.current = 1;
    getSearchData();
  });
};

const handleStageSelected = (value: number) => {
  searchParams.value.stage_id = value;
  pagination.value.current = 1;
  getSearchData();
};

const handleSearch = () => {
  searchParams.value.query = keyword.value;
  console.log(keyword.value, 555);
  pagination.value.current = 1;
  getSearchData();
};

const handleClickUsageValue = (event: any) => {
  keyword.value = event.target.innerText;
};

const handlePageLimitChange = (limit: number) => {
  pagination.value.limit = limit;
  pagination.value.current = 1;
  getSearchData();
};

const handlePageChange = (newPage: number) => {
  pagination.value.current = newPage;
  getSearchData();
};

const handleRowClick = (row: any) => {
  tableRef.value.toggleRowExpansion(row);
};

const clearFilterKey = () => {
  keyword.value = '';
  if (datePickerRef?.value) {
    datePickerRef.value.shortcut = [, AccessLogStore.datepickerShortcuts[1]];
    shortcutSelectedIndex.value = 1;
  }
  handleSearch();
};

const updateTableEmptyConfig = () => {
  const time = dateTimeRange.value.some(Boolean);
  if (keyword.value || shortcutSelectedIndex.value !== 1) {
    tableEmptyConf.value.keyword = 'placeholder';
    return;
  } if (searchParams.value.stage_id || time) {
    tableEmptyConf.value.keyword = '$CONSTANT';
    return;
  }
  tableEmptyConf.value.keyword = '';
};

const getRowClassName = ({ row }: any) => {
  return (!(row.status >= 200 && row.status < 300) || row.error) ? 'exception' : '';
};

const chartResize = () => {
  nextTick(() => {
    chartInstance.value.resize();
  });
};

const initChart = () => {
  chartInstance.value = echarts.init(chartContainer.value);
  console.log(chartInstance.value, 5555);
  window.addEventListener('resize', chartResize);
};

const init = async () => {
  await getApigwStages();
  getSearchData();
};

watch(
  () => route,
  async (payload: any) => {
    if (payload.params?.id) {
      apigwId.value = Number(payload.params.id);
      await init();
    }
  },
  { immediate: true, deep: true },
);

onMounted(() => {
  initChart();
});
</script>

<style lang="scss" scoped>
.access-log-wrapper {
  min-height: calc(100vh - 208px);
  padding: 24px;

  .ag-top-header {
    min-height: 32px;
    margin-bottom: 20px;
    position: relative;

    :deep(.search-form) {
      width: 100% !important;
      max-width: 100% !important;
      display: inline-block;

      .bk-form-item {
        display: inline-flex;
        margin-bottom: 0;
        margin-left: 8px;
        vertical-align: middle;

        &:first-child {
          margin-left: 0;
        }

        .bk-form-label {
          width: auto !important;
          line-height: 32px;
          display: inline-block;
          padding: 0 15px 0 0;

          span {
            display: inline-block;
            line-height: 20px;
          }
        }

        .bk-form-content {
          margin-left: 0 !important;
        }
      }

      .ag-form-item-inline {
        margin-left: 8px !important;
        margin-top: 0px !important;

        .bk-form-content {
          display: flex !important;
          font-size: unset;
        }

        .suffix {
          margin-left: 4px;
        }
      }

      .top-search-input {
        width: 600px;
      }
    }
  }

  .list {
    margin-top: 16px;

    .details {
      position: relative;
      padding: 16px 0;

      .item {
        display: flex;
        margin-bottom: 8px;

        .label {
          position: relative;
          flex: none;
          width: 200px;
          font-weight: bold;
          color: #63656E;
          margin-right: 32px;
          text-align: right;

          .copy-btn {
            color: #C4C6CC;
            font-size: 12px;
            position: absolute;
            right: -18px;
            top: 4px;
            cursor: pointer;

            &:hover {
              color: #3A84FF;
            }
          }
        }

        .value {
          font-family: 'Courier New', Courier, monospace;
          flex: none;
          width: calc(100% - 300px);
          white-space: pre-wrap;
          word-break: break-word;
          color: #63656E;
          line-height: 20px;
        }
      }

      .share-btn {
        position: absolute;
        right: 0;
        top: 18px;
      }
    }

    .exception {
      background: #F9EDEC;

      &:hover {
        td {
          background: #F9EDEC;
        }
      }

      .status,
      .error {
        color: #FF5656;
      }
    }
  }
}

.chart-container {
  width: 100%;
  background: #FFF;
  border: 1px solid #DCDEE5;

  .chart-title {
    color: #262625;
    font-size: 14px;
    padding: 10px 0 0 10px;
  }

  .chart-el {
    width: 100%;
    height: 160px;
  }
}

.search-usage {
  font-size: 12px;
  color: #3A84FF;
  line-height: 32px;
  margin-left: 16px;
  cursor: pointer;
}

#access-log-search-usage-content {
  font-size: 12px;
  line-height: 26px;
  padding: 4px;

  .sample {
    .mode {
      color: #63656e;
    }

    .value {
      color: #3a84ff;
      cursor: pointer;
    }
  }

  .more {
    color: #63656e;
    border-top: 1px dashed #C4C6CC;
    margin-top: 10px;
    padding-top: 8px;

    .link {
      color: #3A84FF;
    }
  }
}

@media (max-width: 1753px) {
  :deep(.search-form) {
    width: 700px !important;

    .ag-form-item-inline {
      margin-left: 0px !important;
      margin-top: 10px !important;
    }

    .top-search-input {
      width: 526px;
    }

    .top-search-input-en {
      width: 460px;
    }
  }
}

.no-data-chart {
  height: 280px;
}
</style>
