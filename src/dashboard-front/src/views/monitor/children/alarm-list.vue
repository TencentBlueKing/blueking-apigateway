<template>
  <div class="alarm-list">
    <div class="ag-top-header">
      <bk-form class="fl" form-type="inline">
        <bk-form-item :label="$t('选择时间')">
          <bk-date-picker
            class="ag-picker"
            v-model="dateTimeRange"
            :placeholder="$t('选择日期时间范围')"
            :type="'datetimerange'"
            :shortcuts="datepickerShortcuts"
            :shortcut-close="true"
            :use-shortcut-text="true"
            @clear="handleTimeClear"
            @pick-success="handleTimeChange">
          </bk-date-picker>
        </bk-form-item>
        <bk-form-item :label="$t('告警策略')">
          <bk-select
            style="width: 220px;"
            v-model="searchParams.alarm_strategy_id"
            searchable>
            <bk-option v-for="option in alarmStrategies"
              :key="option.id"
              :id="option.id"
              :name="option.name">
            </bk-option>
          </bk-select>
        </bk-form-item>
        <bk-form-item :label="$t('告警状态')">
          <bk-select
            style="width: 150px;"
            v-model="searchParams.status">
            <bk-option v-for="option in alarmStatus"
              :key="option.value"
              :id="option.value"
              :name="option.name">
            </bk-option>
          </bk-select>
        </bk-form-item>
      </bk-form>
    </div>
    <bk-table
      :data="table.list"
      :size="'small'"
      :row-style="{ cursor: 'pointer' }"
      :highlight-current-row="true"
      :pagination="pagination"
      v-bkloading="{ isLoading: isDataLoading }"
      v-if="!pageLoading"
      @page-limit-change="handlePageLimitChange"
      @page-change="handlePageChange"
      @row-click="handleRowClick">
      <div slot="empty">
        <table-empty
          :keyword="tableEmptyConf.keyword"
          :abnormal="tableEmptyConf.isAbnormal"
          @reacquire="getApigwAlarms"
          @clear-filter="clearFilterKey"
        />
      </div>
      <bk-table-column :label="$t('告警ID')" width="120" prop="id">
        <template slot-scope="{ row }">
          <bk-link theme="primary">{{row.id}}</bk-link>
        </template>
      </bk-table-column>
      <bk-table-column :label="$t('告警时间')" width="200" prop="created_time" :render-header="$renderHeader"></bk-table-column>
      <bk-table-column :label="$t('告警策略')" prop="alarm_strategy_names" :render-header="$renderHeader">
        <template slot-scope="{ row }">
          <template v-if="row.alarm_strategy_names.length">
            <div class="strategy-names pt5" style="display: inline-block;" v-bk-tooltips.top="row.alarm_strategy_names.join('; ')">
              <template v-for="(name, index) of row.alarm_strategy_names">
                <span class="ag-label vm mb5" v-if="index < 4" :key="index">
                  {{name}}
                </span>
              </template>
              <template v-if="row.alarm_strategy_names.length > 4">
                <span class="ag-label vm mb5">
                  ...
                </span>
              </template>
            </div>
          </template>
          <template v-else>
            --
          </template>
        </template>
      </bk-table-column>
      <bk-table-column
        :label="$t('告警内容')"
        prop="message"
        :render-header="$renderHeader"
        :formatter="(row) => row.message || '--'">
      </bk-table-column>
      <bk-table-column :label="$t('状态')" width="200">
        <template slot-scope="{ row }">
          <span :class="['ag-ouline-dot', row.status]"></span>
          <span class="status-text">{{getAlarmStatusText(row.status)}}</span>
        </template>
      </bk-table-column>
    </bk-table>

    <bk-sideslider
      :quick-close="true"
      :title="slider.title"
      :width="600"
      :is-show.sync="slider.isShow">
      <div slot="content" class="p30">
        <section class="ag-kv-list">
          <div class="item">
            <div class="key"> {{ $t('告警ID：') }} </div>
            <div class="value">{{slider.data.id}}</div>
          </div>
          <div class="item">
            <div class="key"> {{ $t('告警时间：') }} </div>
            <div class="value">{{slider.data.created_time}}</div>
          </div>
          <div class="item">
            <div class="key"> {{ $t('告警策略：') }} </div>
            <div class="value strategy-name-list">
              <p class="name-item" v-for="(name, index) of slider.data.alarm_strategy_names" :key="index">
                <span class="ag-label" :title="name">{{name}}</span>
              </p>
            </div>
          </div>
          <div class="item">
            <div class="key"> {{ $t('告警内容：') }} </div>
            <div class="value" style="line-height: 22px; padding: 10px 0;">
              <pre>{{slider.data.message || '--'}}</pre>
            </div>
          </div>
          <div class="item">
            <div class="key"> {{ $t('状态：') }} </div>
            <div class="value">
              <span :class="['ag-ouline-dot', slider.data.status]"></span>
              <span class="status-text">{{getAlarmStatusText(slider.data.status)}}</span>
            </div>
          </div>
        </section>
      </div>
    </bk-sideslider>
  </div>
