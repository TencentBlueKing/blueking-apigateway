<template>
  <div class="access-log-wrapper page-wrapper-padding">
    <bk-loading :loading="!isPageLoading && isDataLoading" :z-index="100">
      <bk-collapse v-model="activeIndex">
        <bk-collapse-panel :name="1" class="collapse-panel mb16">
          <template #header>
            <div class="collapse-panel-header">
              <angle-up-fill :class="['panel-title-icon', activeIndex?.includes(1) ? '' : 'packUp']" />
              <span class="panel-title">{{ t('查询条件') }}</span>
            </div>
          </template>
          <template #content>
            <div class="ag-top-header">
              <bk-form class="search-form" form-type="vertical">
                <bk-form-item :label="t('起止时间')" class="ag-form-item-datepicker">
                  <bk-date-picker
                    ref="datePickerRef"
                    type="datetimerange"
                    style="width: 310px"
                    v-model="dateTimeRange"
                    :key="dateKey"
                    :placeholder="t('选择日期时间范围')"
                    :shortcuts="AccessLogStore.datepickerShortcuts"
                    :shortcut-close="true"
                    :use-shortcut-text="true"
                    :clearable="false"
                    :shortcut-selected-index="shortcutSelectedIndex"
                    @shortcut-change="handleShortcutChange"
                    @change="handlePickerChange"
                    @pick-success="handlePickerConfirm"
                  />
                </bk-form-item>
                <bk-form-item :label="t('环境')">
                  <bk-select
                    style="width: 200px" v-model="searchParams.stage_id" :clearable="false" searchable
                    @change="handleStageChange">
                    <bk-option v-for="option in stageList" :key="option.id" :id="option.id" :name="option.name">
                    </bk-option>
                  </bk-select>
                </bk-form-item>
                <bk-form-item :label="t('资源')">
                  <ResourceSearcher
                    v-model="searchParams.resource_id"
                    :list="resourceList"
                    :need-prefix="false"
                    style="width: 250px; margin-right: 8px;"
                    @change="handleResourceChange"
                  />
                </bk-form-item>
                <bk-form-item :label="t('查询语句')" class="ag-form-item-inline">
                  <SearchInput
                    v-model:mode-value="keyword"
                    @search="handleSearch"
                    @choose="handleChoose"
                    class="top-search-input"
                  />
                </bk-form-item>
                <bk-form-item label="" style="margin-left: 0">
                  <bk-button theme="primary" @click="handleSearch(keyword)">{{ t('查询') }}</bk-button>
                  <bk-button class="ml10" @click="handleClearFilterKey">{{ t('重置') }}</bk-button>
                </bk-form-item>
              </bk-form>
            </div>
          </template>
        </bk-collapse-panel>
        <div class="search-term" v-show="!!searchConditions?.length">
          <funnel class="icon" />
          <span class="title">{{ t('检索项：') }}</span>
          <bk-tag closable v-for="item in searchConditions" :key="item" @close="handleTagClose(item)">
            <!-- eslint-disable-next-line vue/no-v-html -->
            <span v-html="generateTagContent(item)"></span>
          </bk-tag>
          <bk-button theme="primary" text @click="handleClearSearch">
            {{ t('清除') }}
          </bk-button>
        </div>
        <bk-collapse-panel :name="2" class="collapse-panel mb32" @change="handlePanelChange">
          <template #header>
            <div class="collapse-panel-header">
              <angle-up-fill :class="['panel-title-icon', activeIndex?.includes(2) ? '' : 'packUp']" />
              <span class="panel-title">{{ t('请求数') }}</span>
            </div>
          </template>
          <template #content>
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
          </template>
        </bk-collapse-panel>

        <bk-collapse-panel :name="3" class="collapse-panel">
          <template #header>
            <div class="collapse-panel-header">
              <angle-up-fill :class="['panel-title-icon', activeIndex?.includes(3) ? '' : 'packUp']" />
              <span class="panel-title">{{ t('日志详情') }}</span>
              <span class="panel-total">
                {{ t('共') }}
                <span>{{ pageCount }}</span>
                {{ t('条') }}
              </span>
              <span
                :class="['download-logs', { 'disabled-logs': pageCount === 0 }]"
                @click="handleDownload"
                v-bk-tooltips="{ content: t('检索出的日志条数为 0，不需要下载'), disabled: pageCount !== 0 }">
                <ag-icon name="download" size="16" />
                {{ t('下载日志') }}
              </span>
              <bk-alert
                class="flex1"
                theme="warning"
                closable
                v-if="table?.list?.length >= 10000"
                :title="t('每次查询操作最多只会返回 10,000 条记录。如果您未能查看全部需要的日志，请尝试缩小查询的时间范围')"
              />
            </div>
          </template>
          <template #content>
            <div class="list">
              <bk-table
                ref="tableRef"
                size="small"
                class="access-log-table"
                border="outer"
                :data="table.list"
                :columns="table.headers"
                :pagination="pagination"
                :remote-pagination="true"
                :row-style="{ cursor: 'pointer' }"
                :row-class="getRowClass"
                :show-overflow-tooltip="true"
                :settings="table.settings"
                @row-click="handleRowClick"
                @page-value-change="handlePageChange"
                @page-limit-change="handlePageLimitChange"
              >
                <template #expandRow="row">
                  <dl class="details">
                    <div
                      class="item"
                      v-for="({ label, field/*, is_filter: showCopy*/ }, index) in table.fields"
                      :key="index"
                    >
                      <dt class="label">
                        {{ label }}
                        <span class="fields">
                          ( <span
                            class="fields-main"
                            v-bk-tooltips="t('复制')"
                            @click.stop="copy(field)">
                            {{ field }}
                          </span> ) :
                        </span>
                        <!-- <i
                          v-if="showCopy"
                          v-bk-tooltips="$t('复制字段名')"
                          @click.stop="copy(field)"
                          class="apigateway-icon icon-ag-clipboard copy-btn"
                        >
                        </i> -->
                      </dt>
                      <dd class="value">

                        <span class="respond" v-if="field === 'response_body' && row.status === '200'">
                          <info-line class="respond-icon" /><span>{{ t('状态码为 200 时不记录响应正文') }}</span>
                        </span>
                        <span v-else>
                          {{ formatValue(row[field], field) }}
                        </span>

                        <span class="opt-btns" v-if="row[field]">
                          <copy-shape v-bk-tooltips="t('复制')" @click="handleRowCopy(field, row)" class="opt-copy" />
                          <template v-if="showOpts(field)">
                            <enlarge-line v-bk-tooltips="t('添加到本次检索')" @click="handleInclude(field, row)" />
                            <narrow-line v-bk-tooltips="t('从本次检索中排除')" @click="handleExclude(field, row)" />
                          </template>
                        </span>

                      </dd>
                    </div>
                    <bk-button
                      class="share-btn"
                      theme="primary"
                      outline
                      @click="handleClickCopyLink(row)"
                      :loading="isShareLoading">
                      {{ t('复制分享链接') }}
                    </bk-button>
                  </dl>
                </template>
                <template #empty>
                  <TableEmpty
                    :keyword="tableEmptyConf.keyword" :abnormal="tableEmptyConf.isAbnormal" @reacquire="getSearchData"
                    @clear-filter="handleClearFilterKey" />
                </template>
              </bk-table>
            </div>
          </template>
        </bk-collapse-panel>
      </bk-collapse>
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
import {
  merge,
  trim,
  uniq,
} from 'lodash';
import { copy } from '@/common/util';
import { SearchParamsInterface } from './common/type';
import { useCommon, useAccessLog } from '@/store';
import { userChartIntervalOption } from '@/hooks';
import {
  fetchApigwAccessLogList,
  fetchApigwAccessLogChart,
  fetchApigwStages,
  fetchApigwAccessLogShareLink,
  getApigwResources,
  exportLogs,
} from '@/http';
import {
  AngleUpFill,
  CopyShape,
  EnlargeLine,
  NarrowLine,
  InfoLine,
  Funnel,
} from 'bkui-vue/lib/icon';
import { Message } from 'bkui-vue';
import { useStorage } from '@vueuse/core';
import AgIcon from '@/components/ag-icon.vue';
import ResourceSearcher from '@/views/operate-data/statistics-report/components/resource-searcher.vue';

