<template>
  <div class="page-wrapper-padding app-content">
    <div class="ag-top-header">
      <bk-form class="search-form" form-type="inline" label-width="84">
        <bk-form-item :label="$t('选择时间')" class="ag-form-item-datepicker top-form-item-time">
          <bk-date-picker
            style="width: 320px;"
            ref="datePickerRef"
            v-model="dateTimeRange"
            :key="dateKey"
            :placeholder="$t('选择日期时间范围')"
            :type="'datetimerange'"
            :shortcuts="shortcutsInDay"
            :shortcut-close="true"
            :use-shortcut-text="true"
            :clearable="false"
            :shortcut-selected-index="shortcutSelectedIndex"
            @shortcut-change="handleShortcutChange"
            @pick-success="handleTimeChange">
          </bk-date-picker>
        </bk-form-item>
        <bk-form-item :label="$t('环境')" class="top-form-item-stage">
          <bk-select
            style="width: 160px;"
            v-model="searchParams.stage_id"
            :clearable="false"
            filterable
            :input-search="false"
            @selected="handleStageSelected">
            <bk-option
              v-for="option in stageList"
              :key="option.id"
              :id="option.id"
              :name="option.name">
            </bk-option>
          </bk-select>
        </bk-form-item>
        <bk-form-item :label="$t('资源')" class="top-form-item-resource">
          <bk-select
            class="top-resource-select"
            :popover-width="180"
            ext-popover-cls="resource-dropdown-content"
            v-model="searchParams.resource_id"
            filterable
            :input-search="false"
            @change="handleResourceChange">
            <bk-option
              v-for="option in resourceList"
              :key="option.id"
              :id="option.id"
              :name="`${option.method} ${option.path}`">
            </bk-option>
          </bk-select>
        </bk-form-item>
        <bk-form-item :label="$t('数据维度')" class="top-form-item-dimension">
          <bk-select
            style="width: 160px;"
            v-model="searchParams.dimension"
            @change="handleDimensionChange">
            <bk-option
              v-for="option in dimensionOptions"
              :key="option.value"
              :id="option.value"
              :name="option.name">
            </bk-option>
          </bk-select>
        </bk-form-item>
        <bk-button
          theme="primary"
          class="ml10 top-refresh-button"
          :disabled="isDataLoading"
          @click="handleRefresh">
          {{ $t('刷新') }}
        </bk-button>
      </bk-form>
    </div>

    <bk-loading
      :loading="isDataLoading"
    >
      <div class="page-content">
        <!-- 按维度分组创建图表容器，切换维度通过控制图表组容器元素进行显示隐藏 -->
        <div class="chart" v-for="(charts, key) in chartConfig" :key="key" v-show="key === dimension && !isDataLoading">
          <div class="chart-container" v-for="(chart, chartIndex) in charts" :key="chartIndex">
            <div class="chart-title">{{`${chart.name}${dimensionName ? ` / ${dimensionName}` : ''}`}}</div>
            <div v-show="!chartEmpty[`${key}_${chart.id}`]" class="chart-wrapper">
              <div class="chart-el" :ref="`${key}_${chart.id}`" :id="`${key}_${chart.id}`"></div>
              <div class="chart-legend" v-if="chartLegend[`${key}_${chart.id}`]">
                <div
                  v-for="({ color, name, selected }, legendIndex) in chartLegend[`${key}_${chart.id}`]"
                  :key="legendIndex"
                  :class="['legend-item', { selected, unselected: selected === false }]"
                  @click.stop="handleClickLegend(`${key}_${chart.id}`, legendIndex)">
                  <div class="legend-icon" :style="{ background: color }"></div>
                  <div class="legend-name">{{name}}</div>
                </div>
              </div>
            </div>
            <div v-show="chartEmpty[`${key}_${chart.id}`] && !isPageLoading" class="ap-nodata">
              <TableEmpty
                :keyword="tableEmptyConf.keyword"
                :abnormal="tableEmptyConf.isAbnormal"
                @reacquire="init"
                @clear-filter="handleClearFilterKey"
              />
            </div>
          </div>
        </div>
      </div>
    </bk-loading>
  </div>