</template>

<script>
  import { catchErrorHandler } from '@/common/util'
  import { mapGetters } from 'vuex'

  export default {
    props: {
      pageLoading: {
        type: Boolean,
        default: false
      }
    },
    data () {
      return {
        dateTimeRange: [],
        isDataLoading: false,
        table: {
          list: [],
          fields: [],
          headers: []
        },
        slider: {
          isShow: false,
          title: this.$t('告警详情'),
          data: {}
        },
        alarmStrategies: [],
        pagination: {
          current: 1,
          count: 0,
          limit: 10
        },
        searchParams: {
          alarm_strategy_id: '',
          status: '',
          time_start: '',
          time_end: ''
        },
        tableEmptyConf: {
          keyword: '',
          isAbnormal: false
        }
      }
    },
    computed: {
      ...mapGetters('options', ['datepickerShortcuts', 'alarmStrategyOptions', 'alarmStatus']),
      apigwId () {
        return this.$route.params.id
      }
    },
    watch: {
      searchParams: {
        deep: true,
        handler () {
          this.pagination.current = 1
          this.getApigwAlarms()
        }
      }
    },
    created () {
      this.getApigwAlarmStrategies()
      this.getApigwAlarms()
    },
    methods: {
      async getApigwAlarms () {
        const apigwId = this.apigwId
        const params = {
          ...this.searchParams,
          offset: (this.pagination.current - 1) * this.pagination.limit,
          limit: this.pagination.limit
        }

        this.isDataLoading = true

        try {
          const res = await this.$store.dispatch('monitor/getApigwAlarms', { apigwId, params })
          this.table.list = res.data.results
          this.pagination.count = res.data.count
          this.updateTableEmptyConfig()
          this.tableEmptyConf.isAbnormal = false
        } catch (e) {
          this.tableEmptyConf.isAbnormal = true
          catchErrorHandler(e, this)
        } finally {
          this.$emit('update:pageLoading', false)
          this.isDataLoading = false
        }
      },

      async getApigwAlarmStrategies () {
        const apigwId = this.apigwId
        const params = {
          no_page: true,
          order_by: 'name'
        }

        this.isDataLoading = true

        try {
          const res = await this.$store.dispatch('monitor/getApigwAlarmStrategies', { apigwId, params })
          this.alarmStrategies = res.data.results
        } catch (e) {
          catchErrorHandler(e, this)
        } finally {
          this.isDataLoading = false
        }
      },

      getAlarmStatusText (status) {
        return (this.alarmStatus.find(item => item.value === status) || {}).name
      },

      handleRowClick (row) {
        this.slider.isShow = true
        this.slider.data = row
      },

      handleTimeChange () {
        this.$nextTick(() => {
          this.searchParams.time_start = (+new Date(`${this.dateTimeRange[0]}`)) / 1000
          this.searchParams.time_end = (+new Date(`${this.dateTimeRange[1]}`)) / 1000
        })
      },

      handleTimeClear () {
        this.searchParams.time_start = ''
        this.searchParams.time_end = ''
      },

      handlePageLimitChange (limit) {
        this.pagination.limit = limit
        this.pagination.current = 1
        this.getApigwAlarms()
      },

      handlePageChange (newPage) {
        this.pagination.current = newPage
        this.getApigwAlarms()
      },

      clearFilterKey () {
        this.searchParams.alarm_strategy_id = ''
        this.searchParams.status = ''
        if (this.dateTimeRange.length) {
          this.handleTimeClear()
          this.dateTimeRange = []
        }
      },

      updateTableEmptyConfig () {
        const isEmpty = this.dateTimeRange.some(Boolean)
        if (this.searchParams.alarm_strategy_id || this.searchParams.status || isEmpty) {
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

    .status-text {
        vertical-align: middle;
    }

    .strategy-names {
        .ag-label {
            max-width: 180px;
        }
    }

    .ag-kv-list {
        .item {
            .value {
                pre {
                    margin: 0;
                    white-space: pre-wrap;
                }
            }
        }
    }
    .strategy-name-list {
        display: flex;
        align-items: center;
        flex-wrap: wrap;
        margin: 6px 0;
        .name-item {
            margin: 0 0 4px 0;
            line-height: 0;
            .ag-label {
                max-width: 300px;
            }
        }
    }
</style>
