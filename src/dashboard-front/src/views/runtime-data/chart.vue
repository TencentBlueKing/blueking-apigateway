<template>
    <div id="chart-status" style="width: 100%; height: 350px;" v-bkloading="{ isLoading: isChartDataLoading }"></div>
</template>

<script>
    import echarts from 'echarts/lib/echarts'
    import 'echarts/lib/chart/line'
    import 'echarts/lib/component/tooltip'
    import 'echarts/lib/component/legend'
    import 'echarts/lib/component/toolbox'
    import 'echarts/lib/component/dataZoom'
    import _ from 'lodash'
    import moment from 'moment'
    import i18n from '@/language/i18n.js'

    function gettext (text) {
        return text
    }

    export default {
        props: {
            startTime: {
                type: [Number, String]
            },
            endTime: {
                type: [Number, String]
            },
        },
        data () {
            return {
                isChartDataLoading: true,
                system: '',
            }
        },
        mounted () {
            this.system = this.$route.params.system
            this.render_chart()
            
            window.onresize = () => {
                if (this.chartInstance) {
                    this.chartInstance.resize()
                }
            }
        },
        methods: {
            render_chart: function() {
                var self = this;
                var get_series_options = this.get_series_options;
                var get_yaxis_options = this.get_yaxis_options;

                var _mts_start;
                var _mts_end = Date.now();
                var _time_span = 86400000; // 3600 * 24 * 1000
                _mts_start = _mts_end - _time_span;

                var default_options = this.get_default_options(
                    _mts_start,
                    _mts_end
                );

                // 绘制 系统实时概况 图表
                this.$store.dispatch('runtime/getApigwChartDetail', {
                    system: this.system,
                    start: this.startTime,
                    end: this.endTime
                }).then(result => {
                    // if (result.error_message) {
                    //     $('#chart-status').html('<div>' + gettext('获取系统最新状态数据失败') + ', ' + result.error_message + '</div>')
                    //     return;
                    // }
                    var d = result.data;
                    // if (!d) {
                    //     $('#chart-status').html('<div>' + gettext('系统最新状态数据为空') + '</div>');
                    //     return;
                    // }

                    var chart_options = _.extend(
                        default_options,
                        get_yaxis_options(true, true, false),
                        get_series_options(d)
                    );

                    var echarts_status = echarts.init(document.getElementById('chart-status'));
                    echarts_status.setOption(chart_options);
                    echarts_status.on('datazoom', function(params) {
                        chart_options = echarts_status.getOption();
                        var start_value = chart_options.dataZoom[0].startValue;
                        var end_value = chart_options.dataZoom[0].endValue;
                        self.$emit('time-change', start_value, end_value)
                        // CurrentConf.set({
                        //     time_since: 'custom:' + start_value + '_' + end_value,
                        //     mts_start: start_value,
                        //     mts_end: end_value
                        // });
                    });
                    echarts_status.on('legendselectchanged', function(params){
                        var is_rate_availability_show = params.selected[gettext(i18n.t('可用率'))]
                        var is_requests_show = params.selected[gettext(i18n.t('请求数'))]
                        var is_resp_time_show = params.selected[gettext(i18n.t('平均响应时间'))] || params.selected[gettext(i18n.t('统计响应时间'))]
                        if (is_requests_show) {
                            is_resp_time_show = false;
                        }
                        this.setOption(get_yaxis_options(is_rate_availability_show, is_requests_show, is_resp_time_show));
                    });
                    self.chartInstance = echarts_status
                }).finally(res => {
                    this.isChartDataLoading = false
                });
            },
            get_default_options: function(start_value, end_value) {
                return {
                    title: {
                        text: '',
                        left: 'center',
                        textStyle: {
                            fontWeight: 'bold',
                        }
                    },
                    grid: {
                        top: '15%',
                        left: '1%',
                        right: '1%',
                        bottom: '15%',
                        containLabel: true
                    },
                    xAxis: [{
                        type: 'time',
                        boundaryGap: false,
                        // 设置横轴
                        axisLine: {
                            show: true,
                            lineStyle: {
                                color: '#dde3ea'
                            }
                        },
                        // 设置横轴坐标刻度
                        axisTick: {
                            show: false
                        },
                        // 设置横轴文字
                        axisLabel: {
                            color: '#63656e'
                        },
                        // 设置风格 - 竖线
                        splitLine: {
                            show: true,
                            lineStyle: {
                                color: ['#ecf0f4'],
                                type: 'dashed'
                            }
                        },
                        data: []
                    }],
                    // xAxis: [{
                    //     type: 'time',
                    //     splitLine: {
                    //         show: false
                    //     },
                    // }],
                    legend: {
                        selected: {
                            '平均响应时间': false,
                            'Average response time': false,
                        },
                        textStyle: {
                            fontWeight: 'bold',
                        },
                        data: [
                            {
                                name: gettext(i18n.t('可用率')),
                            },
                            {
                                name: gettext(i18n.t('请求数')),
                            },
                            {
                                name: gettext(i18n.t('平均响应时间')),
                            },
                            {
                                name: gettext(i18n.t('统计响应时间')),
                            }
                        ]
                    },
                    dataZoom: [
                        {
                            type: 'slider',
                            xAxisIndex: 0,
                            backgroundColor: '#fefefe',
                            dataBackground: {
                                color: '#a3c5fd'
                            },
                            lineStyle: {
                                color: 'red'
                            },
                            filterMode: 'filter',
                            // 初始的开始和结束位置，根据实际情况调整
                            startValue: parseInt(end_value) - 60 * 60 * 1000,
                            endValue: parseInt(end_value),
                            realtime: false,
                        }
                    ],
                    tooltip: {
                        trigger: 'axis',
                        axisPointer: {
                            type: 'shadow'
                        },
                        formatter: function(params) {
                            var tip_msg = [];
                            var current_time = null;
                            _.each(params, function(obj, index) {
                                if (!obj.value) {
                                    return;
                                }
                                if (!current_time) {
                                    current_time = moment(obj.value[0]).format('YYYY-MM-DD HH:mm');
                                    tip_msg.push(current_time);
                                }
                                if (obj.value[1] != null) {
                                    if (obj.seriesName == gettext(i18n.t('可用率'))) {
                                        tip_msg.push(obj.seriesName + ': ' + obj.value[1].toFixed(2) + ' %');
                                    } else if (obj.seriesName == gettext(i18n.t('平均响应时间')) || obj.seriesName == gettext(i18n.t('统计响应时间'))) {
                                        tip_msg.push(obj.seriesName + ': ' + obj.value[1].toFixed(2) + ' ms');
                                    } else {
                                        tip_msg.push(obj.seriesName + ': ' + obj.value[1]);
                                    }
                                }
                            });
                            return tip_msg.join('<br>');
                        }
                    }
                };
            },
            get_yaxis_options: function(is_rate_availability_show, is_requests_show, is_resp_time_show) {
                return {
                    yAxis: [
                        {
                            //name: 'rate_avail',
                            max: 100,
                            min: 'dataMin',
                            scale: true,
                            position: 'left',
                            axisLabel: {
                                formatter: function(value, index) {
                                    if (index === 0) {
                                        // 第一个可能出现 99.94340690435767 样数字，保留小数点后两位
                                        var re = /([0-9]+.[0-9]{2})[0-9]*/;
                                        value = value.toString().replace(re, '$1');
                                    }
                                    return value + '%';
                                },
                                show: is_rate_availability_show,
                            },
                            axisTick: {
                                show: is_rate_availability_show,
                            },
                            axisLine: {
                                show: false
                            },
                            splitLine: {
                                show: false
                            },
                            // 设置纵轴文字
                            axisLabel: {
                                formatter: function(value, index) {
                                    if (index === 0) {
                                        // 第一个可能出现 99.94340690435767 样数字，保留小数点后两位
                                        var re = /([0-9]+.[0-9]{2})[0-9]*/;
                                        value = value.toString().replace(re, '$1');
                                    }
                                    return value + '%';
                                },
                                show: is_rate_availability_show,
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
                                    type: 'dashed'
                                }
                            }
                        },
                        {
                            //name: 'requests',
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
                                show: false
                            },
                            splitLine: {
                                show: false
                            }
                        },
                        {
                            //name: 'resp_time',
                            min: 0,
                            axisLabel: {
                                formatter: '{value}ms',
                                show: is_resp_time_show,
                            },
                            axisTick: {
                                show: is_resp_time_show,
                            },
                            axisLine: {
                                show: false
                            },
                            splitLine: {
                                show: false
                            }
                        }
                    ]
                }
            },
            get_series_options: function(d) {
                return {
                    series: [
                        {
                            name: gettext(i18n.t('可用率')),
                            type: 'line',
                            position: 'left',
                            yAxisIndex: 0,
                            data: d.rate_availability.data,
                            symbolSize: 2,
                            showSymbol: false,
                            lineStyle : {
                                normal: {
                                    width: 2,
                                }
                            },
                            itemStyle: {
                                normal: {
                                    color: 'rgba(59,206,149,1)',
                                }
                            }
                        },
                        {
                            name: gettext(i18n.t('请求数')),
                            type: 'line',
                            yAxisIndex: 1,
                            data: d.requests.data,
                            showSymbol: false,
                            symbolSize: 2,
                            lineStyle: {
                                normal: {
                                    width: 2,
                                }
                            },
                            itemStyle: {
                                normal: {
                                    color: 'rgba(255,156,74,1)',
                                }
                            },
                        },
                        {
                            name: gettext(i18n.t('平均响应时间')),
                            type: 'line',
                            data: d.avg_resp_time.data,
                            yAxisIndex: 2,
                            showSymbol: false,
                            symbolSize: 2,
                            connectNulls: true,
                            lineStyle : {
                                normal: {
                                    width: 2,
                                }
                            },
                            itemStyle: {
                                normal: {
                                    color: 'rgba(255,111,114,1)',
                                }
                            }
                        },
                        {
                            name: gettext(i18n.t('统计响应时间')),
                            type: 'line',
                            data: d.perc95_resp_time.data,
                            yAxisIndex: 2,
                            symbolSize: 2,
                            showSymbol: false,
                            connectNulls: true,
                            lineStyle : {
                                normal: {
                                    width: 2,
                                }
                            },
                            itemStyle: {
                                normal: {
                                    color: 'rgba(51,157,255,1)',
                                }
                            }
                        }
                    ]
                }
            },
        }
    }
</script>
