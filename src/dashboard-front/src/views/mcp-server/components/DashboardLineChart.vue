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
import type { IChartLegend, ISeriesItemType } from '@/services/source/observability';
import TableEmpty from '@/components/table-empty/Index.vue';

// 补充图例项类型定义
interface ILegendItem {
  color: string
  name: string
  selected: string
}
// 补充搜索参数类型定义
interface ISearchParamsType { [key: string]: any }

interface IProps {
  instanceId?: string
  title?: string
  chartData?: Record<string, any>
}

interface IEmits {
  'clear-params': [void]
  'report-init': [void]
}

const {
  instanceId = '', // 生成图表的元素id
  title = '响应耗时', // 图表 title
  chartData = {}, // 图表数据
} = defineProps<IProps>();

const emit = defineEmits<IEmits>();

const { getChartIntervalOption } = useChartIntervalOption();
const { searchParams } = useObservabilityDashboard();

const myChart = shallowRef<echarts.ECharts>();
const chartLegend = ref<IChartLegend>({});
const tableEmptyConf = ref<{
  emptyType: string
  isAbnormal: boolean
}>({
  emptyType: '',
  isAbnormal: false,
});

// 判断数据是否为空
const isEmpty = computed(() => {
  const seriesList = Reflect.get(chartData, 'series');
  return !Array.isArray(seriesList) || seriesList?.length == 0;
});

// 更新空状态配置
const updateTableEmptyConfig = () => {
  const list = Object.values(searchParams.value).filter(item => !!item);
  tableEmptyConf.value.emptyType = list.length > 0 ? 'searchEmpty' : 'empty';
};

// 图表自适应
const chartResize = () => {
  nextTick(() => {
    myChart.value?.resize({ animation: { duration: 300 } });
  });
};

// 获取图表核心配置
const getChartOption = () => {
  // 基础配置
  const baseOption: echarts.EChartsOption = {
    grid: {
      left: '36px',
      right: '24px',
    },
    xAxis: {
      type: 'time',
      // 不强制包含零刻度
      // @ts-expect-error scale 属性在 echarts time 轴上有效但类型定义缺失
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
      connectNulls: true, // 连接空数据
      symbol: 'circle', // 拐点形状
      symbolSize: 5, // 拐点大小
      itemStyle: {
        borderColor: 'rgba(0,0,0,0)',
        borderWidth: 0,
      },
      // 隐藏拐点边框
      lineStyle: { width: 1 },
      markPoint: { symbolSize: 12 },
    }],
    legend: { show: false }, // 关闭内置图例，使用自定义图例
    tooltip: { trigger: 'axis' }, // 轴触发tooltip
  };

  const chartOption: echarts.EChartsOption = {
    xAxis: {},
    yAxis: {},
    series: [],
    tooltip: {},
    legend: {},
    grid: {},
  };

  let moreOption: any = {};
  // 需要横向超过两个grid布局
  const multipleList = ['requests', 'requests_2xx', 'non_2xx_status'];
  // 需要转换为毫秒的metrics
  const displayMSList = ['response_time_50th', 'response_time_95th', 'response_time_99th'];
  const seriesData = (chartData as { series: ISeriesItemType[] }).series || [];

  // 处理业务数据，生成系列配置
  seriesData.forEach((item: ISeriesItemType) => {
    // 过滤无效数据：空值、时间戳无效的项
    const dataPoints = (item?.datapoints || (item as any).dataPoints || [])
      .filter((value: Array<number | null>) => !isNaN(Math.round(value[1] as number)) && value[0] !== null);

    // 格式化数据：[时间戳, 数值]，保留2位小数，适配不同instanceId的单位转换
    const formatData = dataPoints.map((point) => {
      const value = Number((point[0] as number).toFixed(2));
      const time = point[1] as number;

      return [time, value];
    });

    // 生成系列项，合并基础配置
    (chartOption.series as any[]).push(merge({}, (baseOption.series as any[])[0], {
      // 优先使用dimensions中的资源名
      name: item.dimensions?.resource_name || (item.target?.split('=')[1])?.replace(/"/g, ''),
      data: formatData,
    }));

    // 计算时间间隔配置
    moreOption = getChartMoreOption(dataPoints as Array<Array<number>>);

    // 动态调整x轴刻度
    if (!displayMSList.includes(instanceId)) {
      const dataLength = dataPoints?.length || 0;
      if (multipleList.includes(instanceId)) {
        moreOption.xAxis.axisLabel = dataLength <= 20
          ? {
            interval: 0,
            rotate: 0,
            fontSize: 12,
          }
          : {
            interval: Math.floor(dataLength / 10),
            rotate: 45,
            margin: 10,
            fontSize: 10,
          };
      }
      else {
        moreOption.xAxis.axisLabel = dataLength <= 30
          ? {
            interval: 0,
            rotate: 0,
            fontSize: 12,
          }
          : {
            interval: Math.floor(dataLength / 10),
            rotate: 25,
            margin: 10,
            fontSize: 10,
          };
      }
    }
  });

  // 设置图表配色
  chartOption.color = generateChartColor(seriesData);

  // 自定义Tooltip（适配业务数据，显示资源名+单位，优化多系列展示）
  setChartTooltip(chartOption, multipleList, displayMSList);

  // 实例ID专属配置
  if (multipleList.includes(instanceId)) {
    if (document.body.clientWidth < 1550) {
      (chartOption.xAxis as any).axisLabel = {
        ...(chartOption.xAxis as any).axisLabel,
        rotate: 35,
      };
    }
  }

  if (displayMSList.includes(instanceId)) {
    (chartOption.yAxis as any).axisLabel = {
      ...(chartOption.yAxis as any).axisLabel,
      formatter: '{value} ms',
    };
  }

  // 合并所有配置
  return merge(baseOption, chartOption, moreOption);
};

