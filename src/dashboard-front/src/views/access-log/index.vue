<template>
  <div class="app-content">
    <div class="ag-top-header">
      <bk-form class="search-form" form-type="inline">
        <bk-form-item :label="$t('选择时间')" class="ag-form-item-datepicker">
          <bk-date-picker
            ref="datePickerRef"
            style="width: 320px;"
            v-model="dateTimeRange"
            :placeholder="$t('选择日期时间范围')"
            :type="'datetimerange'"
            :shortcuts="datepickerShortcuts"
            :shortcut-close="true"
            :use-shortcut-text="true"
            :clearable="false"
            :shortcut-selected-index="shortcutSelectedIndex"
            @shortcut-change="handleShortcutChange"
            @pick-success="handleTimeChange">
          </bk-date-picker>
        </bk-form-item>
        <bk-form-item :label="$t('环境')">
          <bk-select
            style="width: 150px;"
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
        <bk-form-item :label="$t('查询条件')" class="ag-form-item-inline">
          <search-input v-model="keyword" @search="handleSearch" :class="['top-search-input', localLanguage === 'en' ? 'top-search-input-en' : '']" />
          <span v-bk-tooltips="searchUsage.config" class="search-usage">
            {{`${searchUsage.showed ? $t('隐藏示例') : $t('显示示例')}`}}
          </span>
        </bk-form-item>
      </bk-form>
    </div>
    <div v-bkloading="{ isLoading: !isPageLoading && isDataLoading }">
      <div class="chart">
        <div class="chart-container">
          <div class="chart-title"> {{ $t('请求数') }} </div>
          <div v-show="isShowChart" class="chart-el" ref="chartContainer"></div>
          <div v-show="!isShowChart && !isPageLoading" class="ap-nodata">
            <div slot="empty">
              <table-empty
                :keyword="tableEmptyConf.keyword"
                :abnormal="tableEmptyConf.isAbnormal"
                @reacquire="getSearchData"
                @clear-filter="clearFilterKey"
              />
            </div>
          </div>
        </div>
      </div>
      <div class="list">
        <bk-table
          ref="table"
          :data="table.list"
          :size="'small'"
          :pagination="pagination"
          :row-style="{ cursor: 'pointer' }"
          :row-class-name="getRowClassName"
          @row-click="handleRowClick"
          @page-change="handlePageChange"
          @page-limit-change="handlePageLimitChange">
          <div slot="empty">
            <table-empty
              :keyword="tableEmptyConf.keyword"
              :abnormal="tableEmptyConf.isAbnormal"
              @reacquire="getSearchData"
              @clear-filter="clearFilterKey"
            />
          </div>
          <bk-table-column type="expand" width="30" align="center">
            <template slot-scope="{ row }">
              <dl class="details">
                <div class="item" v-for="({ label, field, is_filter: showCopy }, index) in table.fields" :key="index">
                  <dt class="label">
                    {{label}}
                    <i
                      v-bk-tooltips="$t('复制字段名')"
                      v-if="showCopy"
                      class="apigateway-icon icon-ag-clipboard copy-btn"
                      @click="handleClickCopyField(field)">
                    </i>
                  </dt>
                  <dd class="value">{{row[field] | formatValue(field)}}</dd>
                </div>
                <bk-button
                  class="share-btn"
                  theme="primary"
                  outline
                  @click="handleClickCopyLink(row)"
                  :loading="isShareLoading"> {{ $t('复制分享链接') }} </bk-button>
              </dl>
            </template>
          </bk-table-column>
          <template v-if="table.headers.length">
            <bk-table-column
              v-for="({ field, label, width, formatter }, index) in table.headers"
              :show-overflow-tooltip="true"
              :key="index"
              :width="width"
              :formatter="formatter"
              :label="label"
              :class-name="field"
              :prop="field">
            </bk-table-column>
          </template>
          <template v-else>
            <bk-table-column
              label="">
            </bk-table-column>
          </template>
        </bk-table>
      </div>
    </div>

    <div id="access-log-search-usage-content">
      <div class="sample">
        <p>
          <span class="mode">{{ $t('匹配包含某个关键字') }}: </span>
          <span class="value" @click="handleClickUsageValue">request_id: b3e2497532e54f518b3d1267fb67c83a</span></p>
        <p>
          <span class="mode">{{ $t('多个关键字匹配') }}: </span>
          <span class="value" @click="handleClickUsageValue">(app_code: "app-template" AND client_ip: "1.0.0.1") OR resource_name: get_user</span>
        </p>
        <p>
          <span class="mode">{{ $t('不包含关键字') }}: </span>
          <span class="value" @click="handleClickUsageValue">-status: 200</span></p>
        <p>
          <span class="mode">{{ $t('范围匹配') }}: </span>
          <span class="value" @click="handleClickUsageValue">duration: [5000 TO 30000]</span>
        </p>
      </div>
      <div class="more">
        {{ $t('更多示例请参阅') }} <a class="link" target="_blank" :href="GLOBAL_CONFIG.DOC.QUERY_USE"> {{ $t('“请求流水查询规则”') }} </a>
      </div>
    </div>
  </div>