const { t } = i18n.global;
const { getChartIntervalOption } = userChartIntervalOption();
const commonStore = useCommon();
const AccessLogStore = useAccessLog();
// const globalProperties = useGetGlobalProperties();
// const { GLOBAL_CONFIG } = globalProperties;
// 从localStorage 提取搜索历史
const queryHistory = useStorage('access-log-query-history', []);
const activeIndex = ref<number[]>([1, 2, 3]);
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
const resourceList = ref<any>([]);
const apigwId = ref(commonStore.apigwId);
const pagination = ref({
  current: 1,
  count: 0,
  limit: 10,
  showTotalCount: true,
});
const searchParams = ref<SearchParamsInterface>({
  stage_id: 0,
  resource_id: '',
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
  settings: {
    fields: [
      { label: t('请求ID'), field: 'request_id' },
      { label: t('请求时间'), field: 'timestamp' },
      { label: t('蓝鲸应用'), field: 'app_code' },
      { label: t('蓝鲸用户'), field: 'bk_username' },
      { label: t('客户端IP'), field: 'client_ip' },
      { label: t('环境'), field: 'stage' },
      { label: t('资源ID'), field: 'resource_id' },
      { label: t('资源名称'), field: 'resource_name' },
      { label: t('请求方法'), field: 'method', disabled: true },
      { label: t('请求域名'), field: 'http_host' },
      { label: t('请求路径'), field: 'http_path', disabled: true },
      { label: 'QueryString', field: 'params' },
      { label: 'Body', field: 'body' },
      { label: t('后端请求方法'), field: 'backend_method' },
      { label: t('后端Scheme'), field: 'backend_scheme' },
      { label: t('后端域名'), field: 'backend_host' },
      { label: t('后端路径'), field: 'backend_path' },
      { label: t('响应体大小'), field: 'response_size' },
      { label: t('状态码'), field: 'status' },
      { label: t('请求总耗时'), field: 'request_duration' },
      { label: t('耗时(毫秒)'), field: 'backend_duration' },
      { label: t('错误编码名称'), field: 'code_name' },
      { label: t('错误'), field: 'error' },
      { label: t('响应说明'), field: 'response_desc' },
    ],
    extCls: 'hide-table-setting-line-height',
    checked: ['timestamp', 'method', 'http_path', 'status', 'backend_duration', 'error'],
  },
});
const includeObj = ref<string[]>([]);
const excludeObj = ref<string[]>([]);

