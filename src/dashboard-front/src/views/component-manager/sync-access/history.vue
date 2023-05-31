<template>
  <div class="app-content apigw-access-manager-wrapper">
    <div class="wrapper">
      <bk-form form-type="inline">
        <bk-form-item :label="$t('选择时间')">
          <bk-date-picker
            ref="topDatePicker"
            style="width: 320px;"
            v-model="dateTimeRange"
            :placeholder="$t('选择日期时间范围')"
            :type="'datetimerange'"
            :shortcuts="datepickerShortcuts"
            :shortcut-close="true"
            :use-shortcut-text="true"
            :shortcut-selected-index="shortcutSelectedIndex"
            @shortcut-change="handleShortcutChange"
            @clear="handleTimeClear"
            @pick-success="handleTimeChange">
          </bk-date-picker>
        </bk-form-item>
      </bk-form>
      <ag-loader
        :offset-top="0"
        :offset-left="0"
        loader="stage-loader"
        :is-loading="false">
        <bk-table
          style="margin-top: 16px;"
          :data="componentList"
          size="small"
          :pagination="pagination"
          v-bkloading="{ isLoading, opacity: 1 }"
          @page-change="handlePageChange"
          @page-limit-change="handlePageLimitChange">
          <div slot="empty">
            <table-empty
              :keyword="tableEmptyConf.keyword"
              :abnormal="tableEmptyConf.isAbnormal"
              @reacquire="getComponents(true)"
              @clear-filter="clearFilterKey"
            />
          </div>
          <bk-table-column label="ID" prop="resource_version_title">
            <template slot-scope="{ row }">
              <bk-button theme="primary" class="mr10" text @click="handleVersion(row.id)">{{row.id || '--'}}</bk-button>
            </template>
          </bk-table-column>
          <bk-table-column :label="$t('同步时间')" prop="created_time" :render-header="$renderHeader"></bk-table-column>
          <bk-table-column :label="$t('同步版本号（版本标题）')" prop="resource_version_name" :render-header="$renderHeader">
            <template slot-scope="{ row }">
              {{row.resource_version_display || '--'}}
            </template>
          </bk-table-column>
          <bk-table-column :label="$t('操作人')" prop="component_name">
            <template slot-scope="{ row }">
              {{row.created_by || '--'}}
            </template>
          </bk-table-column>
          <bk-table-column :label="$t('操作结果')" :render-header="$renderHeader">
            <template slot-scope="props">
              <template v-if="props.row.status === 'releasing'">
                <round-loading />
                {{ $t('同步中') }}
              </template>
              <template v-else>
                <span :class="`ag-dot ${props.row.status} mr5`"></span> {{ statusMap[props.row.status] }}
              </template>
            </template>
          </bk-table-column>
          <bk-table-column :label="$t('操作日志')" prop="message" :render-header="$renderHeader"></bk-table-column>
        </bk-table>
      </ag-loader>
    </div>
  </div>
