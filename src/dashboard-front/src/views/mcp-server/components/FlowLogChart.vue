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
  <div class="flow-log-request">
    <BkLoading :loading="chartLoading">
      <div class="chart">
        <div class="chart-box">
          <div
            v-show="isDisplayChart && !chartLoading"
            ref="chartBoxRef"
            class="chart-el"
          />
          <TableEmpty
            v-show="!isDisplayChart && !chartLoading"
            :empty-type="chartEmptyConf.emptyType"
            :abnormal="chartEmptyConf.isAbnormal"
            @refresh="handleRefresh"
            @clear-filter="handleClearFilter"
          />
        </div>
      </div>
    </BkLoading>
  </div>
</template>

<script lang="ts" setup>
import dayjs from 'dayjs';
import * as echarts from 'echarts';
import 'echarts/lib/chart/bar';
import 'echarts/lib/component/tooltip';
import 'echarts/lib/component/toolbox';
import 'echarts/lib/component/dataZoom';
import { debounce, merge } from 'lodash-es';
import { t } from '@/locales';
import { useChartIntervalOption } from '@/hooks';
import TableEmpty from '@/components/table-empty/Index.vue';

interface IEmits {
  'clear-filter': [void]
  'refresh-request': [void]
  'update-date': { dateValue: string[] }
};

// 空数据配置
const chartEmptyConf = defineModel('chartEmptyConf', {
  type: Object,
  default: () => ({
    emptyType: '',
    isAbnormal: false,
  }),
});

// 图表加载状态
const chartLoading = defineModel('chartLoading', {
  type: Boolean,
  default: false,
});

const emit = defineEmits<IEmits>();

const { getChartIntervalOption } = useChartIntervalOption();

const chartBoxRef = ref<HTMLDivElement>(null);
// ECharts 实例
const chartInstance = ref<echarts.ECharts | null>(null);
// 图表数据（series + timeline）
const chartData = ref<{
  series: number[]
  timeline: number[]
}>({
  series: [],
  timeline: [],
});

// 防重复初始化 & 异步锁
let isChartInit = false;
let isRendering = false;

// 是否展示chart
const isDisplayChart = computed(() => {
  return Array.isArray(chartData.value.series)
    && Array.isArray(chartData.value.timeline)
    && chartData.value.series.length > 0
    && chartData.value.timeline.length > 0;
});

const handleSetChartDispatchAction = () => {
  chartInstance.value?.dispatchAction({
    type: 'takeGlobalCursor',
    key: 'dataZoomSelect',
    dataZoomSelectActive: true,
  });
};

// echart监听尺寸方法
const handleChartResize = debounce(() => {
  if (!chartInstance.value || !chartBoxRef.value) return;
  const { offsetWidth, offsetHeight } = chartBoxRef.value;
  if (offsetWidth && offsetHeight) {
    chartInstance.value.resize({
      width: offsetWidth,
      height: offsetHeight,
    });
  }
}, 200);

// echart监听区域拖拽
const handleDataZoom = debounce((e: echarts.EChartEvent) => {
  const { start, end } = e ?? {};

  // 无值直接返回
  if (start === undefined || end === undefined) return;

  const xAxisOption = chartInstance.value?.getOption().xAxis?.[0];
  if (!xAxisOption || !xAxisOption.data) return;

  const xData = xAxisOption.data;
  const len = xData.length;

  // 百分比 → 数组索引
  const startIndex = Math.floor((start / 100) * len);
  const endIndex = Math.ceil((end / 100) * len);

  // 防止越界
  const startIdx = Math.max(0, Math.min(len - 1, startIndex));
  const endIdx = Math.max(0, Math.min(len - 1, endIndex));

  // 截取选中区间的时间
  const zoomedData = xData.slice(startIdx, endIdx + 1);
  const startTime = zoomedData[0];
  const endTime = zoomedData[zoomedData.length - 1];

  const dateValue: string[] = [];

  if (startTime && endTime && startTime !== endTime) {
    dateValue.push(startTime, endTime);
  }

  emit('update-date', { dateValue });
}, 1000);