const searchConditions = computed(() => {
  const res: string[] = [];
  includeObj.value?.forEach((item: string) => {
    const tempArr = item?.split(':');
    res.push(`${tempArr[0]}=${tempArr[1]}`);
  });
  excludeObj.value?.forEach((item: string) => {
    const tempArr = item?.split(':');
    res.push(`${tempArr[0]}!=${tempArr[1]}`);
  });
  return res;
});

const pageCount = computed(() => {
  return pagination.value.count;
});

// const searchUsage = ref({
//   showed: false,
// });
const chartData: Record<string, any> = ref({});
const stageList = ref([]);

const isShowChart = computed(() => {
  return chartData.value?.series?.length > 0;
});

// const localLanguage = computed(() => {
//   return 'zh-cn';
// });

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

const handlePanelChange = ({ name }: any) => {
  if (name === 2) {
    chartResize();
  }
};

const renderChart = (data: Record<string, any>) => {
  const { series, timeline } = data;
  const xAxisData = timeline.map((time: number) => dayjs.unix(time).format('YYYY-MM-DD\nHH:mm:ss'));
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
      backgroundColor: 'rgba(255, 255, 255, 1)',
      textStyle: {
        fontSize: 12,
        color: '#63656E',
        lineHeight: 24,
      },
      padding: [6, 10],
      extraCssText: 'box-shadow: 0 0 12px 4px #31323826;',
      formatter(params: any) {
        return `${params.name}<br />请求数: ${formatterValue(params)}`;
      },
    },
    toolbox: {
      right: 22,
      top: -10,
      feature: {
        dataZoom: {
          show: true,
          yAxisIndex: 'none',
          iconStyle: {
            opacity: 0,
          },
        },
      },
    },
  };
  const timeDuration = timeline[timeline.length - 1] - timeline[0];
  const intervalOption = getChartIntervalOption(timeDuration, 'time', 'xAxis');
  chartInstance.value.setOption(merge(options, intervalOption));
  chartInstance.value?.dispatchAction({
    type: 'takeGlobalCursor',
    key: 'dataZoomSelect',
    dataZoomSelectActive: true,
  });
  chartResize();
};

