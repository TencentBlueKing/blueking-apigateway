<template>
  <div class="access-log-wrapper">
    <div class="ag-top-header">
      <bk-form class="search-form" form-type="vertical">
        <bk-form-item :label="t('选择时间')" class="ag-form-item-datepicker">
          <bk-date-picker
            ref="datePickerRef"
            type="datetimerange"
            style="width: 320px"
            v-model="dateTimeRange"
            :key="dateKey"
            :placeholder="t('选择日期时间范围')"
            :shortcuts="AccessLogStore.datepickerShortcuts"
            :shortcut-close="true"
            :use-shortcut-text="true"
            :clearable="false"
            :shortcut-selected-index="shortcutSelectedIndex"
            @shortcut-change="handleShortcutChange" @change="handlePickerChange" />
        </bk-form-item>
        <bk-form-item :label="t('环境')">
          <bk-select
            style="width: 150px" v-model="searchParams.stage_id" :clearable="false" searchable
            @selected="handleStageSelected">
            <bk-option v-for="option in stageList" :key="option.id" :id="option.id" :name="option.name">
            </bk-option>
          </bk-select>
        </bk-form-item>
        <bk-form-item :label="t('查询条件')" class="ag-form-item-inline">
          <SearchInput
            v-model:modeValue="keyword"
            @search="handleSearch"
            :class="[
              'top-search-input',
              localLanguage === 'en' ? 'top-search-input-en' : '',
            ]"
          />
          <span>
            <bk-popover
              :is-show="searchUsage.showed" trigger="click" width="450" theme="light" placement="bottom"
              ext-cls="access-log-popover" @after-show="handlePopoverShow" @after-hidden="handlePopoverHidden">
              <bk-button text theme="primary" class="search-usage">
                {{ `${searchUsage.showed ? t("隐藏示例") : t("显示示例")}` }}
              </bk-button>
              <template #content>
                <div class="access-log-search-usage-content">
                  <div class="sample">
                    <p>
                      <span class="mode">{{ t("匹配包含某个关键字") }}: </span>
                      <span class="value" @click="handleClickUsageValue">
                        request_id: b3e2497532e54f518b3d1267fb67c83a
                      </span>
                    </p>
                    <p>
                      <span class="mode">{{ t("多个关键字匹配") }}: </span>
                      <span class="value" @click="handleClickUsageValue">
                        (app_code: "app-template" AND client_ip: "1.0.0.1") OR
                        resource_name: get_user
                      </span>
                    </p>
                    <p>
                      <span class="mode">{{ t("不包含关键字") }}: </span>
                      <span class="value" @click="handleClickUsageValue">-status: 200</span>
                    </p>
                    <p>
                      <span class="mode">{{ t("范围匹配") }}: </span>
                      <span class="value" @click="handleClickUsageValue">duration: [5000 TO 30000]</span>
                    </p>
                  </div>
                  <div class="more">
                    {{ t("更多示例请参阅") }}
                    <a class="link" target="_blank" :href="GLOBAL_CONFIG.DOC.QUERY_USE">
                      {{ t("“请求流水查询规则”") }}
                    </a>
                  </div>
                </div>
              </template>
            </bk-popover>
          </span>
        </bk-form-item>
      </bk-form>
    </div>

    <bk-loading :loading="!isPageLoading && isDataLoading" :z-index="100">
      <div class="chart">
        <div class="chart-container">
          <div class="chart-title">{{ t("请求数") }}</div>
          <div v-show="isShowChart" ref="chartContainer" class="chart-el" />
          <div v-show="!isShowChart && !isPageLoading" class="no-data-chart">
            <slot name="empty">
              <TableEmpty
                :keyword="tableEmptyConf.keyword" :abnormal="tableEmptyConf.isAbnormal"
                @reacquire="getSearchData" @clear-filter="handleClearFilterKey" />
            </slot>
          </div>
        </div>
      </div>
      <div class="list">
        <bk-table
          ref="tableRef"
          size="small"
          class="access-log-table"
          :data="table.list"
          :columns="table.headers"
          :pagination="pagination"
          :remote-pagination="true"
          :row-style="{ cursor: 'pointer' }"
          :row-class="getRowClass"
          :show-overflow-tooltip="true"
          @row-click="handleRowClick"
          @page-value-change="handlePageChange"
          @page-limit-change="handlePageLimitChange"
        >
          <template #expandRow="row">
            <dl class="details">
              <div
                class="item"
                v-for="({ label, field, is_filter: showCopy }, index) in table.fields"
                :key="index">
                <dt class="label">
                  {{label}}
                  <i
                    v-if="showCopy"
                    v-bk-tooltips="$t('复制字段名')"
                    @click.stop="copy(field)"
                    class="apigateway-icon icon-ag-clipboard copy-btn"
                  >
                  </i>
                </dt>
                <dd class="value">{{ formatValue(row[field], field) }}</dd>
              </div>
              <bk-button
                class="share-btn"
                theme="primary"
                outline
                @click="handleClickCopyLink(row)"
                :loading="isShareLoading"> {{ $t('复制分享链接') }} </bk-button>
            </dl>
          </template>
          <template #empty>
            <TableEmpty
              :keyword="tableEmptyConf.keyword" :abnormal="tableEmptyConf.isAbnormal" @reacquire="getSearchData"
              @clear-filter="handleClearFilterKey" />
          </template>
        </bk-table>
      </div>
    </bk-loading>
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
import { ref, computed, nextTick, onMounted, onBeforeUnmount, markRaw } from 'vue';
import { merge } from 'lodash';
import { copy } from '@/common/util';
import { SearchParamsInterface } from './common/type';
import { useCommon, useAccessLog } from '@/store';
import { useGetGlobalProperties, userChartIntervalOption } from '@/hooks';
import {
  fetchApigwAccessLogList,
  fetchApigwAccessLogChart,
  fetchApigwStages,
  fetchApigwAccessLogShareLink,
} from '@/http';