</template>

<script>
  import { mapGetters } from 'vuex'
  import dayjs from 'dayjs'
  import merge from 'lodash.merge'
  import echarts from 'echarts/lib/echarts'
  import 'echarts/lib/chart/bar'
  import 'echarts/lib/component/tooltip'
  import { bus } from '@/common/bus'
  import { catchErrorHandler } from '@/common/util'
  import chartMixin from '@/mixins/chart'

  let chartInstance = null

  export default {
    filters: {
      formatValue (value, field) {
        if (value && field === 'timestamp') {
          return dayjs.unix(value).format('YYYY-MM-DD HH:mm:ss ZZ')
        }

        return value || '--'
      }
    },
    mixins: [chartMixin],
    data () {
      return {
        isPageLoading: true,
        isDataLoading: false,
        isShareLoading: false,
        dateTimeRange: [],
        shortcutSelectedIndex: 1,
        keyword: '',
        searchParams: {
          stage_id: '',
          time_start: '',
          time_end: '',
          query: ''
        },
        table: {
          list: [],
          fields: [],
          headers: []
        },
        pagination: {
          current: 1,
          count: 0,
          limit: 10
        },
        stageList: [],
        searchUsage: {
          config: {
            allowHtml: true,
            trigger: 'click',
            theme: 'light',
            content: '#access-log-search-usage-content',
            onShow: () => {
              this.searchUsage.showed = true
            },
            onClose: () => {
              this.searchUsage.showed = false
            }
          },
          showed: false
        },
        chartData: {},
        tableEmptyConf: {
          keyword: '',
          isAbnormal: false
        }
      }
    },
    computed: {
      ...mapGetters('options', ['datepickerShortcuts']),
      apigwId () {
        return this.$route.params.id
      },
      isShowChart () {
        return this.chartData.series && this.chartData.series.length
      },
      formatterValue () {
        return params => this.$t(`{value} 次`, { value: params.value.toLocaleString() })
      },
      localLanguage () {
        return this.$store.state.localLanguage
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
        await this.getApigwStages()
        this.getSearchData()
      },
      initChart () {
        chartInstance = echarts.init(this.$refs.chartContainer)
        window.addEventListener('resize', this.chartResize)
      },
      chartResize () {
        this.$nextTick(() => {
          chartInstance.resize()
        })
      },
      async getSearchData () {
        this.isDataLoading = true
        try {
          this.setSearchTimeRange()

          const [listRes, chartRes] = await Promise.all([this.getApigwAccessLogList(), this.getApigwAccessLogChart()])

          this.chartData = chartRes.data
          this.renderChart(this.chartData)

          this.table.list = listRes.data.results
          this.table.fields = listRes.data.fields
          // 根据接口要求最大显示10000条以内数据，但总条数仍然显示为实际值
          this.pagination.count = Math.min(listRes.data.count, 10000)
          this.$nextTick(() => {
            const countDom = document.querySelector('.bk-page-total-count .stress')
            if (countDom) {
              countDom.innerText = listRes.data.count
            }
          })

          this.setTableHeader()
          this.updateTableEmptyConfig()
          this.tableEmptyConf.isAbnormal = false
        } catch (e) {
          this.tableEmptyConf.isAbnormal = true
          catchErrorHandler(e, this)
        } finally {
          this.isPageLoading = false
          this.isDataLoading = false
          this.$store.commit('setMainContentLoading', false)
          this.setTableHeader()
        }
      },
      getApigwAccessLogList () {
        const apigwId = this.apigwId
        const params = {
          ...this.searchParams,
          query: this.keyword,
          offset: (this.pagination.current - 1) * this.pagination.limit,
          limit: this.pagination.limit
        }

        return this.$store.dispatch('accessLog/getApigwAccessLogList', { apigwId, params })
      },
      getApigwAccessLogChart () {
        const apigwId = this.apigwId
        const params = {
          ...this.searchParams,
          query: this.keyword,
          no_page: true
        }

        return this.$store.dispatch('accessLog/getApigwAccessLogChart', { apigwId, params })
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
      renderChart (data) {
        const { timeline } = data
        const xAxisData = timeline.map(time => dayjs.unix(time).format('MM-DD\nHH:mm:ss'))

        const _that = this
        const options = {
          grid: {
            left: 20,
            right: 20,
            top: 16,
            bottom: 16,
            containLabel: true
          },
          xAxis: {
            type: 'category',
            data: xAxisData,
            axisLabel: {
              color: '#A0A4AA'
            },
            axisLine: {
              lineStyle: {
                color: '#e9edf0'
              }
            },
            axisTick: {
              alignWithLabel: true,
              lineStyle: {
                color: '#BDC8D3'
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
            type: 'bar',
            data: data.series,
            barMaxWidth: 60,
            itemStyle: {
              color: '#5B8FF9'
            }
          }],
          tooltip: {
            trigger: 'item',
            backgroundColor: 'rgba(0, 0, 0, 0.7)',
            textStyle: {
              fontSize: 12
            },
            formatter (params) {
              return `${_that.formatterValue(params)}<br />${params.name}`
            }
          }
        }

        const timeDuration = timeline[timeline.length - 1] - timeline[0]
        const intervalOption = this.$getChartIntervalOption(timeDuration, 'time', 'xAxis')

        chartInstance.setOption(merge(options, intervalOption))
        this.chartResize()
      },
      setTableHeader () {
        const formatValue = this.$options.filters['formatValue']
        const columns = [
          {
            field: 'timestamp',
            width: 220,
            label: this.$t('请求时间'),
            formatter: (row, column, cellValue) => {
              return formatValue(cellValue, column.property)
            }
          },
          { field: 'method', width: 160, label: this.$t('请求方法') },
          { field: 'http_path', label: this.$t('请求路径') },
          { field: 'status', width: 160, label: this.$t('状态码') },
          { field: 'backend_duration', width: 160, label: this.$t('耗时(毫秒)') },
          {
            field: 'error',
            width: 200,
            label: this.$t('错误'),
            formatter: (row, column, cellValue) => {
              return formatValue(cellValue, column.property)
            }
          }
        ]
        this.table.headers = columns
      },
      setSearchTimeRange () {
        let timeRange = this.dateTimeRange
                
        // 选择的是时间快捷项，需要实时计算时间值
        if (this.shortcutSelectedIndex !== -1) {
          timeRange = this.datepickerShortcuts[this.shortcutSelectedIndex].value()
        }
        const formatTimeRange = this.formatDatetime(timeRange)
        this.searchParams.time_start = formatTimeRange[0]
        this.searchParams.time_end = formatTimeRange[1]
      },
      getRowClassName ({ row }) {
        return (!(row.status >= 200 && row.status < 300) || row.error) ? 'exception' : ''
      },
      formatDatetime (timeRange) {
        return [
          (+new Date(`${timeRange[0]}`)) / 1000,
          (+new Date(`${timeRange[1]}`)) / 1000
        ]
      },
      handleClickCopyField (field) {
        this.$copyText(field).then((e) => {
          this.$bkMessage({
            theme: 'success',
            limit: 1,
            message: this.$t('复制成功')
          })
        }, () => {
          this.$bkMessage({
            theme: 'error',
            limit: 1,
            message: this.$t('复制失败')
          })
        })
      },
      async handleClickCopyLink (row) {
        const apigwId = this.apigwId
        const { request_id } = row
        const params = { request_id }

        this.isShareLoading = true

        try {
          const res = await this.$store.dispatch('accessLog/getApigwAccessLogShareLink', { apigwId, params })

          const link = res.data.link || ''
          this.$copyText(link).then((e) => {
            this.$bkMessage({
              theme: 'success',
              limit: 1,
              message: this.$t('复制成功')
            })
          }, () => {
            this.$bkMessage({
              theme: 'error',
              limit: 1,
              message: this.$t('复制失败')
            })
          })
        } catch (e) {
          catchErrorHandler(e, this)
        } finally {
          this.isShareLoading = false
        }
      },
      handleStageSelected (value) {
        this.searchParams.stage_id = value
        this.pagination.current = 1
        this.getSearchData()
      },
      handleSearch () {
        this.searchParams.query = this.keyword
        this.pagination.current = 1
        this.getSearchData()
      },
      handleClickUsageValue (event) {
        this.keyword = event.target.innerText
      },
      handleTimeChange () {
        this.$nextTick(() => {
          this.pagination.current = 1
          this.getSearchData()
        })
      },
      handleShortcutChange (value, index) {
        this.shortcutSelectedIndex = index
        this.updateTableEmptyConfig()
      },
      handlePageLimitChange (limit) {
        this.pagination.limit = limit
        this.pagination.current = 1
        this.getSearchData()
      },
      handlePageChange (newPage) {
        this.pagination.current = newPage
        this.getSearchData()
      },
      handleRowClick (row) {
        this.$refs.table.toggleRowExpansion(row)
      },
      clearFilterKey () {
        this.keyword = ''
        if (this.$refs.datePickerRef) {
          this.$refs.datePickerRef.shortcut = this.datepickerShortcuts[1]
          this.shortcutSelectedIndex = 1
        }
        this.handleSearch()
      },
      updateTableEmptyConfig () {
        const time = this.dateTimeRange.some(Boolean)
        if (this.keyword || this.searchParams.stage_id || time) {
          this.tableEmptyConf.keyword = 'placeholder'
          return
        }
        this.tableEmptyConf.keyword = ''
      }
    }
  }
</script>

<style lang="postcss" scoped>
    @import '@/css/variable.css';

    .chart-container {
        width: 100%;
        background: #FFF;
        border: 1px solid #DCDEE5;

        .chart-title {
            color: #262625;
            font-size: 14px;
            padding: 10px 0 0 10px;
        }

        .chart-el {
            width: 100%;
            height: 160px;
        }
    }

    .list {
        margin-top: 16px;

        .details {
            position: relative;
            padding: 16px 0;
            .item {
                display: flex;
                margin-bottom: 8px;
                .label {
                    position: relative;
                    flex: none;
                    width: 200px;
                    font-weight: bold;
                    color: #63656E;
                    margin-right: 32px;
                    text-align: right;

                    .copy-btn {
                        color: #C4C6CC;
                        font-size: 12px;
                        position: absolute;
                        right: -18px;
                        top: 4px;
                        cursor: pointer;

                        &:hover {
                            color: #3A84FF;
                        }
                    }
                }
                .value {
                    font-family: 'Courier New', Courier, monospace;
                    flex: none;
                    width: calc(100% - 300px);
                    white-space: pre-wrap;
                    word-break: break-word;
                    color: #63656E;
                    line-height: 20px;
                }
            }

            .share-btn {
                position: absolute;
                right: 0;
                top: 18px;
            }
        }

        /deep/.exception {
            background: #F9EDEC;

            &:hover {
                td {
                    background: #F9EDEC;
                }
            }

            .status,
            .error {
                color: #FF5656;
            }
        }
    }

    .search-usage {
        font-size: 12px;
        color: $primaryColor;
        line-height: 32px;
        margin-left: 16px;
        cursor: pointer;
    }

    #access-log-search-usage-content {
        font-size: 12px;
        line-height: 26px;
        padding: 4px;
        .sample {
            .mode {
                color: #63656e;
            }
            .value {
                color: #3a84ff;
                cursor: pointer;
            }
        }
        .more {
            color: #63656e;
            border-top: 1px dashed #C4C6CC;
            margin-top: 10px;
            padding-top: 8px;

            .link {
                color: $primaryColor;
            }
        }
    }

    .search-form {
        width: 100% !important;
        max-width: 100% !important;

        .top-search-input {
            width: 600px;
        }
    }

    @media (max-width: 1753px) {
        .search-form {
            width: 700px !important;

            .ag-form-item-inline {
                margin-left: 0 !important;
                margin-top: 10px !important;
            }

            .top-search-input {
                width: 526px;
            }
            .top-search-input-en {
                width: 460px;
            }
        }
    }
    .ap-nodata {
        height: 280px;
    }
</style>
