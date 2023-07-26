<template>
  <div class="app-content">
    <div class="ag-top-header">
      <bk-form class="search-form" form-type="inline">
        <bk-form-item :label="$t('选择时间')" class="ag-form-item-datepicker top-form-item-time">
          <bk-date-picker
            style="width: 320px;"
            v-model="dateTimeRange"
            :placeholder="$t('选择日期时间范围')"
            :type="'datetimerange'"
            :shortcuts="shortcutsInDay"
            :shortcut-close="true"
            :use-shortcut-text="true"
            :clearable="false"
            :shortcut-selected-index="shortcutSelectedIndex"
            @shortcut-change="handleShortcutChange"
            @pick-success="handleTimeChange">
          </bk-date-picker>
        </bk-form-item>
        <bk-form-item :label="$t('环境')" class="top-form-item-stage">
          <bk-select
            style="width: 160px;"
            v-model="searchParams.stage_id"
            :clearable="false"
            searchable
            @selected="handleStageSelected">
            <bk-option v-for="option in stageList"
              :key="option.id"
              :id="option.id"
              :name="option.name">
            </bk-option>
          </bk-select>
        </bk-form-item>
        <bk-form-item :label="$t('资源')" class="top-form-item-resource">
          <bk-select
            class="top-resource-select"
            :popover-width="180"
            ext-popover-cls="resource-dropdown-content"
            v-model="searchParams.resource_id"
            searchable
            @change="handleResourceChange">
            <bk-option v-for="option in resourceList"
              :key="option.id"
              :id="option.id"
              :name="`${option.method} ${option.path}`">
            </bk-option>
          </bk-select>
        </bk-form-item>
        <bk-form-item :label="$t('数据维度')" class="top-form-item-dimension">
          <bk-select
            style="width: 160px;"
            v-model="searchParams.dimension"
            @change="handleDimensionChange">
            <bk-option v-for="option in dimensionOptions"
              :key="option.value"
              :id="option.value"
              :name="option.name">
            </bk-option>
          </bk-select>
        </bk-form-item>
        <bk-button theme="primary" class="ml10 top-refresh-button" :disabled="isDataLoading" @click="handleRefresh"> {{ $t('刷新') }} </bk-button>
      </bk-form>
    </div>

    <div class="page-content" v-bkloading="{ isLoading: isDataLoading }">
      <!-- 按维度分组创建图表容器，切换维度通过控制图表组容器元素进行显示隐藏 -->
      <div class="chart" v-for="(charts, key) in chartConfig" :key="key" v-show="key === dimension && !isDataLoading">
        <div class="chart-container" v-for="(chart, chartIndex) in charts" :key="chartIndex">
          <div class="chart-title">{{`${chart.name}${dimensionName ? ` / ${dimensionName}` : ''}`}}</div>
          <div v-show="!chartEmpty[`${key}_${chart.id}`]" class="chart-wrapper">
            <div class="chart-el" :ref="`${key}_${chart.id}`" :id="`${key}_${chart.id}`"></div>
            <div class="chart-legend" v-if="chartLegend[`${key}_${chart.id}`]">
              <div v-for="({ color, name, selected }, legendIndex) in chartLegend[`${key}_${chart.id}`]"
                :key="legendIndex"
                :class="['legend-item', { selected, unselected: selected === false }]"
                @click.stop="handleClickLegend(`${key}_${chart.id}`, legendIndex)">
                <div class="legend-icon" :style="{ background: color }"></div>
                <div class="legend-name">{{name}}</div>
              </div>
            </div>
          </div>
          <div v-show="chartEmpty[`${key}_${chart.id}`] && !isPageLoading" class="ap-nodata">
            <div slot="empty">
              <table-empty empty />
            </div>
          </div>
        </div>
      </div>
    </div>

  </div>
</template>