const getResources = async () => {
  const { apigwId } = commonStore;
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
    isDataLoading.value = false;
  }
};

const setTableHeader = () => {
  const columns =  [
    {
      type: 'expand',
      width: 30,
      minWidth: 30,
      showOverflowTooltip: false,
    },
    { field: 'request_id', width: 180, label: t('请求ID') },
    {
      field: 'timestamp',
      width: 180,
      label: t('请求时间'),
      render: ({ data }: Record<string, any>) => {
        return formatValue(data.timestamp, 'timestamp');
      },
    },
    { field: 'app_code', width: 100, label: t('蓝鲸应用') },
    { field: 'bk_username', width: 100, label: t('蓝鲸用户') },
    { field: 'client_ip', width: 100, label: t('客户端IP') },
    { field: 'stage', width: 80, label: t('环境') },
    { field: 'resource_id', width: 80, label: t('资源ID') },
    { field: 'resource_name', width: 160, label: t('资源名称') },
    { field: 'method', width: 100, label: t('请求方法') },
    { field: 'http_host', width: 160, label: t('请求域名') },
    { field: 'http_path', label: t('请求路径'), width: 260 },
    { field: 'params', width: 120, label: 'QueryString' },
    { field: 'body', width: 120, label: 'Body' },
    { field: 'backend_method', width: 120, label: t('后端请求方法') },
    { field: 'backend_scheme', width: 120, label: t('后端Scheme') },
    { field: 'backend_host', width: 160, label: t('后端域名') },
    { field: 'backend_path', width: 160, label: t('后端路径')  },
    { field: 'response_size', width: 100, label: t('响应体大小') },
    { field: 'status', width: 100, label: t('状态码') },
    { field: 'request_duration', width: 120, label: t('请求总耗时') },
    { field: 'backend_duration', width: 120, label: t('耗时(毫秒)') },
    { field: 'code_name', width: 120, label: t('错误编码名称') },
    {
      field: 'error',
      width: 120,
      label: t('错误'),
      showOverflowTooltip: true,
      render: ({ data }: Record<string, any>) => {
        return data.error || '--';
      },
    },
    { field: 'response_desc', width: 120, label: t('响应说明') },
  ];
  table.value.headers = columns;
};

