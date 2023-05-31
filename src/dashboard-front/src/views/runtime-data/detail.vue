<template>
  <div class="app-content">
    <div class="top-header mb15">
      <div class="filter" style="overflow: hidden;">
        <strong class="title" style="color: #63656e; font-weight: normal;">{{systemName}}<span class="f12" v-if="principalFlag"> （{{ $t('负责人：') }}{{summaryData.basic_info.maintainers.join(', ')}}）</span></strong>
        <div class="auto-refresh fr">
          <bk-switcher class="mr10" v-model="autoEnable" theme="primary"></bk-switcher><span class="vm f13"> {{ $t('每分钟自动刷新') }} </span>
        </div>
      </div>
    </div>
    <div class="chart-box">
      <chart-view @time-change="handlTimeChnage" :start-time="dayStartTime" :end-time="endTime"></chart-view>
    </div>

    <div class="card-box" v-bkloading="{ isLoading: isSummaryDataLoading }">
      <div class="card">
        <div class="value">{{summaryData.requests.count_str || '--'}}</div>
        <div class="key"> {{ $t('请求数') }} </div>
      </div>
      <div class="card">
        <div class="value">{{summaryData.rate_availability.value_str || '--'}}%</div>
        <div class="key">
          {{ $t('可用率') }}
          <span v-bk-tooltips="$t('该系统在指定时间范围内可用率低于100%')" v-if="summaryData.rate_availability.value < 1">
            <i class="apigateway-icon icon-ag-info"></i>
          </span>
        </div>
      </div>
      <div class="card">
        <div class="value">{{summaryData.perc95_resp_time.value_str || '--'}}ms</div>
        <div class="key">
          {{ $t('统计响应时间') }}
          <span v-bk-tooltips="$t('根据百分位计算出的响应时间，相比平均响应时间，更能反映问题')" v-if="summaryData.rate_availability.value < 1">
            <i class="apigateway-icon icon-ag-help"></i>
          </span>
        </div>
      </div>
    </div>

    <div class="runtime-container">
      <bk-tab :active.sync="active" type="unborder-card" @tab-change="handleTabChange">
        <bk-tab-panel name="req_component_name" :label="$t('按组件')">
          <bk-table
            :data="requests"
            :border="false"
            :outer-border="false"
            :header-border="true"
            v-bkloading="{ isLoading: isDataLoading, opacity: 1, delay: 1000 }"
            :size="'small'">
            <div slot="empty">
              <table-empty empty />
            </div>
            <bk-table-column type="index" :label="$t('序列')" width="60"></bk-table-column>
            <bk-table-column :label="$t('组件名')" prop="req_component_name"></bk-table-column>
            <bk-table-column :label="$t('错误 / 总次数')" prop="req_component_name" sortable :sort-method="handleSortCount" :render-header="$renderHeader">
              <template slot-scope="props">
                <span v-if="props.row.requests.error_count">{{props.row.requests.error_count}} /</span> <span>{{props.row.requests.count}}</span>
                <bk-button v-if="props.row.requests.error_count" :text="true" @click="handleShowDetail(props.row)" class="ml5"> {{ $t('详情') }} </bk-button>
              </template>
            </bk-table-column>
            <bk-table-column :label="$t('统计响应时间(ms)')" prop="req_component_name" sortable :sort-method="handleSortRespTime" :render-header="$renderHeader">
              <template slot-scope="props">
                {{props.row.perc95_resp_time.value}}
              </template>
            </bk-table-column>
            <bk-table-column :label="$t('平均响应时间(ms)')" prop="req_component_name" sortable :sort-method="handleSortAvgTime" :render-header="$renderHeader">
              <template slot-scope="props">
                {{props.row.avg_resp_time.value}}
              </template>
            </bk-table-column>
            <bk-table-column :label="$t('可用率')" prop="req_component_name" sortable :sort-method="handleSortRate" :render-header="$renderHeader">
              <template slot-scope="props">
                {{props.row.rate_availability.value_str}}%
              </template>
            </bk-table-column>
          </bk-table>
        </bk-tab-panel>

        <bk-tab-panel name="req_app_code" :label="$t('按APP')">
          <bk-table
            :data="requests"
            :border="false"
            :outer-border="false"
            :header-border="true"
            v-bkloading="{ isLoading: isDataLoading, opacity: 1, delay: 1000 }"
            :size="'small'">
            <div slot="empty">
              <table-empty empty />
            </div>
            <bk-table-column type="index" :label="$t('序列')" width="60"></bk-table-column>
            <bk-table-column label="app_code" prop="req_app_code"></bk-table-column>
            <bk-table-column :label="$t('错误 / 总次数')" prop="req_component_name" sortable :sort-method="handleSortCount" :render-header="$renderHeader">
              <template slot-scope="props">
                <span v-if="props.row.requests.error_count">{{props.row.requests.error_count}} /</span> <span>{{props.row.requests.count}}</span>
                <bk-button v-if="props.row.requests.error_count" :text="true" @click="handleShowDetail(props.row)" class="ml5"> {{ $t('详情') }} </bk-button>
              </template>
            </bk-table-column>
            <bk-table-column :label="$t('统计响应时间(ms)')" prop="req_component_name" sortable :sort-method="handleSortRespTime" :render-header="$renderHeader">
              <template slot-scope="props">
                {{props.row.perc95_resp_time.value}}
              </template>
            </bk-table-column>
            <bk-table-column :label="$t('平均响应时间(ms)')" prop="req_component_name" sortable :sort-method="handleSortAvgTime" :render-header="$renderHeader">
              <template slot-scope="props">
                {{props.row.avg_resp_time.value}}
              </template>
            </bk-table-column>
            <bk-table-column :label="$t('可用率')" prop="req_component_name" sortable :sort-method="handleSortRate" :render-header="$renderHeader">
              <template slot-scope="props">
                {{props.row.rate_availability.value_str}}%
              </template>
            </bk-table-column>
          </bk-table>
        </bk-tab-panel>

        <bk-tab-panel name="req_url" :label="$t('按URL')">
          <bk-table
            :data="requests"
            :border="false"
            :outer-border="false"
            :header-border="true"
            v-bkloading="{ isLoading: isDataLoading, opacity: 1, delay: 1000 }"
            :size="'small'">
            <div slot="empty">
              <table-empty empty />
            </div>
            <bk-table-column type="index" :label="$t('序列')" width="60"></bk-table-column>
            <bk-table-column label="URL" prop="req_url" :min-width="200"></bk-table-column>
            <bk-table-column :label="$t('错误 / 总次数')" prop="req_component_name" sortable :sort-method="handleSortCount" :render-header="$renderHeader">
              <template slot-scope="props">
                <span v-if="props.row.requests.error_count">{{props.row.requests.error_count}} /</span> <span>{{props.row.requests.count}}</span>
                <bk-button v-if="props.row.requests.error_count" :text="true" @click="handleShowDetail(props.row)" class="ml5"> {{ $t('详情') }} </bk-button>
              </template>
            </bk-table-column>
            <bk-table-column :label="$t('统计响应时间(ms)')" prop="req_component_name" :sortable="true" :sort-method="handleSortRespTime" :render-header="$renderHeader">
              <template slot-scope="props">
                {{props.row.perc95_resp_time.value}}
              </template>
            </bk-table-column>
            <bk-table-column :label="$t('平均响应时间(ms)')" prop="req_component_name" :sortable="true" :sort-method="handleSortAvgTime" :render-header="$renderHeader">
              <template slot-scope="props">
                {{props.row.avg_resp_time.value}}
              </template>
            </bk-table-column>
            <bk-table-column :label="$t('可用率')" prop="req_component_name" :sortable="true" :sort-method="handleSortRate" :render-header="$renderHeader">
              <template slot-scope="props">
                {{props.row.rate_availability.value_str}}%
              </template>
            </bk-table-column>
          </bk-table>
        </bk-tab-panel>
      </bk-tab>
    </div>

    <bk-dialog
      v-model="detailDialog.visiable"
      theme="primary"
      :width="900"
      :mask-close="true"
      :header-position="'left'"
      :title="$t('错误请求详情')"
      :show-footer="false">
      <div v-bkloading="{ isLoading: isErrorDataLoading, opacity: 1, delay: 1000 }">
        <div class="mb10">
          <strong>{{detailDialog.name}}</strong>
        </div>
        <bk-alert class="mb10" type="info" :title="$t('此处最多展示最近 200 条错误信息')"></bk-alert>
        <bk-table
          :data="errorRequests"
          :header-border="true"
          :max-height="400"
          :size="'small'">
          <div slot="empty">
            <table-empty empty />
          </div>
          <bk-table-column :label="$t('时间')" prop="datetime" width="120"></bk-table-column>
          <bk-table-column :label="$t('错误信息')" prop="message" :render-header="$renderHeader"></bk-table-column>
          <bk-table-column :label="$t('耗时')" prop="time" width="120"></bk-table-column>
          <bk-table-column :label="$t('响应状态')" prop="status" width="80" :render-header="$renderHeader"></bk-table-column>
        </bk-table>
      </div>
    </bk-dialog>
  </div>
