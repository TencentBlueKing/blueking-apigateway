/*
 * TencentBlueKing is pleased to support the open source community by making
 * 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
 * Copyright (C) 2025 Tencent. All rights reserved.
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
    <div
      :id="mountId"
      class="line-chart"
    />
  </div>
</template>

<script lang="ts" setup>
import {
  nextTick,
  onMounted,
  onUnmounted,
  watch,
} from 'vue';
import * as echarts from 'echarts';

interface IProp {
  mountId: string
  data?: number[]
}

const {
  data = [],
  mountId,
} = defineProps<IProp>();

let chartInstance: echarts.ECharts | null = null;
const option: echarts.EChartOption = {
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
    option.series![0].data = data;
    renderChart();
  },
  { deep: true },
);

const renderChart = () => {
  nextTick(() => {
    chartInstance?.setOption(option);
  });
};

onMounted(() => {
  const chartDom = document.getElementById(mountId);
  chartInstance = echarts.init(chartDom as HTMLDivElement);
  renderChart();
});

onUnmounted(() => {
  chartInstance?.dispose();
  chartInstance = null;
});

</script>

<style lang="scss" scoped>

.chart-wrapper {
  width: 390px;
  height: 60px;

  .line-chart {
    width: 390px;
    height: 60px;
  }
}

</style>
