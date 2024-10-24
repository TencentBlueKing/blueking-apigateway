<template>
  <div v-show="!isEmpty" class="line-chart" :id="instanceId"></div>
  <div v-show="isEmpty" class="ap-nodata">
    <TableEmpty
      :keyword="tableEmptyConf.keyword"
      :abnormal="tableEmptyConf.isAbnormal"
      @reacquire="handleInit"
      @clear-filter="handleClearFilterKey"
    />
  </div>
</template>

<script lang="ts" setup>
import { ref, shallowRef, watch, onMounted, onBeforeUnmount, nextTick } from 'vue';
import * as echarts from 'echarts';
import { merge } from 'lodash';
import { userChartIntervalOption } from '@/hooks';
import { SeriesItemType, SearchParamsType } from '../type';
import TableEmpty from '@/components/table-empty.vue';

const props = defineProps({
  instanceId: { // 生成图表的元素id
    type: String,
    default: '',
  },
  chartData: { // 图表数据
    type: Object,
    default: () => {},
  },
  title: { // 图表 title
    type: String,
    default: '响应耗时',
  },
});

const emit = defineEmits(['clear-params', 'report-init']);

const { getChartIntervalOption } = userChartIntervalOption();

const myChart = shallowRef();
const searchParams = ref<SearchParamsType>();
const isEmpty = ref<boolean>(false);
const tableEmptyConf = ref<{keyword: string, isAbnormal: boolean}>({
  keyword: '',
  isAbnormal: false,
});

onMounted(() => {
  const chartDom = document.getElementById(props.instanceId);
  myChart.value = echarts.init(chartDom as HTMLDivElement);

  window.addEventListener('resize', chartResize);
});

onBeforeUnmount(() => {
  window.removeEventListener('resize', chartResize);
});

watch(
  () => props.chartData,
  (data) => {
    if (!data?.series?.length) {
      isEmpty.value = true;
      updateTableEmptyConfig();
    } else {
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
    color: ['#FFB43D', '#4BC7AD', '#FF7756', '#B5E0AB', '#D66F6B', '#3E96C2', '#FFA66B', '#85CCA8', '#FFC685', '#3762B8'],
    title: {
      text: props.title,
      top: 12,
      left: 24,
      textStyle: {
        color: '#313238',
        fontSize: 14,
        fontWeight: 'bold',
        lineHeight: 22,
      },
    },
    grid: {
      right: 140, // 设置距离右侧的间距
    },
    xAxis: {
      type: 'time',
      scale: true, // 设置成 true 后坐标刻度不会强制包含零刻度
      boundaryGap: false,
      axisLabel: { // 坐标轴刻度标签的相关设置
        color: '#666666',
        rotate: 35,
      },
      axisLine: { // 坐标轴轴线相关设置
        lineStyle: {
          color: '#DCDEE5',
        },
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
      type: 'line',
      connectNulls: true, // 是否连接空数据
      symbol: 'circle', // 拐点标记的形状
      symbolSize: 5, // 拐点标记的大小
      itemStyle: { // 折线拐点标志的样式
        normal: {
          borderColor: 'rgba(0,0,0,0)', // 边框颜色透明，去除边框
          borderWidth: 0, // 边框宽度为0
        },
      },
    }],
    legend: { // 图例组件
      show: true,
      type: 'scroll',
      orient: 'vertical', // 垂直排列
      right: 10,
      top: 30,     // 垂直居中
      height: 302,
      pageIconSize: 12, // 翻页按钮的大小
      pageIconColor: '#63656E', // 翻页按钮的颜色
      pageIconInactiveColor: '#C4C6CC', // 翻页按钮不激活时（即翻页到头时）的颜色
      textStyle: {       // 图例文字的样式设置
        fontSize: 12,
        color: '#63656E',
      },
      itemWidth: 16, // 图例标记的图形宽度
      itemHeight: 6, // 图例标记的图形高度
      itemGap: 16, // 设置图例项之间的间隔
      tooltip: {
        show: true,
      },
      formatter: (name: string) => {
        return echarts.format.truncateText(name, 80, '12px Microsoft Yahei', '…');
      },
    },
  };

  const chartOption: echarts.EChartOption = {
    yAxis: {},
    series: [],
    tooltip: {},
    legend: {},
    grid: {},
  };

  let moreOption = {};

  if (props.instanceId !== 'response_time') {
    props.chartData?.series?.forEach((item: SeriesItemType) => {
      let datapoints = item.datapoints || [];
      datapoints = datapoints.filter((value: Array<number>) => !isNaN(Math.round(value[0])));
      chartOption.series.push(merge({}, baseOption.series[0], {
        name: (item.target?.split('=')[1])?.replace(/"/g, ''),
        data: datapoints.map((item) => {
          if (props.instanceId === 'ingress' || props.instanceId === 'egress') {
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
    if (props.instanceId === 'requests') {
      chartOption.legend.show = false;
      chartOption.grid.left = '14%';
      chartOption.grid.right = '8%';
    }

    if (props.instanceId === 'non_200_status') {
      chartOption.grid.left = '14%';
      chartOption.grid.right = 80;
    }

    if (props.instanceId === 'ingress' || props.instanceId === 'egress') {
      chartOption.yAxis.axisLabel = {
        formatter: '{value} KB',
      };
    }

    if (props.instanceId === 'response_time_90th') {
      chartOption.yAxis.axisLabel = {
        formatter: '{value} ms',
      };
    }
  } else {
    const datapoints = [
      (props.chartData?.response_time_90th?.series[0] || {})?.datapoints || [],
      (props.chartData?.response_time_80th?.series[0] || {})?.datapoints || [],
      (props.chartData?.response_time_50th?.series[0] || {})?.datapoints || [],
    ];
    // const seriesNames = ['90%', '80%', '50%'];
    const seriesNames = ['90%'];
    datapoints.forEach((data, index: number) => {
      const values = data.filter((value: Array<number>) => !isNaN(Math.round(value[0])));
      chartOption.series.push(merge({}, baseOption.series[0], {
        name: seriesNames[index],
        data: values.map((item: Array<number>) => ([
          item[1],
          Math.round(item[0]),
        ])),
      }));
    });

    chartOption.yAxis.axisLabel = {
      formatter: '{value} ms',
    };

    chartOption.grid.right = '10%';

    const serieData = datapoints.reduce((a, b) => a.concat(b), []);
    moreOption = getChartMoreOption(serieData);
  }
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

const renderChart = () => {
  nextTick(() => {
    const option = getChartOption();
    myChart.value?.setOption(option, { notMerge: true });
    chartResize();
  });
};

const syncParams = (params: SearchParamsType) => {
  searchParams.value = params;
};

defineExpose({
  syncParams,
});
</script>

<style lang="scss" scoped>
.line-chart {
  width: 100%;
  height: 100%;
}
</style>