</template>

<script lang="ts" setup>
// @ts-nocheck
import { ref, reactive, computed, onMounted, onBeforeUnmount, nextTick } from 'vue';
import dayjs from 'dayjs';
import { merge } from 'lodash';
import echarts from 'echarts/lib/echarts';
import 'echarts/lib/chart/line';
import 'echarts/lib/component/tooltip';
import 'echarts/lib/component/legend';
import 'echarts/lib/component/toolbox';
import 'echarts/lib/component/dataZoom';
import { useI18n } from 'vue-i18n';
import { useCommon, useAccessLog } from '@/store';
import { Message } from 'bkui-vue';
import { getApigwMetrics, getApigwStages, getApigwResources } from '@/http';
import { userChartIntervalOption } from '@/hooks';
import { getColorHue } from '@/common/util';
import TableEmpty from '@/components/table-empty.vue';
import { Console } from 'console';

const {
  getChartIntervalOption,
} = userChartIntervalOption();

const AccessLogStore = useAccessLog();
const common = useCommon();
const chartInstances: any = {};
const { t } = useI18n();
const isPageLoading = ref<boolean>(true);
const isDataLoading = ref<boolean>(false);
const datePickerRef = ref(null);
const dateKey = ref('dateKey');
const dateTimeRange = ref<Array<any>>([]);
const shortcutSelectedIndex = ref<number>(1);
const tableEmptyConf = ref<{keyword: string, isAbnormal: boolean}>({
  keyword: '',
  isAbnormal: false,
});
let searchParams = reactive<any>({
  stage_id: '',
  resource_id: '',
  time_start: '',
  time_end: '',
  dimension: '',
});
const stageList = ref<any>([]);
const resourceList = ref<any>([]);
const chartData = ref<any>({});
const chartLegend = ref<any>({});
const chartEmpty = ref<any>({});
const dimensionOptions = reactive([
  {
    name: t('资源'),
    value: 'resource',
  },
  {
    name: t('蓝鲸应用ID'),
    value: 'app',
  },
  {
    name: t('资源+非200状态码'),
    value: 'resource_non200_status',
  },
]);
const metricsMap = reactive<any>({
  resource: [
    'requests',
    'failed_requests',
  ],
  app: ['requests'],
  resource_non200_status: ['requests'],
  all: [
    'requests',
    'failed_requests',
    'response_time_95th',
    'response_time_90th',
    'response_time_80th',
    'response_time_50th',
  ],
});

const shortcutsInDay = computed(() => AccessLogStore.shortcutsInDay);
const dimension = computed(() => searchParams.dimension || 'all');
const dimensionName = computed(() => dimensionOptions.find(item => item.value === dimension.value)?.name);
const metricsList = computed(() => metricsMap[dimension.value]);
const chartConfig = computed(() => {
  const titles: any = {
    requests: t('请求数'),
    failed_requests: t('失败请求数'),
    response_time: t('响应时间'),
  };

  const chartConfig: any = {};
  Object.keys(metricsMap).forEach((key) => {
    let config = metricsMap[key];
    if (key === 'all') {
      const groupName = 'response_time';
      config = config.filter((item: any) => !item.startsWith(`${groupName}_`));
      config.push(groupName);
    }
    chartConfig[key] = config.map((item: any) => ({
      id: item,
      name: titles[item],
    }));
  });

  return chartConfig;
});

const init = async () => {
  // 资源列表
  getResources();

  // 业务数据的加载依赖环境参数的初始化
  await getStages();
  getDataByDimension();
};

const chartResize = () => {
  nextTick(() => {
    Object.values(chartInstances).forEach((chart: any) => {
      chart.resize();
    });
  });
  updateTableEmptyConfig();
};

const initChart = () => {
  Object.keys(chartConfig.value).forEach((key) => {
    const configs = chartConfig.value[key];
    configs.forEach((config: any) => {
      const chartId = `${key}_${config.id}`;
      chartInstances[chartId] = echarts.init(document.getElementById(chartId));
    });
  });

  window.addEventListener('resize', chartResize);
};

