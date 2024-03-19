<template>
  <bk-loading :loading="isChartDataLoading">
    <div id="chart-status" style="width: 100%; height: 350px;"></div>
  </bk-loading>
</template>

<script lang="ts" setup>
import echarts from 'echarts/lib/echarts';
import 'echarts/lib/chart/line';
import 'echarts/lib/component/tooltip';
import 'echarts/lib/component/legend';
import 'echarts/lib/component/toolbox';
import 'echarts/lib/component/dataZoom';
import _ from 'lodash';
import moment from 'moment';
import { useI18n } from 'vue-i18n';
import { ref, onMounted } from 'vue';
import { useRoute } from 'vue-router';
import { getApigwChartDetail } from '@/http';

const route = useRoute();
const { t } = useI18n();

function gettext(text: any) {
  return text;
}

const props = defineProps({
  startTime: {
    type: [Number, String],
  },
  endTime: {
    type: [Number, String],
  },
});

const emit = defineEmits(['time-change']);

const isChartDataLoading = ref<boolean>(true);
const system = ref<string | string[]>('');
const chartInstance = ref<any>();

onMounted(() => {
  system.value = route.params?.system;
  render_chart();

  window.onresize = () => {
    if (chartInstance.value) {
      chartInstance.value?.resize();
    }
  };
});

const render_chart = () => {
  const _mts_end = Date.now();
  const _time_span = 86400000; // 3600 * 24 * 1000
  const _mts_start = _mts_end - _time_span;

  const default_options = get_default_options(
    _mts_start,
    _mts_end,
  );

  // 绘制 系统实时概况 图表
  getApigwChartDetail({
    system: system.value,
    start: props.startTime,
    end: props.endTime,
  }).then((result: any) => {
    // if (result.error_message) {
    //     $('#chart-status').html('<div>' + gettext('获取系统最新状态数据失败') + ', ' + result.error_message + '</div>')
    //     return;
    // }
    const d = result;
    // if (!d) {
    //     $('#chart-status').html('<div>' + gettext('系统最新状态数据为空') + '</div>');
    //     return;
    // }

    let chart_options = _.extend(
      default_options,
      get_yaxis_options(true, true, false),
      get_series_options(d),
    );

    const echarts_status = echarts.init(document.getElementById('chart-status'));
    echarts_status.setOption(chart_options);
    echarts_status.on('datazoom', () => {
      chart_options = echarts_status.getOption();
      const start_value = chart_options.dataZoom[0].startValue;
      const end_value = chart_options.dataZoom[0].endValue;
      emit('time-change', start_value, end_value);
      // CurrentConf.set({
      //     time_since: 'custom:' + start_value + '_' + end_value,
      //     mts_start: start_value,
      //     mts_end: end_value
      // });
    });
    echarts_status.on('legendselectchanged', (params: any) => {
      const is_rate_availability_show = params.selected[gettext(t('可用率'))];
      const is_requests_show = params.selected[gettext(t('请求数'))];
      let is_resp_time_show = params.selected[gettext(t('平均响应时间'))] || params.selected[gettext(t('统计响应时间'))];
      if (is_requests_show) {
        is_resp_time_show = false;
      }
      echarts_status.setOption(get_yaxis_options(is_rate_availability_show, is_requests_show, is_resp_time_show));
    });
    chartInstance.value = echarts_status;
  })
    .finally(() => {
      isChartDataLoading.value = false;
    });
};