<script>
  import { mapGetters } from 'vuex'
  import merge from 'lodash.merge'
  import dayjs from 'dayjs'
  import echarts from 'echarts/lib/echarts'
  import 'echarts/lib/chart/line'
  import 'echarts/lib/component/tooltip'
  import 'echarts/lib/component/legend'
  import 'echarts/lib/component/toolbox'
  import 'echarts/lib/component/dataZoom'
  import { bus } from '@/common/bus'
  import { getColorHue } from '@/common/util.js'
  import { catchErrorHandler } from '@/common/util'
  import chartMixin from '@/mixins/chart'

  const chartInstances = {}

  export default {
    mixins: [chartMixin],
    data () {
      return {
        isPageLoading: true,
        isDataLoading: false,
        dateTimeRange: [],
        shortcutSelectedIndex: 1,
        searchParams: {
          stage_id: '',
          resource_id: '',
          time_start: '',
          time_end: '',
          dimension: ''
        },
        stageList: [],
        resourceList: [],
        chartData: {},
        chartLegend: {},
        chartEmpty: {},
        dimensionOptions: [
          {
            name: this.$t('资源'),
            value: 'resource'
          },
          {
            name: this.$t('蓝鲸应用ID'),
            value: 'app'
          },
          {
            name: this.$t('资源+非200状态码'),
            value: 'resource_non200_status'
          }
        ],
        metricsMap: {
          resource: [
            'requests',
            'failed_requests'
          ],
          app: ['requests'],
          resource_non200_status: ['requests'],
          all: [
            'requests',
            'failed_requests',
            'response_time_95th',
            'response_time_90th',
            'response_time_80th',
            'response_time_50th'
          ]
        }
      }
    },
    computed: {
      ...mapGetters('options', ['shortcutsInDay']),
      apigwId () {
        return this.$route.params.id
      },
      dimension () {
        return this.searchParams.dimension || 'all'
      },
      dimensionName () {
        return (this.dimensionOptions.find(item => item.value === this.dimension) || {}).name
      },
      metricsList () {
        return this.metricsMap[this.dimension]
      },
      chartConfig () {
        const titles = {
          requests: this.$t('请求数'),
          failed_requests: this.$t('失败请求数'),
          response_time: this.$t('响应时间')
        }

        const chartConfig = {}
        Object.keys(this.metricsMap).forEach(key => {
          let config = this.metricsMap[key]
          if (key === 'all') {
            const groupName = 'response_time'
            config = config.filter(item => !item.startsWith(`${groupName}_`))
            config.push(groupName)
          }
          chartConfig[key] = config.map(item => ({
            id: item,
            name: titles[item]
          }))
        })

        return chartConfig
      }
    },
    created () {
      this.init()
    },
    mounted () {
      this.initChart()

      bus.$on('side-toggle-end', () => {
        this.chartResize()
      })
    },
    beforeDestroy () {
      window.removeEventListener('resize', this.chartResize)
    },
    methods: {
      async init () {
        // 资源列表
        this.getApigwResources()

        // 业务数据的加载依赖环境参数的初始化
        await this.getApigwStages()
        this.getDataByDimension()
      },
      initChart () {
        Object.keys(this.chartConfig).forEach(key => {
          const configs = this.chartConfig[key]
          configs.forEach(config => {
            const chartId = `${key}_${config.id}`
            chartInstances[chartId] = echarts.init(this.$refs[chartId][0])
          })
        })

        window.addEventListener('resize', this.chartResize)
      },
      chartResize () {
        this.$nextTick(() => {
          Object.values(chartInstances).forEach(chart => {
            chart.resize()
          })
        })
      },
      async getDataByDimension () {
        const apigwId = this.apigwId
        const dimension = this.dimension
        const metricsList = this.metricsList
        this.setSearchTimeRange()
        // 限制在一天内
        if ((this.searchParams.time_end - this.searchParams.time_start) > 24 * 60 * 60) {
          this.$bkMessage({
            theme: 'error',
            limit: 1,
            message: this.$t('请重新选择时间范围，最长不超过一天')
          })
          return false
        }
        const requests = metricsList.map(metrics => {
          const params = {
            ...this.searchParams,
            dimension,
            metrics
          }

          return this.$store.dispatch('report/getApigwMetrics', { apigwId, params })
        })

        this.isDataLoading = true
        try {
          const res = await Promise.all(requests)
          this.chartData = {}
          metricsList.forEach((metrics, index) => {
            this.chartData[metrics] = res[index]
          })

          this.renderChart()
        } catch (e) {
          catchErrorHandler(e, this)
        } finally {
          this.isPageLoading = false
          this.isDataLoading = false
          this.$store.commit('setMainContentLoading', false)
        }
      },
      async getApigwStages () {
        const apigwId = this.apigwId
        const pageParams = {
          no_page: true,
          order_by: 'name'
        }

        try {
          const res = await this.$store.dispatch('stage/getApigwStages', { apigwId, pageParams })
          this.stageList = res.data.results

          this.searchParams.stage_id = (this.stageList[0] || {}).id
        } catch (e) {
          catchErrorHandler(e, this)
        }
      },
      async getApigwResources () {
        const apigwId = this.apigwId
        const pageParams = {
          no_page: true,
          order_by: 'path'
        }

        try {
          const res = await this.$store.dispatch('resource/getApigwResources', { apigwId, pageParams })
          this.resourceList = res.data.results
        } catch (e) {
          catchErrorHandler(e, this)
        }
      },
      renderChart () {
        this.chartConfig[this.dimension].forEach(config => {
          const chartId = config.id
          const chartInstId = `${this.dimension}_${chartId}`
          const option = this.getChartOption(chartId, chartInstId)
          this.$nextTick(() => {
            chartInstances[chartInstId].setOption(option, { notMerge: true })

            // 切换图例，处理单个数据点x轴显示问题
            chartInstances[chartInstId].on('legendselected', function (params) {
              const currentOption = this.getOption()
              const serie = currentOption.series.find(item => item.name === params.name) || {}
              if (serie.data && serie.data.length === 1) {
                // fix单个数据点xAxis显示异常，本质上是去掉动态计算出的间隔设置
                this.setOption({
                  xAxis: {
                    interval: 'auto'
                  }
                })
              } else {
                this.setOption(option)
              }
            })
            this.chartResize()
            this.generateChartLegend(chartId, chartInstId)
          })
        })
      },
      getChartOption (chartId, chartInstId) {
        const dimension = this.dimension
        const baseOption = {
          grid: {
            left: 30,
            right: 30,
            top: 30,
            bottom: 30,
            containLabel: true
          },
          xAxis: {
            type: 'time',
            scale: true,
            boundaryGap: false,
            axisLabel: {
              color: '#A0A4AA'
            },
            axisLine: {
              lineStyle: {
                color: '#e9edf0'
              }
            },
            axisTick: {
              show: false,
              alignWithLabel: true,
              lineStyle: {
                color: '#BDC8D3'
              }
            },
            splitLine: {
              lineStyle: {
                color: '#e9edf0'
              }
            }
          },
          yAxis: {
            type: 'value',
            axisLabel: {
              color: '#A0A4AA'
            },
            splitLine: {
              lineStyle: {
                color: '#e9edf0'
              }
            },
            axisLine: {
              show: false
            },
            axisTick: {
              show: false
            }
          },
          series: [{
            data: [],
            type: 'line',
            showSymbol: false,
            connectNulls: true,
            lineStyle: {
              width: 1
            },
            areaStyle: {
              opacity: 0.2
            }
          }],
          tooltip: {
            trigger: 'axis',
            axisPointer: {
              type: 'line',
              // snap: true,
              lineStyle: {
                color: '#ff5656',
                opacity: 0.7
              }
            },
            backgroundColor: 'rgba(0, 0, 0, 0.7)',
            textStyle: {
              fontSize: 12
            }
          },
          legend: {
            show: false,
            left: 30,
            right: 30,
            bottom: 10,
            itemWidth: 10,
            itemHeight: 3,
            icon: 'roundRect'
          },
          toolbox: {
            right: 40,
            feature: {
              dataZoom: {
                yAxisIndex: false
              }
            }
          },
          animation: false
        }

        const chartOption = {
          yAxis: {},
          series: [],
          tooltip: {}
        }
        let moreOption = {}

        // 不同纬度返回的数据结构略有差异，因此分开处理
        if (['resource', 'resource_non200_status', 'app'].includes(dimension)) {
          const chartData = this.chartData[chartId].data.series
          chartData.forEach(item => {
            const serieName = dimension === 'app' ? `APP=${item.dimensions.bk_app_code || '--'}` : `${item.dimensions.resource_name}`
            const values = item.datapoints.filter(value => !isNaN(Math.round(value[0])))
            chartOption.series.push(merge({}, baseOption.series[0], {
              name: serieName,
              data: values.map(value => ([
                // x轴数据，x轴type为time数据需为时间戳
                value[1],
                // 系列数据
                value[0]
              ])),
              // 1个数据点显示小圆点
              showSymbol: values.length === 1
            }))
          })

          // 设置图表颜色
          chartOption.color = this.generateChartColor(chartData, chartId)

          // debug单个数据点
          // chartData.forEach(item => {
          //     if (item.values.length === 1) {
          //         console.log(item.metric.resource || item.metric.app_code, 'item.metric.resource')
          //     }
          // })

          // 设置图表max和interval
          const serieData = chartData.map(item => item.datapoints).reduce((a, b) => a.concat(b), [])
          moreOption = this.getChartMoreOption(serieData, chartInstances[chartInstId])
          chartOption.yAxis.scale = true

          // 设置图表tooltip内容
          chartOption.tooltip.formatter = (params) => {
            const html = [`<p>${dayjs(params[0].data[0]).format('YYYY-MM-DD HH:mm:ss')}</p>`]
            params.forEach(param => {
              html.push(`<p><span>${param.marker}${param.seriesName}: </span><span>${param.data[1] !== null ? param.data[1].toLocaleString() : '0'} ${this.$t('次')}</span></p>`)
            })
            return html.join('')
          }

          // 标记图表是否数据为空
          this.chartEmpty[chartInstId] = !(chartData || []).length
        } else if (dimension === 'all') {
          if (chartId !== 'response_time') {
            let chartData = (this.chartData[chartId].data.series[0] || {}).datapoints || []
            chartData = chartData.filter(value => !isNaN(Math.round(value[0])))
            chartOption.series.push(merge({}, baseOption.series[0], {
              data: chartData.map(item => ([
                item[1],
                item[0]
              ]))
            }))

            // 设置图表颜色
            chartOption.color = this.generateChartColor(chartData, chartId)

            moreOption = this.getChartMoreOption(chartData)

            // 设置图表tooltip内容
            chartOption.tooltip.formatter = (params) => {
              const html = [`<p>${dayjs(params[0].data[0]).format('YYYY-MM-DD HH:mm:ss')}</p>`]
              params.forEach(param => {
                html.push(`<p>${param.marker}${param.data[1] !== null ? param.data[1].toLocaleString() : '0'} ${this.$t('次')}</p>`)
              })
              return html.join('')
            }

            this.chartEmpty[chartInstId] = !(chartData || []).length
          } else {
            const chartData = [
              (this.chartData['response_time_95th'].data.series[0] || {}).datapoints || [],
              (this.chartData['response_time_90th'].data.series[0] || {}).datapoints || [],
              (this.chartData['response_time_80th'].data.series[0] || {}).datapoints || [],
              (this.chartData['response_time_50th'].data.series[0] || {}).datapoints || []
            ]
            const serieNames = ['95%', '90%', '80%', '50%']
            chartData.forEach((data, index) => {
              const values = data.filter(value => !isNaN(Math.round(value[0])))
              chartOption.series.push(merge({}, baseOption.series[0], {
                name: serieNames[index],
                data: values.map(item => ([
                  item[1],
                  item[0]
                ]))
              }))
            })

            chartOption.yAxis.axisLabel = {
              formatter: '{value} ms'
            }

            // 设置图表颜色
            chartOption.color = this.generateChartColor(chartData, chartId)

            const serieData = chartData.reduce((a, b) => a.concat(b), [])
            moreOption = this.getChartMoreOption(serieData)

            // 设置图表tooltip内容
            chartOption.tooltip.formatter = (params) => {
              const html = [`<p>${dayjs(params[0].data[0]).format('YYYY-MM-DD HH:mm:ss')}</p>`]
              params.forEach(param => {
                html.push(`<p><span>${param.marker}${param.seriesName}: </span><span>${param.data[1].toLocaleString()} ms</span></p>`)
              })
              return html.join('')
            }

            this.chartEmpty[chartInstId] = !serieData.length
          }
        }

        return merge(baseOption, chartOption, moreOption)
      },
      getChartMoreOption (chartData, chartInstance) {
        // 1. 根据data的最大值，动态计算出max合适值和interval配置
        const serieData = chartData.map(item => Math.round(item[0])).filter(item => !isNaN(item))
        const maxNumber = Math.max(...serieData)
        const yAxisIntervalOption = this.$getChartIntervalOption(maxNumber, 'number', 'yAxis', chartInstance)

        // 2. 根据时间值计算xAxis显示年/月/日/时间部分
        const xAxisData = chartData.map(item => Math.round(item[1]))
        xAxisData.sort((a, b) => a - b)
        // timeDuration 需要秒为单位
        const timeDuration = Math.round((xAxisData[xAxisData.length - 1] - xAxisData[0]) / 1000)
        const xAxisIntervalOption = this.$getChartIntervalOption(timeDuration, 'time', 'xAxis', chartInstance)

        return merge(yAxisIntervalOption, xAxisIntervalOption)
      },
      generateChartLegend (chartId, chartInstId) {
        const option = chartInstances[chartInstId].getOption()
        // 只有一个系列不需要图例
        if (option.series.length > 1) {
          this.chartLegend[chartInstId] = option.series.map((serie, index) => ({
            color: option.color[index],
            name: serie.name,
            // 0值表示默认状态
            selected: 0
          }))
        } else {
          this.chartLegend[chartInstId] = null
        }
      },
      generateChartColor (chartData, chartId) {
        let baseColor = ['#3A84FF', '#5AD8A6', '#5D7092', '#F6BD16', '#FF5656', '#6DC8EC']
        let angle = 30
        if (chartId.indexOf('failed_') !== -1) {
          baseColor = ['#FF5656', '#5AD8A6']
          angle = 10
        }
        const colors = []
        const interval = Math.ceil(chartData.length / baseColor.length)

        baseColor.forEach(color => {
          let i = 0
          while (i < interval) {
            const co = getColorHue(color, i * angle)
            colors.push(co)
            i++
          }
        })

        const finalColors = colors.reduce((a, b) => a.concat(b), [])
        return finalColors
      },
      setSearchTimeRange () {
        let timeRange = this.dateTimeRange

        // 选择的是时间快捷项，需要实时计算时间值
        if (this.shortcutSelectedIndex !== -1) {
          timeRange = this.shortcutsInDay[this.shortcutSelectedIndex].value()
        }
        const formatTimeRange = this.formatDatetime(timeRange)
        this.searchParams.time_start = formatTimeRange[0]
        this.searchParams.time_end = formatTimeRange[1]
      },
      formatDatetime (timeRange) {
        return [
          (+new Date(`${timeRange[0]}`)) / 1000,
          (+new Date(`${timeRange[1]}`)) / 1000
        ]
      },
      handleClickLegend (chartInstId, index) {
        const chartInstance = chartInstances[chartInstId]
        const chartLegend = this.chartLegend[chartInstId]
        const currentLegend = chartLegend[index]

        const selected = currentLegend.selected

        // 实现切换单选显示
        if (!selected) {
          // 仅显示选中
          chartInstance.dispatchAction({
            type: 'legendUnSelect',
            batch: chartLegend.map(({ name }) => ({ name }))
          })
          chartInstance.dispatchAction({
            type: 'legendSelect',
            name: currentLegend.name
          })

          // 选中状态设置
          chartLegend.forEach((item, i) => {
            item.selected = index === i
          })
          this.chartLegend = { ...this.chartLegend, ...{ [chartInstId]: chartLegend } }
        } else {
          // 全部显示
          chartInstance.dispatchAction({
            type: 'legendSelect',
            batch: chartLegend.map(({ name }) => ({ name }))
          })

          chartLegend.forEach((item, i) => (item.selected = 0))
          this.chartLegend = { ...this.chartLegend, ...{ [chartInstId]: chartLegend } }
        }
      },
      handleDimensionChange (value) {
        this.searchParams.dimension = value
        this.getDataByDimension()
      },
      handleStageSelected (value) {
        this.searchParams.stage_id = value
        this.getDataByDimension()
      },
      handleResourceChange (value) {
        this.searchParams.resource_id = value
        this.getDataByDimension()
      },
      handleTimeChange () {
        this.getDataByDimension()
      },
      handleShortcutChange (value, index) {
        this.shortcutSelectedIndex = index
      },
      handleRefresh () {
        // TODO 待组件更新，根据日历shortcut值计算实时时间查询
        this.getDataByDimension()
      }
    }
  }