</template>
<script>
  import { catchErrorHandler } from '@/common/util'
  import { mapGetters } from 'vuex'
  import i18n from '@/language/i18n.js'

  const STATUS_MAP = {
    success: i18n.t('成功'),
    failure: i18n.t('失败'),
    pending: i18n.t('待同步'),
    releasing: i18n.t('同步中')
  }

  export default {
    name: '',
    components: {
    },
    data () {
      return {
        componentList: [],
        pagination: {
          current: 1,
          count: 0,
          limit: 10
        },
        requestQueue: ['component'],
        isLoading: false,
        dateTimeRange: [],
        shortcutSelectedIndex: -1,
        searchParams: { time_start: '', time_end: '' },
        statusMap: STATUS_MAP,
        tableEmptyConf: {
          keyword: '',
          isAbnormal: false
        }
      }
    },
    computed: {
      ...mapGetters('options', ['datepickerShortcuts'])
    },
    watch: {
      requestQueue (value) {
        if (value.length < 1) {
          this.$store.commit('setMainContentLoading', false)
        }
      }
    },
    created () {
      this.init()
    },
    methods: {
      init () {
        this.getComponents()
      },

      async getComponents (isLoading = false) {
        this.isLoading = isLoading
        this.setSearchTimeRange()
        const pageParams = {
          limit: this.pagination.limit,
          offset: this.pagination.limit * (this.pagination.current - 1),
          ...this.searchParams
        }
        try {
          const res = await this.$store.dispatch('component/getSyncHistory', { pageParams })
          this.pagination.count = res.data.count
          this.componentList = res.data.results
          this.updateTableEmptyConfig()
          this.tableEmptyConf.isAbnormal = false
        } catch (e) {
          this.tableEmptyConf.isAbnormal = true
          catchErrorHandler(e, this)
        } finally {
          if (this.requestQueue.length > 0) {
            this.requestQueue.shift()
          }
          this.isLoading = false
        }
      },

      setSearchTimeRange () {
        let timeRange = this.dateTimeRange

        // 选择的是时间快捷项，需要实时计算时间值
        if (this.shortcutSelectedIndex !== -1) {
          timeRange = this.datepickerShortcuts[this.shortcutSelectedIndex].value()
        }

        if (timeRange.length) {
          const formatTimeRange = this.formatDatetime(timeRange)
          this.searchParams.time_start = formatTimeRange[0] || ''
          this.searchParams.time_end = formatTimeRange[1] || ''
        }
      },

      formatDatetime (timeRange) {
        if (!timeRange[0] || !timeRange[1]) {
          return []
        }
        return [
          (+new Date(`${timeRange[0]}`)) / 1000,
          (+new Date(`${timeRange[1]}`)) / 1000
        ]
      },

      handlePageLimitChange (limit) {
        this.pagination.limit = limit
        this.pagination.current = 1
        this.getComponents()
      },

      handlePageChange (page) {
        this.pagination.current = page
        this.getComponents()
      },

      handleVersion (id) {
        this.$router.push({
          name: 'syncVersion',
          query: { id }
        })
      },
      handleShortcutChange (value, index) {
        this.shortcutSelectedIndex = index
      },
      handleTimeClear () {
        this.pagination.current = 1
        this.shortcutSelectedIndex = -1
        this.$nextTick(() => {
          this.getComponents()
        })
      },
      handleTimeChange () {
        this.pagination.current = 1
        this.$nextTick(() => {
          this.getComponents()
        })
      },
      clearFilterKey () {
        this.dateTimeRange = []
        this.$refs.topDatePicker && this.$refs.topDatePicker.handleClear()
      },
      updateTableEmptyConfig () {
        const isEmpty = this.dateTimeRange.some(Boolean)
        if (isEmpty) {
          this.tableEmptyConf.keyword = 'placeholder'
          return
        }
        this.tableEmptyConf.keyword = ''
      }
    }
  }
</script>
<style lang="postcss" scoped>
    .apigw-access-manager-wrapper {
        display: flex;
        justify-content: flex-start;
        .wrapper {
            padding: 0 10px;
            width: 100%
        }
        .search-wrapper {
            display: flex;
            justify-content: space-between;
        }
        .bk-table {
            .api-name,
            .docu-link {
                max-width: 200px;
                display: inline-block;
                word-break: break-all;
                overflow: hidden;
                white-space: nowrap;
                text-overflow: ellipsis;
                vertical-align: bottom;
            }
            .copy-icon {
                font-size: 14px;
                cursor: pointer;
                &:hover {
                    color: #3a84ff;
                }
            }
        }
    }
    .apigw-access-manager-slider-cls {
        .tips {
            line-height: 24px;
            font-size: 12px;
            color: #63656e;
            i {
                position: relative;
                top: -1px;
                margin-right: 3px;
            }
        }
        .timeout-append {
            width: 36px;
            font-size: 12px;
            text-align: center;
        }
    }

    .ag-flex {
        display: flex;
    }
    .ag-auto-text {
        vertical-align: middle;
    }
    .ag-tag.success {
        width: 44px;
    }
</style>
