<template>
  <div class="app-content">
    <div class="ag-top-header">
      <bk-form class="search-form" form-type="inline">
        <bk-form-item :label="$t('选择时间')" class="ag-form-item-datepicker top-form-item-time">
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
        <bk-form-item :label="$t('操作对象')" class="top-form-item-object-type">
          <bk-select
            style="width: 150px;"
            v-model="searchParams.op_object_type"
            searchable
            @selected="handleObjectTypeChange">
            <bk-option v-for="option in auditOptions.OPObjectType"
              :key="option.value"
              :id="option.value"
              :name="option.name">
            </bk-option>
          </bk-select>
        </bk-form-item>
        <bk-form-item :label="$t('操作类型')" :class="{ 'top-form-item-input': localLanguage === 'en' }">
          <bk-select
            style="width: 150px;"
            v-model="searchParams.op_type"
            @selected="handleOpTypeChange">
            <bk-option v-for="option in auditOptions.OPType"
              :key="option.value"
              :id="option.value"
              :name="option.name">
            </bk-option>
          </bk-select>
        </bk-form-item>
        <bk-form-item :label="$t('操作人')" class="top-form-item-input">
          <user
            ref="topMemberSelector"
            class="member-selector"
            :max-data="1"
            v-model="members"
            @change="handleFilterMemeberChange">
          </user>
        </bk-form-item>
        <bk-button theme="primary" class="ml10 top-search-button" :disabled="isDataLoading" @click="handleReSearch"> {{ $t('刷新') }} </bk-button>
        <bk-button theme="default" class="ml10 top-clear-button" :disabled="isDataLoading" @click="handleClearSearch"> {{ $t('清空') }} </bk-button>
      </bk-form>
    </div>
    <bk-table
      :data="table.list"
      :size="'small'"
      :pagination="pagination"
      v-bkloading="{ isLoading: isDataLoading }"
      @page-limit-change="handlePageLimitChange"
      @page-change="handlePageChange">
      <div slot="empty">
        <table-empty
          :keyword="tableEmptyConf.keyword"
          :abnormal="tableEmptyConf.isAbnormal"
          @reacquire="getAuditLogList"
          @clear-filter="clearFilterKey"
        />
      </div>
      <bk-table-column :label="$t('网关')" :show-overflow-tooltip="true">
        <template slot-scope="{}">
          {{currentApigwName}}
        </template>
      </bk-table-column>
      <bk-table-column :label="$t('时间')" prop="op_time" :show-overflow-tooltip="true"></bk-table-column>
      <bk-table-column :label="$t('操作类型')" :render-header="$renderHeader">
        <template slot-scope="{ row }">
          {{getOpTypeText(row.op_type)}}
        </template>
      </bk-table-column>
      <bk-table-column :label="$t('操作对象')" width="300" :show-overflow-tooltip="false" :render-header="$renderHeader">
        <template slot-scope="{ row }">
          <div class="cell-field">
            <span class="label"> {{ $t('类型') }}： </span>
            <span class="content">{{getOpObjectTypeText(row.op_object_type)}}</span>
          </div>
          <div class="cell-field">
            <span class="label"> {{ $t('对象') }}： </span>
            <span class="content" v-bk-overflow-tips>{{row.op_object}}</span>
          </div>
        </template>
      </bk-table-column>
      <bk-table-column :label="$t('状态')">
        <template slot-scope="{ row }">
          <span :class="['ag-dot', row.op_status]"></span>
          <span class="status-text">{{getStatusText(row.op_status)}}</span>
        </template>
      </bk-table-column>
      <bk-table-column :label="$t('操作者')" prop="username" :show-overflow-tooltip="true"></bk-table-column>
      <bk-table-column :label="$t('描述')" prop="comment" :show-overflow-tooltip="true"></bk-table-column>
    </bk-table>
  </div>
</template>