const getDataByDimension = async () => {
  const { apigwId } = common;
  setSearchTimeRange();
  // 限制在一天内
  if ((searchParams.time_end - searchParams.time_start) > 24 * 60 * 60) {
    Message({
      theme: 'error',
      limit: 1,
      message: t('请重新选择时间范围，最长不超过一天'),
    });
    return false;
  }
  metricsList.value?.map((metrics: any) => {
    const params = {
      ...searchParams,
      dimension: dimension.value,
      metrics,
    };

    return getApigwMetrics(apigwId, params);
  });

  isDataLoading.value = true;
  try {
    // const res = await Promise.all(requests);
    chartData.value = {};
    metricsList.value?.forEach((metrics: any) => {
      // chartData.value[metrics] = res[index];
      chartData.value[metrics] = {
        metrics: [], series: [],
      };
    });

    renderChart();
  } catch (e) {
    console.log(e);
  } finally {
    isPageLoading.value = false;
    isDataLoading.value = false;
  }
};

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

const getChartMoreOption = (chartData: any) => {
  // 1. 根据data的最大值，动态计算出max合适值和interval配置
  const serieData = chartData.map((item: any) => Math.round(item[0])).filter((item: any) => !isNaN(item));
  const maxNumber = Math.max(...serieData);
  const yAxisIntervalOption = getChartIntervalOption(maxNumber, 'number', 'yAxis');

  // 2. 根据时间值计算xAxis显示年/月/日/时间部分
  const xAxisData = chartData.map((item: any) => Math.round(item[1]));
  xAxisData.sort((a: any, b: any) => a - b);
  // timeDuration 需要秒为单位
  const timeDuration = Math.round((xAxisData[xAxisData.length - 1] - xAxisData[0]) / 1000);
  const xAxisIntervalOption = getChartIntervalOption(timeDuration, 'time', 'xAxis');

  return merge(yAxisIntervalOption, xAxisIntervalOption);
};

const generateChartLegend = (_: any, chartInstId: any) => {
  const option = chartInstances[chartInstId]?.getOption();
  // 只有一个系列不需要图例
  if (option.series.length > 1) {
    chartLegend.value[chartInstId] = option?.series?.map((serie: any, index: number) => ({
      color: option.color[index],
      name: serie.name,
      // 0值表示默认状态
      selected: 0,
    }));
  } else {
    chartLegend.value[chartInstId] = null;
  }
};

const generateChartColor = (chartData: any, chartId: string) => {
  let baseColor = ['#3A84FF', '#5AD8A6', '#5D7092', '#F6BD16', '#FF5656', '#6DC8EC'];
  let angle = 30;
  if (chartId?.indexOf('failed_') !== -1) {
    baseColor = ['#FF5656', '#5AD8A6'];
    angle = 10;
  }
  const colors: any = [];
  const interval = Math.ceil(chartData.length / baseColor.length);

  baseColor.forEach((color) => {
    let i = 0;
    while (i < interval) {
      const co = getColorHue(color, i * angle);
      colors.push(co);
      i += 1;
    }
  });

  const finalColors = colors.reduce((a: any, b: any) => a.concat(b), []);
  return finalColors;
};

const formatDatetime = (timeRange: any) => {
  return [
    (+new Date(`${timeRange[0]}`)) / 1000,
    (+new Date(`${timeRange[1]}`)) / 1000,
  ];
};

const setSearchTimeRange = () => {
  let timeRange = dateTimeRange.value;

  // 选择的是时间快捷项，需要实时计算时间值
  if (shortcutSelectedIndex.value !== -1) {
    timeRange = shortcutsInDay.value[shortcutSelectedIndex.value].value();
  }
  const formatTimeRange = formatDatetime(timeRange);
  const [time_start, time_end] = formatTimeRange;
  searchParams.time_start = time_start;
  searchParams.time_end = time_end;
};