const { t } = i18n.global;
const { getChartIntervalOption } = userChartIntervalOption();
const commonStore = useCommon();
const AccessLogStore = useAccessLog();
const globalProperties = useGetGlobalProperties();
const { GLOBAL_CONFIG } = globalProperties;

const keyword = ref('');
const chartInstance = ref(null);
const chartContainer = ref(null);
const tableRef = ref(null);
const datePickerRef = ref(null);
const isPageLoading = ref(false);
const isDataLoading = ref(false);
const isShareLoading = ref(false);
const shortcutSelectedIndex = ref(1);
const dateKey = ref('dateKey');
const dateTimeRange = ref([]);
const apigwId = ref(commonStore.apigwId);
const pagination = ref({
  current: 1,
  count: 0,
  limit: 10,
  showTotalCount: true,
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
});
const chartData: Record<string, any> = ref({});
const stageList = ref([]);

const isShowChart = computed(() => {
  return chartData.value?.series?.length > 0;
});

const localLanguage = computed(() => {
  return 'zh-cn';
});

const formatterValue = (params: Record<string, any>) => {
  return `${params.value.toLocaleString()}次`;
};

const formatValue = (value: any, field: string) => {
  if (value && ['timestamp'].includes(field)) {
    return dayjs.unix(value).format('YYYY-MM-DD HH:mm:ss ZZ');
  }
  return value || '--';
};

