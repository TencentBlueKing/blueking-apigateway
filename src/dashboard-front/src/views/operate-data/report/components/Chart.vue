<template>
  <div class="chart-wrapper">
    <div class="chart-title">
      {{ title || '--' }}
    </div>

    <div v-show="!isEmpty">
      <div
        :id="instanceId"
        class="line-chart"
      />

      <!-- <div
        :class="['chart-legend', 'custom-scroll-bar', { 'side-legend': instanceId === 'non_20x_status' }]"
        v-if="chartLegend[instanceId]">
        <div
        v-for="({ color, name, selected }, legendIndex) in chartLegend[instanceId]"
        :key="legendIndex"
        :class="['legend-item', selected]"
        @click.stop="handleClickLegend(legendIndex)">
        <div class="legend-icon" :style="{ background: color }"></div>
        <div class="legend-name">{{name}}</div>
        </div>
        </div> -->
    </div>

    <div
      v-show="isEmpty"
      class="ap-nodata basic-height"
    >
      <TableEmpty
        :keyword="tableEmptyConf.keyword"
        :abnormal="tableEmptyConf.isAbnormal"
        @reacquire="handleInit"
        @clear-filter="handleClearFilterKey"
      />
    </div>
  </div>
</template>

<script lang="ts" setup>
import * as echarts from 'echarts';
import { merge } from 'lodash';
import dayjs from 'dayjs';
import { useChartIntervalOption } from '@/hooks';
import type {
  ISearchParamsType,
  ISeriesItemType,
} from '@/services/source/report';
import TableEmpty from '@/components/table-empty/Index.vue';
import { getColorHue } from '@/utils';

interface IProps {
  instanceId?: string
  chartData?: object
  title?: string
}

const {
  instanceId = '',
  chartData = {},
  title = '响应耗时',
} = defineProps<IProps>();

const emit = defineEmits<{
  'clear-params': [void]
  'report-init': [void]
}>();

const { t } = useI18n();
const { getChartIntervalOption } = useChartIntervalOption();

const myChart = shallowRef();
// const chartLegend = ref<ChartLegend>({});
const searchParams = ref<ISearchParamsType>();
const isEmpty = ref<boolean>(false);
const tableEmptyConf = ref<{
  keyword: string
  isAbnormal: boolean
}>({
  keyword: '',
  isAbnormal: false,
});

onMounted(() => {
  const chartDom = document.getElementById(instanceId);
  myChart.value = echarts.init(chartDom as HTMLDivElement);

  window.addEventListener('resize', chartResize);
});

onBeforeUnmount(() => {
  window.removeEventListener('resize', chartResize);
});

watch(
  () => chartData,
  (data) => {
    if (!data?.series[0]?.datapoints?.length) {
      isEmpty.value = true;
      updateTableEmptyConfig();
    }
    else {
      isEmpty.value = false;
      renderChart();
    }
  },
  { deep: true },
);

const handleClearFilterKey = () => {
  emit('clear-params');
};

const handleInit = () => {
  emit('report-init');
};

const updateTableEmptyConfig = () => {
  const list = Object.values(searchParams.value).filter(item => !!item);
  if (list.length > 0) {
    tableEmptyConf.value.keyword = 'placeholder';
    return;
  }
  if (searchParams.value.stage_id) {
    tableEmptyConf.value.keyword = '$CONSTANT';
    return;
  }
  tableEmptyConf.value.keyword = '';
};

const chartResize = () => {
  nextTick(() => {
    myChart.value?.resize();
  });
};