</template>

<script>
  import ChartView from './chart.vue'
  import moment from 'moment'
  import i18n from '@/language/i18n.js'

  export default {
    components: {
      ChartView
    },
    data () {
      return {
        timer: 0,
        autoEnable: true,
        detailDialog: {
          name: '',
          visiable: false
        },
        panels: [
          { name: 'req_component_name', label: i18n.t('按组件') },
          { name: 'req_app_code', label: i18n.t('按APP') },
          { name: 'req_url', label: i18n.t('按URL') }
        ],
        active: 'req_component_name',
        requests: [],
        pagination: {
          current: 1,
          count: 500,
          limit: 20
        },
        endTime: Date.now(),
        startTime: Date.now() - 60 * 60 * 1000,
        dayStartTime: Date.now() - 24 * 60 * 60 * 1000,
        isDataLoading: true,
        isSummaryDataLoading: true,
        summaryData: {
          avg_resp_time: {
            value: ''
          },
          perc95_resp_time: {
            value_str: ''
          },
          rate_availability: {
            value_str: ''
          },
          requests: {
            count_str: ''
          }
        },
        isErrorDataLoading: false,
        errorRequests: [],
        chartData: {
          system_name: '',
          avg_resp_time: {
            data: []
          },
          perc95_resp_time: {
            data: []
          },
          rate_availability: {
            data: []
          },
          requests: {
            data: []
          }
        }
      }
    },
    computed: {
      principalFlag () {
        if (this.summaryData.basic_info && this.summaryData.basic_info.maintainers.length) {
          return true
        }
        return false
      }
    },
    watch: {
      autoEnable () {
        this.enableAutoRefresh()
      },

      'detailDialog.visiable' (value) {
        if (value) {
          this.clearAutoRefresh()
        } else {
          this.enableAutoRefresh()
        }
      }
    },
    created () {
      this.system = this.$route.params.system
      this.systemName = this.$route.query.systemName
      this.init()
      this.$route.meta.title = `${this.$t('系统实时概况')}`
    },
    mounted () {
      // this.initChart()
    },
    methods: {
      init () {
        this.getRuntimeRequest()
        this.getSystemSummary()
        this.enableAutoRefresh()
      },

      async getRuntimeRequest () {
        this.isDataLoading = true
        try {
          const res = await this.$store.dispatch('runtime/getApigwRuntimeRequest', {
            type: this.active,
            system: this.system,
            start: this.startTime,
            end: this.endTime
          })
          this.requests = res.data
        } catch (e) {
          // catchErrorHandler(e, this)
        } finally {
          this.isDataLoading = false
          this.$store.commit('setMainContentLoading', false)
        }
      },

      handleSortCount (a, b) {
        if (a.requests.count < b.requests.count) {
          return -1
        }
        if (a.requests.count > b.requests.count) {
          return 1
        }
        return 0
      },

      handleSortRespTime (a, b) {
        if (a.perc95_resp_time.value < b.perc95_resp_time.value) {
          return -1
        }
        if (a.perc95_resp_time.value > b.perc95_resp_time.value) {
          return 1
        }
        return 0
      },

      handleSortAvgTime (a, b) {
        if (a.avg_resp_time.value < b.avg_resp_time.value) {
          return -1
        }
        if (a.avg_resp_time.value > b.avg_resp_time.value) {
          return 1
        }
        return 0
      },

      handleSortRate (a, b) {
        if (a.rate_availability.value < b.rate_availability.value) {
          return -1
        }
        if (a.rate_availability.value > b.rate_availability.value) {
          return 1
        }
        return 0
      },

      async getSystemSummary () {
        this.isSummaryDataLoading = true
        try {
          const res = await this.$store.dispatch('runtime/getApigwSystemSummary', {
            system: this.system,
            start: this.startTime,
            end: this.endTime
          })
          this.summaryData = res.data
        } catch (e) {
          // catchErrorHandler(e, this)
        } finally {
          this.isSummaryDataLoading = false
        }
      },

      handlTimeChnage (start, end) {
        this.startTime = start
        this.endTime = end
        this.init()
      },

      handleTabChange (name) {
        this.active = name
        this.getRuntimeRequest(name)
      },

      enableAutoRefresh () {
        clearInterval(this.timer)
        if (!this.autoEnable) {
          return false
        }
        this.timer = setInterval(() => {
          this.init()
        }, 1000 * 60)
      },

      clearAutoRefresh () {
        clearInterval(this.timer)
      },

      goBack () {
        this.$router.push({
          name: 'runtimeData'
        })
      },

      async handleShowDetail (data) {
        this.isErrorDataLoading = true
        this.errorRequests = []
        this.detailDialog.visiable = true
        this.detailDialog.name = data.req_app_code || data.req_component_name || data.req_url || '--'

        try {
          const res = await this.$store.dispatch('runtime/getApigwErrorRequest', {
            system: this.system,
            appCode: data.req_app_code || '',
            componentName: data.req_component_name || '',
            requestUrl: data.req_url || '',
            start: this.startTime,
            end: this.endTime
          })
          this.errorRequests = res.data.data.data_list.map(item => {
            const datetime = moment(item.timestamp).format('MM-DD HH:mm')
            const endTime = moment(item.req_end_time).valueOf()
            const startTime = moment(item.req_start_time).valueOf()
            const time = endTime - startTime
            return {
              datetime: datetime,
              message: item.req_exception,
              status: item.req_status,
              time: time + 'ms'
            }
          })
        } catch (e) {
          // catchErrorHandler(e, this)
        } finally {
          this.isErrorDataLoading = false
        }
      }
    }
  }
</script>
<style lang="postcss" scoped>
    .chart-box {
        width: 100%;
        background: #FFF;
        border: 1px solid #dcdee5;
        border-radius: 2px;
        margin-bottom: 20px;
        padding: 10px;
    }
    .runtime-container {
        background: #FFF;
        border: 1px solid #dcdee5;
        border-radius: 2px;
    }
    .card-box {
        background: #FFF;
        border: 1px solid #dcdee5;
        border-radius: 2px;
        margin-bottom: 20px;
        display: flex;
        padding: 20px 0;

        .card {
            text-align: center;
            flex: 1;
            border-left: 1px solid #eee;

            .value {
                font-size: 40px;
                color: #63656e;
            }

            .key {
                font-size: 14px;
                color: #979ba5;
            }
        }
    }
</style>