const handleClickLegend = (chartInstId: any, index: number) => {
  const chartInstance = chartInstances[chartInstId];
  const legend = chartLegend.value[chartInstId];
  const currentLegend = legend[index];

  const { selected } = currentLegend;

  // 实现切换单选显示
  if (!selected) {
    // 仅显示选中
    chartInstance.dispatchAction({
      type: 'legendUnSelect',
      batch: legend.map(({ name }: any) => ({ name })),
    });
    chartInstance.dispatchAction({
      type: 'legendSelect',
      name: currentLegend.name,
    });

    // 选中状态设置
    legend.forEach((item: any, i: number) => {
      item.selected = index === i;
    });
    chartLegend.value = { ...chartLegend.value, ...{ [chartInstId]: legend } };
  } else {
    // 全部显示
    chartInstance.dispatchAction({
      type: 'legendSelect',
      batch: legend.map(({ name }: any) => ({ name })),
    });

    legend.forEach((item: any) => (item.selected = 0));
    chartLegend.value = { ...chartLegend.value, ...{ [chartInstId]: legend } };
  }
};

const handleDimensionChange = (value: any) => {
  searchParams.dimension = value;
  getDataByDimension();
};

const handleStageSelected = (value: any) => {
  searchParams.stage_id = value;
  getDataByDimension();
};

const handleResourceChange = (value: any) => {
  searchParams.resource_id = value;
  getDataByDimension();
};

const handleTimeChange = () => {
  getDataByDimension();
};

const handleShortcutChange = (value: any, index: number) => {
  shortcutSelectedIndex.value = index;
  updateTableEmptyConfig();
};