const getChartOption = () => {
  const baseOption: echarts.EChartOption = {
    // 设置距离右侧的间距
    grid: { right: '8%' },
    xAxis: {
      type: 'time',
      scale: true, // 设置成 true 后坐标刻度不会强制包含零刻度
      boundaryGap: false,
      axisLabel: { // 坐标轴刻度标签的相关设置
        color: '#666666',
        fontSize: 12,
        padding: [0, 5, 0, 0],
      },
      axisLine: { // 坐标轴轴线相关设置
        lineStyle: { color: '#DCDEE5' },
      },
      axisTick: { // 坐标轴刻度相关设置。
        show: false,
      },
      splitLine: { // 坐标轴在 grid 区域中的分隔线
        show: false,
      },
    },
    yAxis: {
      type: 'value',
      axisLabel: { // 坐标轴刻度标签的相关设置
        color: '#666666',
        fontSize: 12,
        padding: [0, 5, 0, 0],
      },
      splitLine: { // 坐标轴在 grid 区域中的分隔线
        lineStyle: {
          color: '#e9edf0',
          type: 'dashed',
        },
      },
      axisLine: { // 坐标轴轴线相关设置
        show: false,
      },
      axisTick: { // 坐标轴刻度相关设置
        show: false,
      },
    },
    series: [{
      data: [],
      type: 'bar',
    }],
    legend: { show: false },
  };

  const chartOption: echarts.EChartOption = {
    xAxis: {},
    yAxis: {},
    series: [],
    tooltip: {},
    legend: {},
    grid: {},
  };

  let moreOption = {};

  chartData?.series?.forEach((item: ISeriesItemType) => {
    let datapoints = item.datapoints || [];
    datapoints = datapoints.filter((value: Array<number>) => !isNaN(Math.round(value[0])));
    chartOption.series.push(merge({}, baseOption.series[0], {
      name: (item.target?.split('=')[1])?.replace(/"/g, ''),
      data: datapoints.map((item) => {
        if (instanceId === 'ingress' || instanceId === 'egress') {
          return [
            item[1],
            (item[0] / 1024).toFixed(2),
          ];
        }
        return [
          item[1],
          item[0],
        ];
      }),
    }));
    moreOption = getChartMoreOption(datapoints);
  });
  // 设置图表颜色
  chartOption.color = generateChartColor(chartData.series ?? []);

  // tooltip
  chartOption.tooltip.formatter = (params: echarts.EChartOption.Tooltip.Format) => {
    return `<div>
  <p>${dayjs(params.data[0]).format('YYYY-MM-DD')}</p>
  <p><span class="tooltip-icon">${params.marker}${t(title)}: </span><span>${params.data[1] !== null ? params.data[1].toLocaleString() : '0'} ${t('次')}</span></p>
  </div>`;
  };
  return merge(baseOption, chartOption, moreOption);
};

const getChartMoreOption = (seriesData: Array<Array<number>>) => {
  // 1. 根据data的最大值，动态计算出max合适值和interval配置
  // const serieData = seriesData.map((item: Array<number>) => Math.round(item[0]))
  // .filter((item: number) => !isNaN(item));
  // const maxNumber = Math.max(...serieData);
  // const yAxisIntervalOption = getChartIntervalOption(maxNumber, 'number', 'yAxis');

  // 2. 根据时间值计算xAxis显示年/月/日/时间部分
  const xAxisData = seriesData.map((item: Array<number>) => Math.round(item[1]));
  xAxisData.sort((a: number, b: number) => a - b);
  // timeDuration 需要秒为单位
  const timeDuration = Math.round((xAxisData[xAxisData.length - 1] - xAxisData[0]) / 1000);
  const xAxisIntervalOption = getChartIntervalOption(timeDuration, 'time', 'xAxis');

  // return merge(yAxisIntervalOption, xAxisIntervalOption);
  return xAxisIntervalOption;
};

const generateChartColor = (chartData: ISeriesItemType[]) => {
  let baseColor = ['#3A84FF', '#5AD8A6', '#5D7092', '#F6BD16', '#FF5656', '#6DC8EC', '#FFB43D', '#4BC7AD', '#FF7756', '#B5E0AB'];
  let angle = 30;
  if (instanceId.indexOf('failed_') !== -1) {
    baseColor = ['#FF5656', '#5AD8A6'];
    angle = 10;
  }
  const colors: string[] = [];
  const interval = Math.ceil(chartData.length / baseColor.length);

  baseColor.forEach((color) => {
    let i = 0;
    while (i < interval) {
      const co = getColorHue(color, i * angle);
      colors.push(co);
      i += 1;
    }
  });

  const finalColors = colors.reduce((a, b) => a.concat(b), []);
  return finalColors;
};

const renderChart = () => {
  nextTick(() => {
    const option = getChartOption();
    myChart.value?.setOption(option, { notMerge: true });
    chartResize();
    // generateChartLegend();
  });
};

const syncParams = (params: ISearchParamsType) => {
  searchParams.value = params;
};

defineExpose({ syncParams });
</script>

<style lang="scss" scoped>
@use "sass:color";

.chart-wrapper {
  position: relative;
  padding-top: 12px;
  .chart-title {
    margin-left: 24px;
    color: #313238;
    font-size: 14px;
    font-weight: bold;
    line-height: 22px;
  }
  .line-chart {
    height: 360px;
  }
  .chart-legend {
    display: flex;
    flex-wrap: wrap;
    margin: 0 40px;
    height: 70px;
    max-height: 110px;
    overflow-y: auto;

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
  .side-legend {
    position: absolute;
    right: -34px;
    top: 10px;
    flex-direction: column;
    height: 220px;
    max-height: 242px;
  }
  .custom-scroll-bar {
    &::-webkit-scrollbar {
      width: 4px;
      background-color: color.scale(#C4C6CC, $lightness: 80%);
    }

    &::-webkit-scrollbar-thumb {
      height: 5px;
      border-radius: 2px;
      background-color: #c4c6cc;
    }

    &::-webkit-scrollbar-track {
      background: transparent;
    }
  }
}
:deep(.tooltip-icon) {
  margin-right: 6px;
  span {
    height: 4px !important;
    width: 16px !important;
    border-radius: 2px !important;
    vertical-align: middle;
  }
}
.basic-height {
  height: 286px;
}
</style>