const get_default_options = (start_value: any, end_value: any) => {
  return {
    title: {
      text: '',
      left: 'center',
      textStyle: {
        fontWeight: 'bold',
      },
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
        lineStyle: {
          color: '#dde3ea',
        },
      },
      // 设置横轴坐标刻度
      axisTick: {
        show: false,
      },
      // 设置横轴文字
      axisLabel: {
        color: '#63656e',
      },
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
    // xAxis: [{
    //     type: 'time',
    //     splitLine: {
    //         show: false
    //     },
    // }],
    legend: {
      selected: {
        平均响应时间: false,
        'Average response time': false,
      },
      textStyle: {
        fontWeight: 'bold',
      },
      data: [
        {
          name: gettext(t('可用率')),
        },
        {
          name: gettext(t('请求数')),
        },
        {
          name: gettext(t('平均响应时间')),
        },
        {
          name: gettext(t('统计响应时间')),
        },
      ],
    },
    dataZoom: [
      {
        type: 'slider',
        xAxisIndex: 0,
        backgroundColor: '#fefefe',
        dataBackground: {
          color: '#a3c5fd',
        },
        lineStyle: {
          color: 'red',
        },
        filterMode: 'filter',
        // 初始的开始和结束位置，根据实际情况调整
        startValue: parseInt(end_value, 10) - 60 * 60 * 1000,
        endValue: parseInt(end_value, 10),
        realtime: false,
      },
    ],
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'shadow',
      },
      formatter(params: any) {
        const tip_msg: any[] = [];
        let current_time: any = null;
        _.each(params, (obj) => {
          if (!obj.value) {
            return;
          }
          if (!current_time) {
            current_time = moment(obj.value[0]).format('YYYY-MM-DD HH:mm');
            tip_msg.push(current_time);
          }
          if (obj.value[1] !== null) {
            if (obj.seriesName === gettext(t('可用率'))) {
              tip_msg.push(`${obj.seriesName}: ${obj.value[1].toFixed(2)} %`);
            } else if (obj.seriesName === gettext(t('平均响应时间')) || obj.seriesName === gettext(t('统计响应时间'))) {
              tip_msg.push(`${obj.seriesName}: ${obj.value[1].toFixed(2)} ms`);
            } else {
              tip_msg.push(`${obj.seriesName}: ${obj.value[1]}`);
            }
          }
        });
        return tip_msg.join('<br>');
      },
    },
  };
};

const get_yaxis_options = (is_rate_availability_show: any, is_requests_show: any, is_resp_time_show: any) => {
  return {
    yAxis: [
      {
        // name: 'rate_avail',
        max: 100,
        min: 'dataMin',
        scale: true,
        position: 'left',
        axisLabel: {
          formatter(value: any, index: any) {
            if (index === 0) {
              // 第一个可能出现 99.94340690435767 样数字，保留小数点后两位
              const re = /([0-9]+.[0-9]{2})[0-9]*/;
              value = value.toString().replace(re, '$1');
            }
            return `${value}%`;
          },
          show: is_rate_availability_show,
        },
        axisTick: {
          show: is_rate_availability_show,
        },
        axisLine: {
          show: false,
        },
        // axisLabel: {
        //     color: '#8a8f99',
        //     formatter (value, index) {
        //         return `${value}%`
        //     }
        // },
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
        // name: 'requests',
        position: 'right',
        min: 0,
        minInterval: 1,
        axisLabel: {
          show: is_requests_show,
        },
        axisTick: {
          show: is_requests_show,
        },
        axisLine: {
          show: false,
        },
        splitLine: {
          show: false,
        },
      },
      {
        // name: 'resp_time',
        min: 0,
        axisLabel: {
          formatter: '{value}ms',
          show: is_resp_time_show,
        },
        axisTick: {
          show: is_resp_time_show,
        },
        axisLine: {
          show: false,
        },
        splitLine: {
          show: false,
        },
      },
    ],
  };
};

const get_series_options = (d: any) => {
  return {
    series: [
      {
        name: gettext(t('可用率')),
        type: 'line',
        position: 'left',
        yAxisIndex: 0,
        data: d?.rate_availability?.data,
        symbolSize: 2,
        showSymbol: false,
        lineStyle: {
          normal: {
            width: 2,
          },
        },
        itemStyle: {
          normal: {
            color: 'rgba(59,206,149,1)',
          },
        },
      },
      {
        name: gettext(t('请求数')),
        type: 'line',
        yAxisIndex: 1,
        data: d?.requests?.data,
        showSymbol: false,
        symbolSize: 2,
        lineStyle: {
          normal: {
            width: 2,
          },
        },
        itemStyle: {
          normal: {
            color: 'rgba(255,156,74,1)',
          },
        },
      },
      {
        name: gettext(t('平均响应时间')),
        type: 'line',
        data: d?.avg_resp_time?.data,
        yAxisIndex: 2,
        showSymbol: false,
        symbolSize: 2,
        connectNulls: true,
        lineStyle: {
          normal: {
            width: 2,
          },
        },
        itemStyle: {
          normal: {
            color: 'rgba(255,111,114,1)',
          },
        },
      },
      {
        name: gettext(t('统计响应时间')),
        type: 'line',
        data: d?.perc95_resp_time?.data,
        yAxisIndex: 2,
        symbolSize: 2,
        showSymbol: false,
        connectNulls: true,
        lineStyle: {
          normal: {
            width: 2,
          },
        },
        itemStyle: {
          normal: {
            color: 'rgba(51,157,255,1)',
          },
        },
      },
    ],
  };
};
</script>