const handleRefresh = () => {
  // TODO 待组件更新，根据日历shortcut值计算实时时间查询
  getDataByDimension();
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

const getChartOption = (chartId: any, chartInstId: any) => {
  const baseOption: any = {
    grid: {
      left: 30,
      right: 30,
      top: 30,
      bottom: 30,
      containLabel: true,
    },
    xAxis: {
      type: 'time',
      scale: true,
      boundaryGap: false,
      axisLabel: {
        color: '#A0A4AA',
      },
      axisLine: {
        lineStyle: {
          color: '#e9edf0',
        },
      },
      axisTick: {
        show: false,
        alignWithLabel: true,
        lineStyle: {
          color: '#BDC8D3',
        },
      },
      splitLine: {
        lineStyle: {
          color: '#e9edf0',
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
      data: [],
      type: 'line',
      showSymbol: false,
      connectNulls: true,
      lineStyle: {
        width: 1,
      },
      areaStyle: {
        opacity: 0.2,
      },
    }],
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'line',
        // snap: true,
        lineStyle: {
          color: '#ff5656',
          opacity: 0.7,
        },
      },
      backgroundColor: 'rgba(0, 0, 0, 0.7)',
      textStyle: {
        fontSize: 12,
      },
    },
    legend: {
      show: false,
      left: 30,
      right: 30,
      bottom: 10,
      itemWidth: 10,
      itemHeight: 3,
      icon: 'roundRect',
    },
    toolbox: {
      right: 40,
      feature: {
        dataZoom: {
          yAxisIndex: false,
        },
      },
    },
    animation: false,
  };

  const chartOption: any = {
    yAxis: {},
    series: [],
    tooltip: {},
  };
  let moreOption = {};

  // 不同维度返回的数据结构略有差异，因此分开处理
  if (['resource', 'resource_non200_status', 'app'].includes(dimension.value)) {
    const chartSeriesData = chartData.value[chartId]?.series;
    chartSeriesData.forEach((item: any) => {
      const serieName = dimension.value === 'app' ? `APP=${item?.dimensions?.bk_app_code || '--'}` : `${item?.dimensions?.resource_name}`;
      const values = item.datapoints.filter((value: any) => !isNaN(Math.round(value[0])));
      chartOption.series.push(merge({}, baseOption.series[0], {
        name: serieName,
        data: values.map((value: any) => ([
          // x轴数据，x轴type为time数据需为时间戳
          value[1],
          // 系列数据
          value[0],
        ])),
        // 1个数据点显示小圆点
        showSymbol: values.length === 1,
      }));
    });

    // 设置图表颜色
    chartOption.color = generateChartColor(chartSeriesData, chartId);

    // debug单个数据点
    // chartData.forEach(item => {
    //     if (item.values.length === 1) {
    //         console.log(item.metric.resource || item.metric.app_code, 'item.metric.resource')
    //     }
    // })

    // 设置图表max和interval
    const serieData = chartSeriesData.map((item: any) => item.datapoints).reduce((a: any, b: any) => a.concat(b), []);
    moreOption = getChartMoreOption(serieData);
    chartOption.yAxis.scale = true;

    // 设置图表tooltip内容
    chartOption.tooltip.formatter = (params: any) => {
      const html = [`<p>${dayjs(params[0].data[0]).format('YYYY-MM-DD HH:mm:ss')}</p>`];
      params.forEach((param: any) => {
        html.push(`<p><span>${param.marker}${param.seriesName}: </span><span>${param.data[1] !== null ? param.data[1].toLocaleString() : '0'} ${t('次')}</span></p>`);
      });
      return html.join('');
    };

    // 标记图表是否数据为空
    chartEmpty.value[chartInstId] = !(chartSeriesData || []).length;
  } else if (dimension.value === 'all') {
    if (chartId !== 'response_time') {
      let datapoints = (chartData.value[chartId]?.series[0] || {})?.datapoints || [];
      datapoints = datapoints.filter((value: any) => !isNaN(Math.round(value[0])));
      chartOption.series.push(merge({}, baseOption.series[0], {
        data: datapoints.map((item: any) => ([
          item[1],
          item[0],
        ])),
      }));

      // 设置图表颜色
      chartOption.color = generateChartColor(datapoints, chartId);

      moreOption = getChartMoreOption(datapoints);

      // 设置图表tooltip内容
      chartOption.tooltip.formatter = (params: any) => {
        const html = [`<p>${dayjs(params[0].data[0]).format('YYYY-MM-DD HH:mm:ss')}</p>`];
        params.forEach((param: any) => {
          html.push(`<p>${param.marker}${param.data[1] !== null ? param.data[1].toLocaleString() : '0'} ${t('次')}</p>`);
        });
        return html.join('');
      };

      chartEmpty.value[chartInstId] = !(datapoints || []).length;
    } else {
      const datapoints = [
        (chartData.value?.response_time_95th?.series[0] || {})?.datapoints || [],
        (chartData.value?.response_time_90th?.series[0] || {})?.datapoints || [],
        (chartData.value?.response_time_80th?.series[0] || {})?.datapoints || [],
        (chartData.value?.response_time_50th?.series[0] || {})?.datapoints || [],
      ];
      const serieNames = ['95%', '90%', '80%', '50%'];
      datapoints.forEach((data: any, index: number) => {
        const values = data.filter((value: any) => !isNaN(Math.round(value[0])));
        chartOption.series.push(merge({}, baseOption.series[0], {
          name: serieNames[index],
          data: values.map((item: any) => ([
            item[1],
            item[0],
          ])),
        }));
      });

      chartOption.yAxis.axisLabel = {
        formatter: '{value} ms',
      };

      // 设置图表颜色
      chartOption.color = generateChartColor(datapoints, chartId);

      const serieData = datapoints.reduce((a, b) => a.concat(b), []);
      moreOption = getChartMoreOption(serieData);

      // 设置图表tooltip内容
      chartOption.tooltip.formatter = (params: any) => {
        const html = [`<p>${dayjs(params[0].data[0]).format('YYYY-MM-DD HH:mm:ss')}</p>`];
        params.forEach((param: any) => {
          html.push(`<p><span>${param.marker}${param.seriesName}: </span><span>${param.data[1].toLocaleString()} ms</span></p>`);
        });
        return html.join('');
      };

      chartEmpty.value[chartInstId] = !serieData.length;
    }
  }

  return merge(baseOption, chartOption, moreOption);
};