// 计算x轴时间间隔配置
const getChartMoreOption = (seriesList: Array<Array<number>>) => {
  const xAxisData = seriesList.map((item: Array<number>) => Math.round(item[1]));
  xAxisData.sort((a: number, b: number) => a - b);
  const timeDuration = Math.round((xAxisData[xAxisData.length - 1] - xAxisData[0]) / 1000);
  return getChartIntervalOption(timeDuration, 'time', 'xAxis');
};

// 生成图表配色
const generateChartColor = (seriesList: ISeriesItemType[]) => {
  let baseColor = ['#3A84FF', '#5AD8A6', '#5D7092', '#F6BD16', '#FF5656', '#6DC8EC', '#FFB43D', '#4BC7AD', '#FF7756', '#B5E0AB'];
  let angle = 30;
  if (instanceId.indexOf('failed_') !== -1) {
    baseColor = ['#FF5656', '#5AD8A6'];
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

// 设置Tooltip格式化（适配业务数据，优化多系列展示）
const setChartTooltip = (
  chartOption: echarts.EChartsOption,
  multipleList: string[],
  displayMSList: string[],
) => {
  // 统一Tooltip格式化逻辑，适配所有instanceId
  // @ts-expect-error echarts tooltip formatter 类型兼容
  chartOption.tooltip.formatter = (params: any) => {
    if (!Array.isArray(params)) params = [params];
    // 时间标题（所有系列共用一个时间）
    let res = `<p>${dayjs(params[0].data[0]).format('YYYY-MM-DD HH:mm:ss')}</p>`;
    // 遍历所有系列，显示颜色标记+资源名+数值+单位
    params.forEach((p: any) => {
      const value = p.data[1] !== null ? p.data[1].toLocaleString() : '0';
      let unit = t('次');
      if (displayMSList.includes(instanceId)) unit = 'ms';
      if (['requests'].includes(instanceId)) {
        p.seriesName = t('总请求数');
      }
      res += `<p>
        <span style="display:inline-block;width:16px;height:4px;border-radius:2px;background:${p.color};margin-right:6px;vertical-align:middle;"></span>
        ${p.seriesName}: <span>${value} ${unit}</span>
      </p>`;
    });
    return res;
  };
};

// 生成自定义图例
const generateChartLegend = () => {
  const option = myChart.value?.getOption();
  if (option && (option.series as any[]).length > 1) {
    chartLegend.value[instanceId] = (option?.series as any[])?.map((ser: any, index: number) => ({
      color: (option.color as string[])[index],
      name: ser.name,
      selected: 'all',
    }));
  }
  else {
    chartLegend.value[instanceId] = null;
  }
};

// 处理图例点击
const handleClickLegend = (index: number) => {
  const legend = chartLegend.value[instanceId];
  if (!legend) return;
  const currentLegend = legend[index];
  const { selected } = currentLegend;

  if (selected !== 'selected') {
    // 仅显示选中项
    myChart.value?.dispatchAction({
      type: 'legendUnSelect',
      batch: legend.map(({ name }: ILegendItem) => ({ name })),
    });
    myChart.value?.dispatchAction({
      type: 'legendSelect',
      name: currentLegend.name,
    });
    // 更新选中状态
    legend.forEach((item: ILegendItem, i: number) => {
      item.selected = index === i ? 'selected' : 'unselected';
    });
  }
  else {
    // 显示所有项
    myChart.value?.dispatchAction({
      type: 'legendSelect',
      batch: legend.map(({ name }: ILegendItem) => ({ name })),
    });
    legend.forEach((item: ILegendItem) => (item.selected = 'all'));
  }

  chartLegend.value = {
    ...chartLegend.value,
    [instanceId]: legend,
  };
};

// 渲染图表主方法
const renderChart = () => {
  if (!myChart.value) return;
  nextTick(() => {
    const option = getChartOption();
    myChart.value.setOption(option, {
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

// 清空筛选参数
const handleClearFilterKey = () => {
  emit('clear-params');
};

// 初始化图表
const handleInit = () => {
  emit('report-init');
};

// 监听数据变化重绘图表
watch(() => chartData, () => {
  if (isEmpty.value) {
    updateTableEmptyConfig();
    return;
  }

  renderChart();
},
{
  deep: true,
  immediate: true,
},
);

onMounted(() => {
  const initChart = () => {
    const chartDom = document.getElementById(instanceId);
    if (!chartDom) return;

    // 检查宽高是否为0
    if (chartDom.clientWidth === 0 || chartDom.clientHeight === 0) {
      // 延时16ms重试（≈60fps），兼容旧浏览器
      setTimeout(() => initChart(), 16);
      return;
    }

    if (myChart.value) {
      myChart.value.dispose();
    }

    myChart.value = echarts.init(chartDom);

    renderChart();
  };

  // 启动初始化（0ms延时，让出主线程）
  setTimeout(() => initChart(), 0);

  window.addEventListener('resize', chartResize);
});

onUnmounted(() => {
  if (myChart.value) {
    myChart.value.dispose();
    myChart.value = null;
  }
  window.removeEventListener('resize', chartResize);
});

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
    color: #4d4f56;
    font-size: 14px;
    font-weight: bold;
    line-height: 22px;
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
      align-items: center;
      flex: none;
      font-size: 12px;
      line-height: 22px;
      margin-right: 16px;
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
      flex: none;
      width: 16px;
      height: 4px;
      background-color: #999;
      border-radius: 2px;
      margin-right: 4px;
    }
  }

  .side-legend {
    position: absolute;
    right: -34px;
    top: 10px;
    flex-direction: column;
    max-height: 242px;
    padding: 8px 0;
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

.basic-height {
  height: 286px;
  display: flex;
  align-items: center;
  justify-content: center;
}
</style>
