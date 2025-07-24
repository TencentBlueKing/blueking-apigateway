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
  <BkLoading :loading="isChartDataLoading">
    <div
      id="chart-status"
      style="width: 100%; height: 350px;"
    />
  </BkLoading>
</template>

<script lang="ts" setup>
import echarts from 'echarts/lib/echarts';
import 'echarts/lib/chart/line';
import 'echarts/lib/component/tooltip';
import 'echarts/lib/component/legend';
import 'echarts/lib/component/toolbox';
import 'echarts/lib/component/dataZoom';
import { each, extend } from 'lodash';
import moment from 'moment';
import { getApigwChartDetail } from '@/services/source/runTime';

interface IProps {
  startTime: number | string
  endTime: number | string
}

interface Emits { (e: 'time-change', start_value?: number, end_value?: number): void }

const { startTime, endTime } = defineProps<IProps>();
const emits = defineEmits<Emits>();

const route = useRoute();
const { t } = useI18n();

const isChartDataLoading = ref(true);
const system = ref<string | string[]>('');
const chartInstance = ref();

const gettext = (text: string) => {
  return text;
};

const renderChart = () => {
  const _mts_end = Date.now();
  const _time_span = 86400000; // 3600 * 24 * 1000
  const _mts_start = _mts_end - _time_span;

  const default_options = getDefaultOptions(
    _mts_start,
    _mts_end,
  );

  // 绘制 系统实时概况 图表
  getApigwChartDetail({
    system: system.value,
    start: startTime,
    end: endTime,
  }).then((result) => {
    let chart_options = extend(
      default_options,
      getYAxisOptions(true, true, false),
      getSeriesOptions(result),
    );

    const echartStatus = echarts.init(document.getElementById('chart-status'));
    echartStatus.setOption(chart_options);
    echartStatus.on('datazoom', () => {
      chart_options = echartStatus.getOption();
      const start_value = chart_options.dataZoom[0].startValue;
      const end_value = chart_options.dataZoom[0].endValue;
      emits('time-change', start_value, end_value);
    });
    echartStatus.on('legendselectchanged', (params) => {
      const is_rate_availability_show = params.selected[gettext(t('可用率'))];
      const is_requests_show = params.selected[gettext(t('请求数'))];
      let is_resp_time_show = params.selected[gettext(t('平均响应时间'))] || params.selected[gettext(t('统计响应时间'))];
      if (is_requests_show) {
        is_resp_time_show = false;
      }
      echartStatus.setOption(getYAxisOptions(is_rate_availability_show, is_requests_show, is_resp_time_show));
    });
    chartInstance.value = echartStatus;
  })
    .finally(() => {
      isChartDataLoading.value = false;
    });
};

const getDefaultOptions = (start_value: number, end_value: number) => {
  return {
    title: {
      text: '',
      left: 'center',
      textStyle: { fontWeight: 'bold' },
    },
    grid: {
      top: '15%',
      left: '1%',
      right: '1%',
      bottom: '15%',
      containLabel: true,
    },
    xAxis: [{
      type: 'time',
      boundaryGap: false,
      // 设置横轴
      axisLine: {
        show: true,
        lineStyle: { color: '#dde3ea' },
      },
      // 设置横轴坐标刻度
      axisTick: { show: false },
      // 设置横轴文字
      axisLabel: { color: '#63656e' },
      // 设置风格 - 竖线
      splitLine: {
        show: true,
        lineStyle: {
          color: ['#ecf0f4'],
          type: 'dashed',
        },
      },
      data: [],
    }],
    legend: {
      selected: {
        '平均响应时间': false,
        'Average response time': false,
      },
      textStyle: { fontWeight: 'bold' },
      data: [
        { name: gettext(t('可用率')) },
        { name: gettext(t('请求数')) },
        { name: gettext(t('平均响应时间')) },
        { name: gettext(t('统计响应时间')) },
      ],
    },
    dataZoom: [
      {
        type: 'slider',
        xAxisIndex: 0,
        backgroundColor: '#fefefe',
        dataBackground: { color: '#a3c5fd' },
        lineStyle: { color: 'red' },
        filterMode: 'filter',
        // 初始的开始和结束位置，根据实际情况调整
        startValue: parseInt(end_value, 10) - 60 * 60 * 1000,
        endValue: parseInt(end_value, 10),
        realtime: false,
      },
    ],
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      formatter(params) {
        const tip_msg: any[] = [];
        let current_time = null;
        each(params, (obj) => {
          if (!obj.value) {
            return;
          }
          if (!current_time) {
            current_time = moment(obj.value[0]).format('YYYY-MM-DD HH:mm');
            tip_msg.push(current_time);
          }
          if (obj.value[1]) {
            if (obj.seriesName === gettext(t('可用率'))) {
              tip_msg.push(`${obj.seriesName}: ${obj.value[1].toFixed(2)} %`);
            }
            else if (obj.seriesName === gettext(t('平均响应时间')) || obj.seriesName === gettext(t('统计响应时间'))) {
              tip_msg.push(`${obj.seriesName}: ${obj.value[1].toFixed(2)} ms`);
            }
            else {
              tip_msg.push(`${obj.seriesName}: ${obj.value[1]}`);
            }
          }
        });
        return tip_msg.join('<br>');
      },
    },
  };
};