const handleClearFilterKey = () => {
  [datePickerRef.value.shortcut] = [AccessLogStore.datepickerShortcuts[1]];
  dateTimeRange.value = [];
  shortcutSelectedIndex.value = 1;
  searchParams = Object.assign({}, {
    stage_id: '',
    resource_id: '',
    time_start: '',
    time_end: '',
    dimension: '',
  });
  dateKey.value = String(+new Date());
  setSearchTimeRange();
  init();
};

const updateTableEmptyConfig = () => {
  const time = dateTimeRange.value.some(Boolean);
  const list = Object.values(searchParams).filter(item => item !== '');
  if (time || list.length > 0) {
    tableEmptyConf.value.keyword = 'placeholder';
    return;
  }
  if (searchParams.value.stage_id || time) {
    tableEmptyConf.value.keyword = '$CONSTANT';
    return;
  }
  tableEmptyConf.value.keyword = '';
};

const renderChart = () => {
  chartConfig.value[dimension.value].forEach((config: any) => {
    const chartId = config.id;
    const chartInstId = `${dimension.value}_${chartId}`;
    const option = getChartOption(chartId, chartInstId);
    nextTick(() => {
      chartInstances[chartInstId]?.setOption(option, { notMerge: true });

      // 切换图例，处理单个数据点x轴显示问题
      chartInstances[chartInstId].on('legendselected', (params: any) => {
        const currentOption = chartInstances[chartInstId]?.getOption();
        const serie = currentOption.series.find((item: any) => item.name === params.name) || {};
        if (serie.data && serie.data.length === 1) {
          // fix单个数据点xAxis显示异常，本质上是去掉动态计算出的间隔设置
          chartInstances[chartInstId]?.setOption({
            xAxis: {
              interval: 'auto',
            },
          });
        } else {
          chartInstances[chartInstId]?.setOption(option);
        }
      });
      chartResize();
      generateChartLegend(chartId, chartInstId);
    });
  });
};

init();

onMounted(() => {
  initChart();
});

onBeforeUnmount(() => {
  window.removeEventListener('resize', chartResize);
});
</script>

<style lang="scss" scoped>
.app-content {
  padding-bottom: 24px;
}
.page-content {
  min-height: calc(100vh - 268px);
}

.chart-container {
  width: 100%;
  background: #FFF;
  border: 1px solid #DCDEE5;
  margin-bottom: 12px;

  .chart-wrapper {
    width: 100%;
  }

  .chart-title {
    color: #262625;
    font-size: 16px;
    padding: 20px 0 0 20px;
  }

  .chart-el {
    width: 100%;
    height: 360px;
  }

  .chart-legend {
    display: flex;
    flex-wrap: wrap;
    margin: 0 40px 30px 40px;
    max-height: 110px;
    overflow-y: auto;
    // @mixin scroller;

    .legend-item {
      display: flex;
      align-items: center;
      flex: none;
      font-size: 12px;
      line-height: 22px;
      margin-right: 12px;
      color: #777;
      white-space: nowrap;
      cursor: pointer;

      &:hover,
      &.selected {
        color: #333;
      }

      &.unselected {
        color: #ccc;
      }
    }
    .legend-icon {
      height: 4px;
      background: #999;
      flex: none;
      width: 16px;
      border-radius: 2px;
      margin-right: 3px;
    }
  }

  .ap-nodata {
    :deep(.bk-exception-description) {
      margin-top: 0;
    }
  }
}

.search-form {
  width: 100%;
  :deep(.bk-form-item) {
    display: inline-block;
  }

  .top-resource-select {
    width: 260px;
  }
}

@media (max-width: 1660px) {
  .search-form {
    width: 780px;
    :deep(.bk-form-item) {
      .bk-label {
        width: 72px !important;
      }

      &.top-form-item-resource {
        margin-top: 10px;
        margin-left: 0;
      }
      &.top-form-item-dimension {
        margin-top: 10px;
      }
    }

    .top-resource-select {
      width: 320px;
    }

    .top-refresh-button {
      margin-top: 10px;
    }
  }
}
</style>