const handleResourceChange = (value: any) => {
  searchParams.value.resource_id = value;
  getSearchData();
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

const getPayload = () => {
  const params: any = {
    ...searchParams.value,
    query: keyword.value,
  };

  let includeStr = '';
  includeObj.value?.forEach((item: string) => {
    includeStr += `&include=${item}`;
  });
  let excludeStr = '';
  excludeObj.value?.forEach((item: string) => {
    excludeStr += `&exclude=${item}`;
  });

  return {
    params,
    path: includeStr + excludeStr,
  };
};

const getApigwAccessLogList = async () => {
  const { params, path } = getPayload();
  params.offset = (pagination.value.current - 1) * pagination.value.limit;
  params.limit = pagination.value.limit;

  return await fetchApigwAccessLogList(apigwId.value, params, path);
};

const getApigwAccessLogChart = async () => {
  const { params, path } = getPayload();
  params.no_page = true;

  return await fetchApigwAccessLogChart(apigwId.value, params, path);
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
    chartInstance.value?.dispatchAction({
      type: 'restore',
    });
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

const handleRowCopy = (field:  string, row: any) => {
  const copyStr = `${field}: ${row[field]}`;
  copy(copyStr);
};

const handleInclude = (field:  string, row: any) => {
  const fieldStr = `${field}:${row[field]}`;
  includeObj.value?.push(fieldStr);
  includeObj.value = Array.from(new Set(includeObj.value));

  const index = excludeObj.value?.indexOf(fieldStr);
  if (index !== -1) {
    excludeObj.value?.splice(index, 1);
  }

  getSearchData();
};

const handleExclude = (field:  string, row: any) => {
  const fieldStr = `${field}:${row[field]}`;

  excludeObj.value?.push(fieldStr);
  excludeObj.value = Array.from(new Set(excludeObj.value));

  const index = includeObj.value?.indexOf(fieldStr);
  if (index !== -1) {
    includeObj.value?.splice(index, 1);
  }

  getSearchData();
};

const showOpts = (field: string) => {
  const fieldArr = ['request_id', 'app_code', 'client_ip', 'resource_name', 'method', 'status'];
  if (fieldArr?.includes(field)) {
    return true;
  }
  return false;
};

const handleTagClose = (item: string) => {
  if (!item) return;

  if (item?.indexOf('!=') !== -1) { // 排除项
    const tempArr = item?.split('!=');
    const field = `${tempArr[0]}:${tempArr[1]}`;

    const index = excludeObj.value?.indexOf(field);
    if (index !== -1) {
      excludeObj.value?.splice(index, 1);
    }
  } else {
    const tempArr = item?.split('=');
    const field = `${tempArr[0]}:${tempArr[1]}`;

    const index = includeObj.value?.indexOf(field);
    if (index !== -1) {
      includeObj.value?.splice(index, 1);
    }
  }
  getSearchData();
};

const generateTagContent = (item: string) => {
  if (!item) {
    return;
  }
  if (item.indexOf('!=') !== -1) {
    return item.replace('!=', '<span class="exclude-equal">!=</span>');
  }
  return item.replace('=', '<span class="include-equal">=</span>');
};

const handleClearSearch = () => {
  includeObj.value = [];
  excludeObj.value = [];
  getSearchData();
};

const handleDownload = async (e: Event) => {
  if (pagination.value.count === 0) {
    return;
  }
  e.stopPropagation();
  try {
    const { params, path } = getPayload();
    params.offset = (pagination.value.current - 1) * pagination.value.limit;
    params.limit = 10000;

    const res = await exportLogs(apigwId.value, params, path);
    if (res.success) {
      Message({
        message: t('导出成功'),
        theme: 'success',
      });
    }
  } catch ({ error }: any) {
    Message({
      message: error.message || t('导出失败'),
      theme: 'error',
    });
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

// 处理用户自行输入日期，点击确认后的情况。v-model 不会自动更新，要从 picker 内部拿输入的日期。
const handlePickerConfirm = () => {
  const internalValue = datePickerRef.value?.internalValue;
  if (internalValue) {
    dateTimeRange.value = internalValue;
    handlePickerChange();
  } else {
    Message({ theme: 'warning', message: t('输入的时间错误'), delay: 2000, dismissable: false });
  }
};

const handleStageChange = (value: number) => {
  searchParams.value.stage_id = value;
  pagination.value.current = 1;
  getSearchData();
};

const handleSearch = (value: string) => {
  keyword.value = value;
  searchParams.value.query = keyword.value;
  pagination.value.current = 1;
  // 若是非空字符串则写入搜索历史
  if (trim(value) !== '') {
    queryHistory.value.unshift(value);
    queryHistory.value = uniq(queryHistory.value).slice(0, 10);
  }
  getSearchData();
};

const handleChoose = (search: string) => {
  keyword.value = search;
};

const handlePageLimitChange = (limit: number) => {
  pagination.value = Object.assign(pagination.value, { current: 1, limit });
  getSearchData();
};

const handlePageChange = (current: number) => {
  pagination.value = Object.assign(pagination.value, { current });
  getSearchData();
};

const handleRowClick = (e: Event, row: Record<string, any>) => {
  e.stopPropagation();
  row.isExpand = !row.isExpand;
  nextTick(() => {
    tableRef.value.setRowExpand(row,  row.isExpand);
  });
};

const handleClearFilterKey = () => {
  keyword.value = '';
  if (stageList.value.length) {
    searchParams.value.stage_id = stageList.value[0].id;
  }
  searchParams.value.resource_id = '';
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
  await getResources();
  await getSearchData();
};

const initChart = async () => {
  chartInstance.value = markRaw(echarts.init(chartContainer.value));
  window.addEventListener('resize', chartResize);

  chartInstance.value.on('datazoom', (event: {batch: {startValue: number, endValue: number}[]}) => {
    const { startValue, endValue } = event.batch[0];

    // 获取x轴缩放后的数据范围
    const zoomedXAxisData = chartInstance.value.getOption().xAxis[0].data.slice(startValue, endValue + 1);
    const startTime = zoomedXAxisData[0];
    const endTime = zoomedXAxisData[zoomedXAxisData.length - 1];

    if (startTime === endTime) {
      dateTimeRange.value = [];
      shortcutSelectedIndex.value = 1;
      [datePickerRef.value.shortcut] = [AccessLogStore.datepickerShortcuts[1]];
    } else {
      shortcutSelectedIndex.value = -1;
      dateTimeRange.value = [new Date(startTime), new Date(endTime)];
    }

    dateKey.value = String(+new Date());
    handlePickerChange();
  });
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
  padding-bottom: 24px;

  .collapse-panel {
    background-color: #fff;
    padding: 24px;
    padding-bottom: 8px;
    .collapse-panel-header {
      display: flex;
      align-items: center;
      cursor: pointer;
      margin-bottom: 24px;
      .panel-title {
        margin-left: 10px;
        font-weight: 700;
        font-size: 14px;
        color: #313238;
      }
      .panel-total {
        color: #63656e;
        font-size: 12px;
        margin: 0 10px;
        span {
          font-weight: bold;
        }
      }
      .download-logs {
        margin-right: 14px;
        color: #3A84FF;
        font-size: 12px;
        .icon-ag-download {
          font-size: 16px;
          margin-right: -4px;
        }
        &.disabled-logs {
          color: #c4c6cc;
          cursor: not-allowed;
        }
      }
      .panel-title-icon {
        transition: .2s;
      }
      .packUp {
        transform: rotate(-90deg);
      }
    }
  }

  .search-term {
    margin-bottom: 16px;
    display: flex;
    align-items: center;
    .icon {
      padding-top: 2px;
      margin-right: 4px;
      color: #979BA5;
      font-size: 16px;
    }
    .title {
      font-size: 12px;
      color: #63656E;
    }
    :deep(.bk-tag) {
      background-color: #EAEBF0;
      border-radius: 2px;
      &:not(:nth-last-child(1)) {
        margin-right: 8px;
      }
    }
  }

  .mb16 {
    margin-bottom: 16px;
  }

  .mb32 {
    margin-bottom: 32px;
  }

  .ag-top-header {
    padding-left: 24px;
    padding-right: 4px;

    :deep(.search-form) {
      .bk-form-item {
        display: inline-block;
        margin-bottom: 16px;
        margin-left: 8px;

        &:first-child {
          margin-left: 0;
        }

        .bk-form-label {
          line-height: 32px;
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
        margin-top: 0px !important;
        margin-left: 0px !important;
        margin-right: 8px;

        .bk-form-content {
          display: flex !important;
          font-size: unset;
        }

        .suffix {
          margin-left: 4px;
        }
      }

      .top-search-input {
        width: 400px;
      }
    }
  }

  .list {
    padding-left: 24px;
    margin-top: 16px;

    .details {
      position: relative;
      padding: 16px 0;
      padding-left: 55px;
      font-size: 12px;
      background-color: #ffffff;
      .item {
        display: flex;
        align-items: center;
        margin-bottom: 8px;

        .label {
          font-size: 12px;
          position: relative;
          flex: none;
          width: 212px;
          color: #63656E;
          margin-right: 12px;
          text-align: right;
          .fields {
            color: #979BA5;
            .fields-main {
              cursor: pointer;
              &:hover {
                background-color: #f0f1f5;
              }
            }
          }

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
          color: #313238;
          line-height: 20px;
          display: flex;
          align-items: center;

          .respond {
            font-size: 12px;
            color: #FF9C01;
            display: flex;
            align-items: center;
            .respond-icon {
              margin-right: 4px;
              margin-top: -2px;
            }
          }

          .opt-btns {
            color: #979BA5;
            font-size: 16px;
            padding-top: 3px;
            margin-left: 10px;
            &:hover {
              color: #1768EF;
            }
            .opt-copy {
              font-size: 14px;
            }
            span {
              cursor: pointer;
              margin-right: -4px;
            }
          }
        }
      }

      .share-btn {
        position: absolute;
        right: 28px;
        top: 32px;
      }
    }
  }
}

:deep(.bk-collapse-content) {
  padding: 0;
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

.chart {
  padding-left: 24px;
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

    .ag-form-item-inline {
      margin-left: 0px !important;
      margin-top: 10px !important;
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
.flex1 {
  flex: 1;
}
</style>

<style>
.hide-table-setting-line-height .setting-body-line-height {
  display: none !important;
}
.access-log-popover {
  top: 10px !important;
}
.include-equal,
.exclude-equal {
  font-weight: bold;
  font-size: 16px;
  vertical-align: bottom;
}
.exclude-equal {
  color: #EA3636;
}
.include-equal {
  color: #2DCB56;
}
</style>
