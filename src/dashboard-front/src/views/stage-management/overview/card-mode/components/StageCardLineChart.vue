/*
 * TencentBlueKing is pleased to support the open source community by making
 * 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
 * Copyright (C) Tencent. All rights reserved.
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
    <!-- 无数据或全为 0 时，用 CSS 基线占位 -->
    <div
      v-if="isEmpty"
      class="empty-chart"
      :class="{ 'is-zero': tone === 'zero' }"
      aria-hidden="true"
    />
    <div
      v-else
      :id="mountId"
      class="line-chart"
    />
  </div>
</template>

<script lang="ts" setup>
import * as echarts from 'echarts';

interface IProp {
  mountId: string
  data?: number[]
  tone?: 'unreleased' | 'zero'
}

const {
  data = [],
  mountId,
  tone = 'zero',
} = defineProps<IProp>();

// 无数据或数据全为 0 时视为空态
const isEmpty = computed(() => !data.length || data.every(value => !value));

let chartInstance: echarts.ECharts | null = null;
const option = {
  xAxis: {
    type: 'category',
    data: [
      '1',
      '2',
      '3',
      '4',
      '5',
      '6',
    ],
    boundaryGap: false,
    axisTick: { // 坐标轴刻度相关设置。
      show: false,
    },
    splitLine: { show: false },
  },
  yAxis: {
    type: 'value',
    boundaryGap: false,
    min: 'dataMin',
    max: 'dataMax',
    splitLine: { show: false },
    axisLabel: { show: false },
    axisLine: { // 坐标轴轴线相关设置
      show: false,
    },
    axisTick: { // 坐标轴刻度相关设置
      show: false,
    },
  },
  series: [
    {
      // data: [
      //   150,
      //   230,
      //   224,
      //   218,
      //   135,
      //   147,
      // ],
      data: [],
      type: 'line',
      symbol: 'none',
      smooth: true,
      lineStyle: {
        color: '#6fd2bd',
        width: 1,
      },
      areaStyle: {
        color: {
          type: 'linear',
          x: 0,
          y: 0,
          x2: 0,
          y2: 1,
          colorStops: [
            {
              offset: 0,
              color: '#4bc7ad52', // 0% 处的颜色
            },
            {
              offset: 1,
              color: '#4bc7ad00', // 100% 处的颜色
            },
          ],
          global: false, // 缺省为 false
        },
      },
    },
  ],
  grid: {
    left: 0,
    right: 0,
    top: 1,
    bottom: 0,
  },
};

watch(
  () => data,
  () => {
    if (isEmpty.value) {
      disposeChart();
      return;
    }
    (option.series![0] as any).data = data;
    renderChart();
  },
  { deep: true },
);

const renderChart = () => {
  nextTick(() => {
    const chartDom = document.getElementById(mountId);
    if (!chartDom) {
      return;
    }
    if (!chartInstance) {
      chartInstance = echarts.init(chartDom as HTMLDivElement);
    }
    chartInstance.setOption(option);
  });
};

const disposeChart = () => {
  chartInstance?.dispose();
  chartInstance = null;
};

// 卡片列数会随窗口宽度变化，需同步重算图表尺寸
const handleResize = () => {
  chartInstance?.resize();
};

onMounted(() => {
  window.addEventListener('resize', handleResize);
  if (isEmpty.value) {
    return;
  }
  (option.series![0] as any).data = data;
  renderChart();
});

onUnmounted(() => {
  window.removeEventListener('resize', handleResize);
  disposeChart();
});

</script>

<style lang="scss" scoped>
.chart-wrapper {
  width: 100%;
  height: 60px;

  .line-chart {
    width: 100%;
    height: 60px;
  }
}

.empty-chart {
  position: relative;
  width: 100%;
  height: 100%;

  &::before {
    position: absolute;
    right: 0;
    bottom: 0;
    left: 0;
    height: 36%;
    pointer-events: none;
    background: linear-gradient(180deg, rgb(220 222 229 / 45%) 0%, rgb(220 222 229 / 0%) 100%);
    border-top: 1px solid #dcdee5;
    content: '';
  }

  &.is-zero {

    &::before {
      background: linear-gradient(180deg, rgb(75 199 173 / 32%) 0%, rgb(75 199 173 / 0%) 100%);
      border-top: 1px solid #6fd2bd;
    }
  }
}
</style>