const getYAxisOptions = (is_rate_availability_show: boolean, is_requests_show: boolean, is_resp_time_show: boolean) => {
  return {
    yAxis: [
      {
        max: 100,
        min: 'dataMin',
        scale: true,
        position: 'left',
        axisLabel: {
          formatter(value: string, index: number) {
            if (index === 0) {
              // 第一个可能出现 99.94340690435767 样数字，保留小数点后两位
              const re = /([0-9]+.[0-9]{2})[0-9]*/;
              value = value.toString().replace(re, '$1');
            }
            return `${value}%`;
          },
          show: is_rate_availability_show,
        },
        axisTick: { show: is_rate_availability_show },
        axisLine: { show: false },
        // 设置网格 - 横线
        splitLine: {
          show: true,
          lineStyle: {
            color: ['#ecf0f4'],
            type: 'dashed',
          },
        },
      },
      {
        position: 'right',
        min: 0,
        minInterval: 1,
        axisLabel: { show: is_requests_show },
        axisTick: { show: is_requests_show },
        axisLine: { show: false },
        splitLine: { show: false },
      },
      {
        min: 0,
        axisLabel: {
          formatter: '{value}ms',
          show: is_resp_time_show,
        },
        axisTick: { show: is_resp_time_show },
        axisLine: { show: false },
        splitLine: { show: false },
      },
    ],
  };
};

const getSeriesOptions = (option: Record<string, any>) => {
  return {
    series: [
      {
        name: gettext(t('可用率')),
        type: 'line',
        position: 'left',
        yAxisIndex: 0,
        data: option?.rate_availability?.data,
        symbolSize: 2,
        showSymbol: false,
        lineStyle: { normal: { width: 2 } },
        itemStyle: { normal: { color: 'rgba(59,206,149,1)' } },
      },
      {
        name: gettext(t('请求数')),
        type: 'line',
        yAxisIndex: 1,
        data: option?.requests?.data,
        showSymbol: false,
        symbolSize: 2,
        lineStyle: { normal: { width: 2 } },
        itemStyle: { normal: { color: 'rgba(255,156,74,1)' } },
      },
      {
        name: gettext(t('平均响应时间')),
        type: 'line',
        data: option?.avg_resp_time?.data,
        yAxisIndex: 2,
        showSymbol: false,
        symbolSize: 2,
        connectNulls: true,
        lineStyle: { normal: { width: 2 } },
        itemStyle: { normal: { color: 'rgba(255,111,114,1)' } },
      },
      {
        name: gettext(t('统计响应时间')),
        type: 'line',
        data: option?.perc95_resp_time?.data,
        yAxisIndex: 2,
        symbolSize: 2,
        showSymbol: false,
        connectNulls: true,
        lineStyle: { normal: { width: 2 } },
        itemStyle: { normal: { color: 'rgba(51,157,255,1)' } },
      },
    ],
  };
};

onMounted(() => {
  system.value = route.params?.system;
  renderChart();
  window.onresize = () => {
    if (chartInstance.value) {
      chartInstance.value?.resize();
    }
  };
});
</script>