const formatDatetime = (timeRange: number[]) => {
  return [+new Date(`${timeRange[0]}`) / 1000, +new Date(`${timeRange[1]}`) / 1000];
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

const renderChart = (data: Record<string, any>) => {
  const { series, timeline } = data;
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
    series: [
      {
        type: 'bar',
        data: series || [],
        barMaxWidth: 60,
        itemStyle: {
          color: '#5B8FF9',
        },
      },
    ],
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
  chartResize();
};

const setTableHeader = () => {
  const columns =  [
    {
      type: 'expand',
      width: 30,
      minWidth: 30,
    },
    {
      field: 'timestamp',
      width: 220,
      label: t('请求时间'),
      render: ({ data }: Record<string, any>) => {
        return formatValue(data.timestamp, 'timestamp');
      },
    },
    { field: 'method', width: 160, label: t('请求方法') },
    { field: 'http_path', label: t('请求路径') },
    { field: 'status', width: 160, label: t('状态码') },
    { field: 'backend_duration', width: 100, label: t('耗时(毫秒)') },
    {
      field: 'error',
      width: 200,
      label: t('错误'),
      showOverflowTooltip: true,
      render: ({ data }: Record<string, any>) => {
        return data.error || '--';
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

const getApigwAccessLogList = async () => {
  const params = {
    ...searchParams.value,
    query: keyword.value,
    offset: (pagination.value.current - 1) * pagination.value.limit,
    limit: pagination.value.limit,
  };
  return await fetchApigwAccessLogList(apigwId.value, params);
};

const getApigwAccessLogChart = async () => {
  const params = {
    ...searchParams.value,
    query: keyword.value,
    no_page: true,
  };
  return await fetchApigwAccessLogChart(apigwId.value, params);
};

const getSearchData = async () => {
  isDataLoading.value = true;
  try {
    setSearchTimeRange();
    const [listRes, chartRes]: any = await Promise.all([
      getApigwAccessLogList(),
      getApigwAccessLogChart(),
    ]);
    chartData.value = chartRes || {};
    renderChart(chartData.value);
    table.value = Object.assign(table.value, {
      list: listRes?.results || [],
      fields: listRes?.fields || [],
    });
    table.value.list.forEach((item) => {
      item.isExpand = false;
    });
    pagination.value.count = listRes?.count || 0;
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


const handleClickCopyLink = async ({ request_id }: any) => {
  const params = { request_id };
  isShareLoading.value = true;
  try {
    const { link } = await fetchApigwAccessLogShareLink(apigwId.value, params);
    copy(link || '');
  } catch (e) {
    console.error(e);
  } finally {
    isShareLoading.value = false;
  }
};

const handleShortcutChange = (value: Record<string, any>, index: number) => {
  shortcutSelectedIndex.value = index;
  updateTableEmptyConfig();
};

const handlePickerChange = () => {
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

const handleSearch = (value: string) => {
  keyword.value = value;
  searchParams.value.query = keyword.value;
  pagination.value.current = 1;
  getSearchData();
};

const handlePopoverShow = ({ isShow }: Record<string, boolean>) => {
  searchUsage.value.showed = isShow;
};

const handlePopoverHidden = ({ isShow }: Record<string, boolean>) => {
  searchUsage.value.showed = isShow;
};

const handleClickUsageValue = (event: any) => {
  keyword.value = event.target.innerText;
};

const handlePageLimitChange = (limit: number) => {
  pagination.value = Object.assign(pagination.value, { current: 1, limit });
  getSearchData();
};

const handlePageChange = (current: number) => {
  pagination.value = Object.assign(pagination.value, { current });
  getSearchData();
};

const handleRowClick = (event: any, row: any) => {
  row.isExpand = !row.isExpand;
  nextTick(() => {
    tableRef.value.setRowExpand(row,  row.isExpand);
  });
};

const handleClearFilterKey = () => {
  keyword.value = '';
  [datePickerRef.value.shortcut] = [AccessLogStore.datepickerShortcuts[1]];
  dateTimeRange.value = [];
  shortcutSelectedIndex.value = 1;
  dateKey.value = String(+new Date());
  setSearchTimeRange();
  handleSearch('');
};

const updateTableEmptyConfig = () => {
  const time = dateTimeRange.value.some(Boolean);
  if (keyword.value || !table.value.list.length) {
    tableEmptyConf.value.keyword = 'placeholder';
    return;
  }
  if (searchParams.value.stage_id || time) {
    tableEmptyConf.value.keyword = '$CONSTANT';
    return;
  }
  tableEmptyConf.value.keyword = '';
};

const getRowClass = (row: Record<string, any>) => {
  return !(row.status >= 200 && row.status < 300) || row.error ? 'exception' : '';
};

const chartResize = () => {
  nextTick(() => {
    chartInstance.value.resize();
  });
};

const initData = async () => {
  await getApigwStages();
  await getSearchData();
};

const initChart = async () => {
  chartInstance.value = markRaw(echarts.init(chartContainer.value));
  window.addEventListener('resize', chartResize);
};

onMounted(() => {
  initData();
  initChart();
});

onBeforeUnmount(() => {
  window.removeEventListener('resize', chartResize);
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
      font-size: 12px;
      background-color: #ffffff;
      .item {
        display: flex;
        margin-bottom: 8px;

        .label {
          position: relative;
          flex: none;
          width: 200px;
          font-weight: bold;
          color: #63656e;
          margin-right: 32px;
          text-align: right;

          .copy-btn {
            color: #c4c6cc;
            font-size: 12px;
            position: absolute;
            right: -18px;
            top: 4px;
            cursor: pointer;

            &:hover {
              color: #3a84ff;
            }
          }
        }

        .value {
          font-family: "Courier New", Courier, monospace;
          flex: none;
          width: calc(100% - 400px);
          white-space: pre-wrap;
          word-break: break-word;
          color: #63656e;
          line-height: 20px;
        }
      }

      .share-btn {
        position: absolute;
        right: 30px;
        top: 18px;
      }
    }
  }
}

:deep(.exception) {
  background: #f9edec;
  &:hover {
    td {
      background: #f9edec;
    }
  }
  td {
    background: #f9edec !important;
    &:nth-child(5),
    &:last-child {
      .cell {
        color: #ff5656;
      }
    }
  }
}

.chart-container {
  width: 100%;
  background: #fff;
  border: 1px solid #dcdee5;

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
  color: #3a84ff;
  margin-left: 16px;
}

.access-log-search-usage-content {
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
    border-top: 1px dashed #c4c6cc;
    margin-top: 10px;
    padding-top: 8px;

    .link {
      color: #3a84ff;
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

:deep(.bk-picker-confirm-action) {
  a:first-child {
    display: none;
  }
}

:deep(.access-log-table) {
  .head-text {
    font-weight: 700!important;
    color: #63656e!important;
  }
}
</style>

<style>
.access-log-popover {
  top: 10px !important;
}
</style>