</script>

<style lang="postcss" scoped>
    @import '@/css/variable.css';
    @import '@/css/mixins/scroll.css';

    .page-content {
        min-height: calc(100vh - 268px);
    }

    .chart-container {
        width: 100%;
        background: #FFF;
        border: 1px solid #DCDEE5;
        margin-bottom: 12px;

        .chart-wrapper {
            width: 100%;
        }

        .chart-title {
            color: #262625;
            font-size: 16px;
            padding: 20px 0 0 20px;
        }

        .chart-el {
            width: 100%;
            height: 360px;
        }

        .chart-legend {
            display: flex;
            flex-wrap: wrap;
            margin: 0 40px 30px 40px;
            max-height: 110px;
            overflow-y: auto;
            @mixin scroller;

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

            .legend-name {
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
    }

    .search-form {
        width: 100%;

        .top-resource-select {
            width: 260px;
        }
    }

    @media (max-width: 1660px) {
        .search-form {
            width: 780px;

            /deep/.bk-form-item {
                .bk-label {
                    width: 72px !important;
                }

                &.top-form-item-resource {
                    margin-top: 10px;
                    margin-left: 0;
                }
                &.top-form-item-dimension {
                    margin-top: 10px;
                }
            }

            .top-resource-select {
                width: 320px;
            }

            .top-refresh-button {
                margin-top: 10px;
            }
        }
    }
</style>

<style lang="postcss">
    @import '@/css/mixins/ellipsis.css';
    .resource-dropdown-content {
        .bk-option-name {
            width: 100%;
            @mixin ellipsis;
        }
    }
</style>