<script>
  import { mapGetters, mapState } from 'vuex'
  import { catchErrorHandler } from '@/common/util'
  import User from '@/components/user'

  const defalutSearchParams = {
    op_object_type: '',
    op_type: '',
    username: '',
    time_start: '',
    time_end: ''
  }

  export default {
    components: {
      User
    },
    data () {
      return {
        isPageLoading: true,
        dateTimeRange: [],
        members: [],
        shortcutSelectedIndex: -1,
        isDataLoading: false,
        table: {
          list: []
        },
        pagination: {
          current: 1,
          count: 0,
          limit: 10
        },
        searchParams: { ...defalutSearchParams },
        tableEmptyConf: {
          keyword: '',
          isAbnormal: false
        }
      }
    },
    computed: {
      ...mapGetters('options', ['datepickerShortcuts', 'auditOptions']),
      ...mapState('apis', ['apigwList']),
      apigwId () {
        return this.$route.params.id
      },
      currentApigwName () {
        const current = this.apigwList.find(item => item.id === Number(this.apigwId)) || {}
        return current.name || ''
      },
      localLanguage () {
        return this.$store.state.localLanguage
      }
    },
    created () {
      this.getAuditLogList()
    },
    methods: {
      async getAuditLogList () {
        const apigwId = this.apigwId
        this.setSearchTimeRange()
        const params = {
          ...this.searchParams,
          offset: (this.pagination.current - 1) * this.pagination.limit,
          limit: this.pagination.limit
        }
        this.isDataLoading = true
        try {
          const res = await this.$store.dispatch('audit/getApigwAuditLogs', { apigwId, params })
          this.table.list = res.data.results
          this.pagination.count = res.data.count
          this.updateTableEmptyConfig()
          this.tableEmptyConf.isAbnormal = false
        } catch (e) {
          this.tableEmptyConf.isAbnormal = true
          catchErrorHandler(e, this)
        } finally {
          this.isPageLoading = false
          this.isDataLoading = false
          this.$store.commit('setMainContentLoading', false)
        }
      },
      getStatusText (key) {
        const status = { success: this.$t('成功'), fail: this.$t('失败'), unknown: this.$t('未知') }
        return status[key]
      },
      getOpTypeText (type) {
        return (this.auditOptions.OPType.find(item => item.value === type) || {}).name
      },
      getOpObjectTypeText (type) {
        return (this.auditOptions.OPObjectType.find(item => item.value === type) || {}).name
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
      handleFilterMemeberChange (data) {
        this.pagination.current = 1
        this.searchParams.username = data && data[0]
        this.getAuditLogList()
      },
      handleObjectTypeChange (value) {
        this.pagination.current = 1
        this.getAuditLogList()
      },
      handleOpTypeChange (value) {
        this.pagination.current = 1
        this.getAuditLogList()
      },
      handleTimeChange () {
        this.pagination.current = 1
        this.$nextTick(() => {
          this.getAuditLogList()
        })
      },
      handleTimeClear () {
        this.pagination.current = 1
        this.shortcutSelectedIndex = -1
        this.$nextTick(() => {
          this.getAuditLogList()
        })
      },
      handlePageLimitChange (limit) {
        this.pagination.limit = limit
        this.pagination.current = 1
        this.getAuditLogList()
      },
      handlePageChange (newPage) {
        this.pagination.current = newPage
        this.getAuditLogList()
      },
      handleShortcutChange (value, index) {
        this.shortcutSelectedIndex = index
      },
      handleReSearch () {
        this.getAuditLogList()
      },
      handleClearSearch () {
        this.searchParams = { ...defalutSearchParams }
        this.shortcutSelectedIndex = -1
        this.dateTimeRange = []
        this.members = []
        this.getAuditLogList()
        this.$nextTick(() => {
          this.$refs.topDatePicker.$el.querySelector('.bk-date-picker-editor').value = ''
        })
      },
      clearFilterKey () {
        this.members = []
        this.searchParams.op_object_type = ''
        if (this.searchParams.op_type) {
          this.searchParams.op_type = ''
          this.getAuditLogList()
        }
        if (this.dateTimeRange.length) {
          this.dateTimeRange = []
          this.handleTimeClear()
        }
      },
      updateTableEmptyConfig () {
        // 判断时间是否有值
        const isEmpty = this.dateTimeRange.some(Boolean)
        if (this.searchParams.op_type || this.searchParams.op_object_type || this.members.length || isEmpty) {
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

    .cell-field {
        display: flex;

        .label {
            flex: none;
            color: #979ba5;
        }
        .content {
            flex: 1;
            white-space: nowrap;
            text-overflow: ellipsis;
            overflow: hidden;
        }
    }

    .search-form {
        width: 100%;

        .member-selector {
            width: 180px;
        }
    }

    @media (max-width: 1660px) {
        .search-form {
            width: 870px;

            /deep/ .bk-form-item.top-form-item-input {
                margin-top: 10px !important;
            }

            .member-selector {
                width: 320px;
            }

            .top-search-button,
            .top-clear-button {
                margin-top: 10px;
            }
        }
    }
</style>
