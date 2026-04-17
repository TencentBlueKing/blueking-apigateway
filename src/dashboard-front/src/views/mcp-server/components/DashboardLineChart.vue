/*
 * TencentBlueKing is pleased to support the open source community by making
 * 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
 * Copyright (C) 2026 Tencent. All rights reserved.
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
  <div class="chart-wrapper">
    <div class="chart-title">
      {{ title || '--' }}
    </div>
    <div v-show="!isEmpty">
      <div
        v-if="chartLegend[instanceId]"
        class="chart-legend custom-scroll-bar"
        :class="[{ 'side-legend': ['non_2xx_status'].includes(instanceId) }]"
      >
        <div
          v-for="({ color, name, selected }, legendIndex) in chartLegend[instanceId]"
          :key="legendIndex"
          class="mt-8px legend-item"
          :class="[selected]"
          @click.stop="() => handleClickLegend(legendIndex)"
        >
          <div
            class="legend-icon"
            :style="{ backgroundColor: color }"
          />
          <div class="legend-name">
            {{ name }}
          </div>
        </div>
      </div>
      <div
        :id="instanceId"
        class="line-chart"
        :class="[['requests', 'requests_2xx', 'non_2xx_status'].includes(instanceId) ? 'mini' : 'middle']"
      />
    </div>
    <div
      v-show="isEmpty"
      class="basic-height"
    >
      <TableEmpty
        :empty-type="tableEmptyConf.emptyType"
        :abnormal="tableEmptyConf.isAbnormal"
        @refresh="handleInit"
        @clear-filter="handleClearFilterKey"
      />
    </div>
  </div>
</template>

<script lang="ts" setup>
import dayjs from 'dayjs';
import * as echarts from 'echarts';
import { merge } from 'lodash-es';
import { t } from '@/locales';
import { getColorHue } from '@/utils';
import { useChartIntervalOption, useObservabilityDashboard } from '@/hooks';
import type { ILegendItem, ISearchParamsType, ISeriesItemType } from '@/services/source/observability';
import TableEmpty from '@/components/table-empty/Index.vue';

interface IProps {
  instanceId?: string
  title?: string
  chartData?: {
    series?: ISeriesItemType[]
  }
}

interface IEmits {
  'clear-params': []
  'report-init': []
}

// 组件配置
const {
  instanceId = '',
  title = '响应耗时',
  chartData = {},
} = defineProps<IProps>();
const emit = defineEmits<IEmits>();

// 常量配置
const multipleList = ['requests', 'requests_2xx', 'non_2xx_status'] as const;
const displayMSList = ['response_time_50th', 'response_time_95th', 'response_time_99th'] as const;
const displayBytesList = ['request_body_size', 'response_body_size'] as const;

// 组合式API
const { getChartIntervalOption } = useChartIntervalOption();
const { searchParams } = useObservabilityDashboard();

const myChart = shallowRef<echarts.ECharts | undefined>();
const chartLegend = ref<Record<string, ILegendItem[] | null>>({});
const tableEmptyConf = ref<{
  emptyType: 'empty' | 'search-empty' | 'searchEmpty' | 'error' | undefined
  isAbnormal: boolean
}>({
  emptyType: undefined,
  isAbnormal: false,
});

// 计算属性
const isEmpty = computed(() => {
  const seriesList = chartData.series;
  return !Array.isArray(seriesList) || seriesList.length === 0;
});

// 更新空状态置
const updateTableEmptyConfig = () => {
  const hasFilter = Object.values(searchParams.value).some(item => !!item);
  tableEmptyConf.value.emptyType = hasFilter ? 'searchEmpty' : 'empty';
};

// 图表自适应
const chartResize = () => {
  nextTick(() => {
    myChart.value?.resize({ animation: { duration: 300 } });
  });
};

// 计算x轴时间间隔配置
const getChartMoreOption = (seriesList: IDataPoint[]) => {
  const xAxisData = seriesList.map(item => Math.round(item[1]));
  xAxisData.sort((a, b) => a - b);

  if (xAxisData.length < 2) return { xAxis: {} };

  const timeDuration = Math.round((xAxisData[xAxisData.length - 1] - xAxisData[0]) / 1000);
  return getChartIntervalOption(timeDuration, 'time', 'xAxis');
};

// 生成图表配色
const generateChartColor = (seriesList: ISeriesItemType[]): string[] => {
  let baseColor = ['#3a84ff', '#5ad8a6', '#5d7092', '#f6bd16', '#ff5656', '#6dc8ec', '#ffb43d', '#4bc7ad', '#ff7756', '#b5e0ab'];
  let angle = 30;

  if (instanceId.includes('failed_')) {
    baseColor = ['#ff5656', '#5ad8a6'];
    angle = 10;
  }

  const colors: string[] = [];
  const interval = Math.ceil(seriesList.length / baseColor.length);

  baseColor.forEach((color) => {
    let i = 0;
    while (i < interval) {
      const co = getColorHue(color, i * angle);
      colors.push(co);
      i += 1;
    }
  });

  return colors;
};

// 设置Tooltip格式化
const setChartTooltip = (
  chartOption: echarts.EChartsOption,
  multipleList: readonly string[],
  displayMSList: readonly string[],
  displayBytesList: readonly string[],
) => {
  type TooltipParam = {
    data: [number, number]
    seriesName: string
    color: string
  };

  chartOption.tooltip = {
    trigger: 'axis',
    formatter: (params: TooltipParam | TooltipParam[]) => {
      const paramList = Array.isArray(params) ? params : [params];
      if (paramList.length === 0) return '';

      let res = `<p>${dayjs(paramList[0].data[0]).format('YYYY-MM-DD HH:mm:ss')}</p>`;

      paramList.forEach((p) => {
        const value = p.data[1]?.toLocaleString() || '0';
        let unit = t('次');

        if (displayMSList.includes(instanceId)) unit = 'ms';
        if (displayBytesList.includes(instanceId)) unit = 'bytes';
        if (instanceId === 'requests') p.seriesName = t('总请求数');

        res += `<p>
          <span style="display:inline-block;width:16px;height:4px;border-radius:2px;background:${p.color};margin-right:6px;vertical-align:middle;"></span>
          ${p.seriesName}: <span>${value} ${unit}</span>
        </p>`;
      });

      return res;
    },
  };
};

// 获取图表核心配置
const getChartOption = (): echarts.EChartsOption => {
  // 基础配置
  const baseOption: echarts.EChartsOption = {
    grid: {
      top: '15%',
      left: '2%',
      right: '1%',
      bottom: '12%',
      containLabel: true,
    },
    xAxis: {
      type: 'time',
      scale: true,
      boundaryGap: false,
      axisLabel: {
        color: '#666666',
        fontSize: 12,
        padding: [0, 5, 0, 0],
      },
      axisLine: { lineStyle: { color: '#dcdee5' } },
      axisTick: { show: false },
      splitLine: { show: false },
    },
    yAxis: {
      type: 'value',
      axisLabel: {
        color: '#666666',
        fontSize: 12,
        padding: [0, 5, 0, 0],
      },
      splitLine: {
        lineStyle: {
          color: '#e9edf0',
          type: 'dashed',
        },
      },
      axisLine: { show: false },
      axisTick: { show: false },
    },
    series: [{
      data: [],
      type: 'line',
      connectNulls: true,
      symbol: 'circle',
      symbolSize: 5,
      itemStyle: {
        borderColor: 'rgba(0,0,0,0)',
        borderWidth: 0,
      },
      lineStyle: { width: 1 },
      markPoint: { symbolSize: 12 },
    }],
    legend: { show: false },
    tooltip: { trigger: 'axis' },
  };

  const chartOption: echarts.EChartsOption = {
    xAxis: {},
    yAxis: {},
    series: [],
    tooltip: {},
    legend: {},
    grid: {},
  };

  const seriesData = chartData.series || [];

  // 处理业务数据
  seriesData.forEach((item) => {
    const IDataPoints = (item.IDataPoints || [])
      .filter((value): value is IDataPoint =>
        !isNaN(Math.round(value[1])) && value[0] !== null,
      );

    const formatData = IDataPoints.map(point => [
      point[1],
      Number((point[0] as number).toFixed(2)),
    ] as [number, number]);

    const baseSeries = (baseOption.series as echarts.LineSeries[])[0];
    (chartOption.series as echarts.LineSeries[]).push(merge({}, baseSeries, {
      name: item.dimensions?.resource_name || item.target?.split('=')[1]?.replace(/"/g, ''),
      data: formatData,
    }));

    const moreOption = getChartMoreOption(IDataPoints);
    const dataLength = IDataPoints.length;

    // 动态调整x轴刻度
    if (!displayMSList.includes(instanceId) && moreOption.xAxis) {
      if (multipleList.includes(instanceId)) {
        (moreOption.xAxis as echarts.XAXisOption).axisLabel = dataLength <= 20
          ? { interval: 0,
            rotate: 0,
            fontSize: 12 }
          : { interval: Math.floor(dataLength / 10),
            rotate: 45,
            margin: 10,
            fontSize: 10 };
      }
      else {
        (moreOption.xAxis as echarts.XAXisOption).axisLabel = dataLength <= 30
          ? { interval: 0,
            rotate: 0,
            fontSize: 12 }
          : { interval: Math.floor(dataLength / 10),
            rotate: 25,
            margin: 10,
            fontSize: 10 };
      }
    }

    merge(chartOption, moreOption);
  });

  // 设置颜色
  chartOption.color = generateChartColor(seriesData);

  // 设置Tooltip
  setChartTooltip(chartOption, multipleList, displayMSList, displayBytesList);

  // 响应式处理
  if (multipleList.includes(instanceId) && document.body.clientWidth < 1550) {
    (chartOption.xAxis as echarts.XAXisOption).axisLabel = {
      ...(chartOption.xAxis as echarts.XAXisOption).axisLabel,
      rotate: 35,
    };
  }

  // 单位配置
  if (displayMSList.includes(instanceId)) {
    (chartOption.yAxis as echarts.YAXisOption).axisLabel = {
      ...(chartOption.yAxis as echarts.YAXisOption).axisLabel,
      formatter: '{value} ms',
    };
  }

  if (displayBytesList.includes(instanceId)) {
    (chartOption.yAxis as echarts.YAXisOption).axisLabel = {
      ...(chartOption.yAxis as echarts.YAXisOption).axisLabel,
      formatter: '{value} bytes',
    };
  }

  return merge(baseOption, chartOption);
};

// 生成自定义图例
const generateChartLegend = () => {
  const option = myChart.value?.getOption();
  if (!option || !option.series || option.series.length <= 1) {
    chartLegend.value[instanceId] = null;
    return;
  }

  const seriesList = option.series as echarts.LineSeries[];
  const colors = option.color as string[] || [];

  chartLegend.value[instanceId] = seriesList.map((ser, index) => ({
    color: colors[index] || '#999',
    name: ser.name || '',
    selected: 'all' as const,
  }));
};

// 处理图例点击
const handleClickLegend = (index: number) => {
  const legend = chartLegend.value[instanceId];
  if (!legend) return;

  const currentLegend = legend[index];
  if (currentLegend.selected !== 'selected') {
    myChart.value?.dispatchAction({ type: 'legendUnSelect',
      batch: legend.map(({ name }) => ({ name })) });
    myChart.value?.dispatchAction({ type: 'legendSelect',
      name: currentLegend.name });

    legend.forEach((item, i) => {
      item.selected = index === i ? 'selected' : 'unselected';
    });
  }
  else {
    myChart.value?.dispatchAction({ type: 'legendSelect',
      batch: legend.map(({ name }) => ({ name })) });
    legend.forEach(item => item.selected = 'all');
  }

  chartLegend.value = { ...chartLegend.value };
};

// 渲染图表
const renderChart = () => {
  if (!myChart.value) return;

  nextTick(() => {
    const option = getChartOption();
    myChart.value!.setOption(option, {
      notMerge: true,
      animation: { duration: 300 },
    });
    chartResize();
    generateChartLegend();
  });
};

// 同步搜索参数
const syncParams = (params: ISearchParamsType) => {
  searchParams.value = params;
};

// 清空筛选
const handleClearFilterKey = () => {
  emit('clear-params');
};

// 初始化
const handleInit = () => {
  emit('report-init');
};

// 监听数据变化
watch(() => chartData, () => {
  if (isEmpty.value) {
    updateTableEmptyConfig();
    return;
  }
  renderChart();
}, { deep: true,
  immediate: true });

// 生命周期
onMounted(() => {
  const initChart = () => {
    const chartDom = document.getElementById(instanceId);
    if (!chartDom) return;

    if (chartDom.clientWidth === 0 || chartDom.clientHeight === 0) {
      setTimeout(initChart, 16);
      return;
    }

    myChart.value?.dispose();
    myChart.value = echarts.init(chartDom);
    renderChart();
  };

  setTimeout(initChart, 0);
  window.addEventListener('resize', chartResize);
});

onUnmounted(() => {
  myChart.value?.dispose();
  myChart.value = undefined;
  window.removeEventListener('resize', chartResize);
});

// 暴露方法
defineExpose({
  syncParams,
  renderChart,
});
</script>

<style lang="scss" scoped>
@use "sass:color";

.chart-wrapper {
  position: relative;
  width: 100%;
  padding: 0 24px;
  box-sizing: border-box;

  .chart-title {
    padding-top: 12px;
    font-size: 14px;
    font-weight: bold;
    line-height: 22px;
    color: #4d4f56;
  }

  .line-chart {
    width: 100%;
    height: 286px;
  }

  .chart-legend {
    display: flex;
    justify-content: flex-end;
    flex-wrap: wrap;
    overflow-y: auto;

    .legend-item {
      display: flex;
      margin-right: 16px;
      font-size: 12px;
      line-height: 22px;
      white-space: nowrap;
      cursor: pointer;
      align-items: center;
      flex: none;

      &:hover,
      &.selected {
        color: #333;
      }

      &.unselected {
        color: #ccc;
      }
    }

    .legend-icon {
      width: 16px;
      height: 4px;
      margin-right: 4px;
      background-color: #999;
      border-radius: 2px;
      flex: none;
    }
  }

  .side-legend {
    position: absolute;
    top: 10px;
    right: -34px;
    max-height: 242px;
    padding: 8px 0;
    flex-direction: column;
  }

  .custom-scroll-bar {
    &::-webkit-scrollbar {
      width: 4px;
      background-color: color.scale(#C4C6CC, $lightness: 80%);
    }

    &::-webkit-scrollbar-thumb {
      height: 5px;
      background-color: #c4c6cc;
      border-radius: 2px;
    }

    &::-webkit-scrollbar-track {
      background-color: transparent;
    }
  }
}

.basic-height {
  display: flex;
  height: 286px;
  align-items: center;
  justify-content: center;
}
</style>