// 渲染chart配置参数
const renderChart = async (data: {
  series?: number[]
  timeline?: number[]
} = {}) => {
  const { series = [], timeline = [] } = data;

  chartData.value = {
    series,
    timeline,
  };

  // 空数据直接显示空状态，不渲染图表
  if (series.length === 0 || timeline.length === 0) {
    chartEmptyConf.value = {
      emptyType: 'empty',
      isAbnormal: false,
    };
    chartInstance.value?.setOption({
      series: [],
      xAxis: { data: [] },
    }, true);
    return;
  }

  // 实例不存在 → 先初始化
  if (!chartInstance.value) {
    await initChart();
    // 初始化完成后重新渲染
    if (chartInstance.value) {
      renderChart(data);
    }
    return;
  }

  // 防止重复渲染
  if (isRendering) return;
  isRendering = true;

  try {
    const xAxisData = timeline.map(time => dayjs.unix(time).format('YYYY-MM-DD HH:mm:ss'));

    const baseOption = {
      grid: {
        left: 20,
        right: 20,
        top: 16,
        bottom: 40,
        containLabel: true,
      },
      // 暂时先注释掉dataZoom配置
      // dataZoom: [
      //   {
      //     type: 'slider',
      //     xAxisIndex: 0,
      //     start: 0,
      //     end: 100,
      //     height: 20,
      //     bottom: 10,
      //     left: '160px',
      //     right: '160px',
      //     backgroundColor: '#f5f7fa',
      //     borderColor: '#e9edf0',
      //     handleSize: 12,
      //     handleStyle: {
      //       color: '#5b8ff9',
      //       borderColor: '#5b8ff9',
      //     },
      //     textStyle: {
      //       color: '#a0a4aa',
      //       fontSize: 12,
      //     },
      //     show: true,
      //     showDetail: true,
      //     realtime: true,
      //   },
      //   {
      //     type: 'inside',
      //     xAxisIndex: 0,
      //     start: 0,
      //     end: 100,
      //     realtime: true,
      //   },
      // ],
      xAxis: {
        type: 'category',
        boundaryGap: true,
        splitNumber: 8,
        data: xAxisData,
        axisLabel: { color: '#a0a4aa' },
        axisLine: { lineStyle: { color: '#e9edf0' } },
        axisTick: {
          alignWithLabel: true,
          lineStyle: { color: '#bdc8d3' },
        },
      },
      yAxis: {
        type: 'value',
        axisLabel: { color: '#a0a4aa' },
        splitLine: { lineStyle: { color: '#e9edf0' } },
        axisLine: { show: false },
        axisTick: { show: false },
      },
      series: [
        {
          type: 'bar',
          data: series ?? [],
          barMinHeight: 1,
          barMaxWidth: 12,
          itemStyle: { color: '#5b8ff9' },
          emphasis: {
            itemStyle: {
              color: '#5b8ff9',
              shadowBlur: 10,
              shadowColor: 'rgba(0, 0, 0, 0.2)',
            },
          },
          markArea: null,
        },
      ],
      tooltip: {
        trigger: 'item',
        backgroundColor: '#ffffff',
        borderRadius: 8,
        borderWidth: 0,
        confine: true,
        textStyle: {
          fontSize: 12,
          color: '#4d4f56',
          lineHeight: 20,
        },
        padding: [8, 8],
        extraCssText: 'box-shadow: 0 0 10px 0 #31323826;',
        formatter: (params: echarts.DefaultLabelFormatterParams) => {
          try {
            const { name = '', value = 0, color } = params ?? {};
            const num = Number(value);
            const count = isNaN(num) ? String(value) : num.toLocaleString();

            return `
              <div>
                <div style="margin-bottom: 8px;">${name}</div>
                <div style="display: flex; align-items: center;">
                  <div style="display: flex; align-items: center; gap: 6px;">
                    <div style="width: 12px; height: 12px; background-color: ${color}; border-radius: 2px; flex-shrink: 0;"></div>
                    <div>${t('请求数')}</div>
                  </div>
                  <span style="font-weight: 700; margin-left: auto;">${count}</span>
                </div>
              </div>
            `;
          }
          catch {
            return '';
          }
        },
      },
      toolbox: { show: false },
    };

    // 间隔配置
    const timeDuration = timeline.at(-1)! - timeline[0]!;
    const intervalOption = getChartIntervalOption(timeDuration, 'time', 'xAxis');

    const finalOption = merge({}, baseOption, intervalOption);

    // 设置图表配置
    chartInstance.value.setOption(finalOption, true);

    handleChartResize();

    chartEmptyConf.value = {
      emptyType: 'searchEmpty',
      isAbnormal: false,
    };
  }
  catch {
    chartEmptyConf.value = {
      emptyType: 'error',
      isAbnormal: true,
    };
  }
  finally {
    isRendering = false;
  }
};

// 初始化chart渲染
const initChart = async () => {
  // 避免重复初始化
  if (isChartInit || chartInstance.value) return;

  const chartBox = chartBoxRef.value;
  if (!chartBox) return;

  // 强制设置DOM尺寸（防止尺寸为0）
  chartBox.style.width = '100%';
  chartBox.style.height = '160px';

  // 宽高为 0 则重试
  const { offsetWidth, offsetHeight } = chartBox;
  if ([offsetWidth, offsetHeight].includes(0)) {
    if (typeof requestIdleCallback === 'function') {
      requestIdleCallback(initChart, { timeout: 3000 });
    }
    else {
      setTimeout(initChart, 0);
    }
    return;
  }

  try {
    isChartInit = true;

    chartInstance.value = markRaw(
      echarts.init(chartBox, null, {
        width: offsetWidth,
        height: offsetHeight,
      }),
    );

    chartInstance.value.on('datazoom', handleDataZoom);

    window.addEventListener('resize', handleChartResize);

    if (chartData.value.series.length > 0) {
      renderChart(chartData.value);
    }

    // 初始化后立即触发一次resize
    handleChartResize();
  }
  catch {
    isChartInit = false;
    chartEmptyConf.value = {
      emptyType: 'error',
      isAbnormal: true,
    };
  }
};

const setChartData = (data) => {
  renderChart(data);
};

const handleClearFilter = () => {
  emit('clear-filter');
};

const handleRefresh = () => {
  emit('refresh-request');
};

onMounted(() => {
  initChart();
});

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleChartResize);
  chartInstance.value?.off('datazoom', handleDataZoom);
  chartInstance.value?.dispose();
  chartInstance.value = null;
  isChartInit = false;
});

defineExpose({
  setChartData,
  renderChart,
  handleSetChartDispatchAction,
  chartInstance,
});
</script>

<style lang="scss" scoped>
.flow-log-request {
  width: 100%;
  box-sizing: border-box;

  .chart-box {
    width: 100%;
    height: 160px;
    background: #ffffff;
    position: relative;

    .chart-el {
      width: 100%;
      height: 100%;
      min-height: 100px;
    }
  }
}
</style>
