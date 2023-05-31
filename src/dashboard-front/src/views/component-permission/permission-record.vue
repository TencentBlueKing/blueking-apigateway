<template>
  <div class="app-content">
    <div class="ag-top-header">
      <bk-form class="fl" form-type="inline">
        <bk-form-item :label="$t('选择时间')" class="ag-form-item-datepicker">
          <bk-date-picker
            style="width: 320px;"
            v-model="initDateTimeRange"
            :placeholder="$t('选择日期时间范围')"
            :type="'datetimerange'"
            :shortcuts="datepickerShortcuts"
            :shortcut-close="true"
            :use-shortcut-text="true"
            @clear="handleTimeClear"
            :shortcut-selected-index="shortcutSelectedIndex"
            @shortcut-change="handleShortcutChange"
            @pick-success="handleTimeChange">
          </bk-date-picker>
        </bk-form-item>
        <bk-form-item :label="$t('蓝鲸应用ID')">
          <bk-input
            :clearable="true"
            v-model="keyword"
            :placeholder="$t('请输入应用ID，按Enter搜索')"
            :right-icon="'bk-icon icon-search'"
            style="width: 250px;"
            @enter="handleSearch">
          </bk-input>
        </bk-form-item>
      </bk-form>
    </div>

    <bk-table
      style="margin-top: 15px;"
      class="ag-apply-table"
      ref="permissionTable"
      :data="permissionRecordList"
      :size="'medium'"
      :pagination="pagination"
      v-bkloading="{ isLoading: isDataLoading }"
      @page-limit-change="handlePageLimitChange"
      @page-change="handlePageChange"
      @expand-change="handlePageExpandChange"
      @row-click="handleRowClick">
      <div slot="empty">
        <table-empty
          :keyword="tableEmptyConf.keyword"
          :abnormal="tableEmptyConf.isAbnormal"
          @reacquire="getApigwPermissionRecordList"
          @clear-filter="clearFilterKey"
        />
      </div>
      <bk-table-column type="expand" width="30" class="ag-expand-cell">
        <template slot-scope="props">
          <bk-table
            :max-height="378"
            :ref="`permissionDetail_${props.row.id}`"
            :size="'small'"
            :data="props.row.components"
            :outer-border="false"
            :header-cell-style="{ background: '#fafbfd', borderRight: 'none' }"
            ext-cls="ag-expand-table">
            <div slot="empty">
              <table-empty empty />
            </div>
            <bk-table-column type="index" label="" width="60"></bk-table-column>
            <bk-table-column prop="name" :label="$t('组件名称')" :render-header="$renderHeader"></bk-table-column>
            <bk-table-column prop="description" :label="$t('组件描述')" :render-header="$renderHeader"></bk-table-column>
            <bk-table-column prop="method" :label="$t('审批状态')" :render-header="$renderHeader">
              <template slot-scope="prop">
                <template v-if="prop.row['apply_status'] === 'rejected'">
                  <span class="ag-dot default mr5 vm"></span> {{ $t('驳回') }}
                </template>
                <template v-else>
                  <span class="ag-dot success mr5 vm"></span> {{ $t('通过') }}
                </template>
              </template>
            </bk-table-column>
          </bk-table>
        </template>
      </bk-table-column>
      <bk-table-column :label="$t('蓝鲸应用ID')" prop="bk_app_code" :render-header="$renderHeader"></bk-table-column>
      <bk-table-column :label="$t('组件系统')" prop="system_name" :render-header="$renderHeader"></bk-table-column>
      <bk-table-column :label="$t('权限期限')" props="expire_days_display" :render-header="$renderHeader">
        <template slot-scope="props">
          <span>{{props.row.expire_days ? getMonths(props.row.expire_days) : '--'}}</span>
        </template>
      </bk-table-column>
      <bk-table-column :label="$t('申请人')" prop="applied_by"></bk-table-column>
      <bk-table-column width="200" :label="$t('审批时间')" prop="handled_time" :render-header="$renderHeader"></bk-table-column>
      <bk-table-column :label="$t('审批人')" prop="handled_by"></bk-table-column>
      <bk-table-column :label="$t('审批状态')" :render-header="$renderHeader">
        <template slot-scope="props">
          <span class="ag-dot default mr5 vm" v-if="props.row['apply_status'] === 'rejected'"></span>
          <span class="ag-dot success mr5 vm" v-else></span>
          {{statusMap[props.row.apply_status]}}
        </template>
      </bk-table-column>
      <bk-table-column :label="$t('操作')" width="100">
        <template slot-scope="props">
          <bk-button class="mr10" theme="primary" text @click.native.stop @click="handleShowRecord(props.row)"> {{ $t('详情') }} </bk-button>
        </template>
      </bk-table-column>
    </bk-table>

    <bk-sideslider
      :quick-close="true"
      :title="detailSliderConf.title"
      :width="650"
      :is-show.sync="detailSliderConf.isShow">
      <div slot="content" class="p30" v-bkloading="{ isLoading: detailSliderConf.loading }">
        <section class="ag-kv-list">
          <div class="item">
            <div class="key"> {{ $t('蓝鲸应用ID：') }} </div>
            <div class="value">{{curRecord.bk_app_code}}</div>
          </div>
          <div class="item">
            <div class="key"> {{ $t('申请人：') }} </div>
            <div class="value">{{curRecord.applied_by}}</div>
          </div>
          <div class="item">
            <div class="key"> {{ $t('权限期限：') }} </div>
            <div class="value">{{getMonths(curRecord.expire_days)}}</div>
          </div>
          <div class="item">
            <div class="key"> {{ $t('申请理由：') }} </div>
            <div class="value">{{curRecord.reason || '--'}}</div>
          </div>
          <div class="item">
            <div class="key"> {{ $t('申请时间：') }} </div>
            <div class="value">{{curRecord.applied_time}}</div>
          </div>
          <div class="item">
            <div class="key"> {{ $t('审批人：') }} </div>
            <div class="value">{{curRecord.handled_by.join('；')}}</div>
          </div>

          <div class="item">
            <div class="key"> {{ $t('审批时间：') }} </div>
            <div class="value">{{curRecord.handled_time}}</div>
          </div>

          <div class="item">
            <div class="key"> {{ $t('审批状态：') }} </div>
            <div class="value" style="line-height: 22px; padding-top: 10px">
              {{curRecord.apply_status_display}}
            </div>
          </div>

          <div class="item">
            <div class="key"> {{ $t('审批内容：') }} </div>
            <div class="value" style="line-height: 22px; padding-top: 10px">{{curRecord.comment}}</div>
          </div>

          <div class="item">
            <div class="key"> {{ $t('组件系统：') }} </div>
            <div class="value">{{curRecord.system_name}}</div>
          </div>
          <div class="item">
            <div class="key"> {{ $t('组件信息：') }} </div>
            <div class="value" style="line-height: 22px; padding-top: 10px">
              <bk-table
                :size="'small'"
                :data="curRecord.components"
                :header-cell-style="{ background: '#fafbfd', borderRight: 'none' }"
                ext-cls="ag-expand-table">
                <div slot="empty">
                  <table-empty empty />
                </div>
                <bk-table-column prop="name" :label="$t('组件名称')" :render-header="$renderHeader"></bk-table-column>
                <bk-table-column :label="$t('审批状态')" :render-header="$renderHeader">
                  <template slot-scope="prop">
                    <template v-if="prop.row['apply_status'] === 'rejected'">
                      <span class="ag-dot default mr5 vm"></span> {{ $t('驳回') }}
                    </template>
                    <template v-else>
                      <span class="ag-dot success mr5 vm"></span> {{ $t('通过') }}
                    </template>
                  </template>
                </bk-table-column>
              </bk-table>
            </div>
          </div>
        </section>
      </div>
    </bk-sideslider>
  </div>
</template>

<script>
  import { mapGetters } from 'vuex'
  import { catchErrorHandler } from '@/common/util'

  export default {
    data () {
      return {
        keyword: '',
        isPageLoading: true,
        isDataLoading: false,
        permissionRecordList: [],
        shortcutSelectedIndex: -1,
        pagination: {
          current: 1,
          count: 0,
          limit: 10
        },
        curRecord: {
          bk_app_code: '',
          applied_by: '',
          applied_time: '',
          handled_by: [],
          handled_time: '',
          status: '',
          comment: ''
        },
        searchParams: {
          bk_app_code: '',
          time_start: '',
          time_end: ''
        },
        statusMap: {
          approved: this.$t('全部通过'),
          partial_approved: this.$t('部分通过'),
          rejected: this.$t('全部驳回'),
          pending: this.$t('未审批')
        },
        detailSliderConf: {
          title: '',
          isShow: false,
          loading: false
        },
        initDateTimeRange: [],
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
      keyword (newVal, oldVal) {
        if (oldVal && !newVal) {
          this.handleSearch()
        }
      },
      searchParams: {
        deep: true,
        handler () {
          this.pagination.current = 1
          this.pagination.count = 0
          this.getApigwPermissionRecordList()
        }
      }
    },
    created () {
      this.init()
    },
    methods: {
      init () {
        this.getApigwPermissionRecordList()
      },

      async getApigwPermissionRecordList (page) {
        const curPage = page || this.pagination.current
        let pageParams = {
          limit: this.pagination.limit,
          offset: this.pagination.limit * (curPage - 1),
          bk_app_code: this.searchParams.bk_app_code,
          handled_time_start: this.searchParams.time_start,
          handled_time_end: this.searchParams.time_end
        }

        // 选择的是时间快捷项，需要实时计算时间值
        if (this.shortcutSelectedIndex !== -1) {
          const searchTimeRange = this.getSearchTimeRange()
          pageParams = { ...pageParams, ...searchTimeRange }
        }

        this.isDataLoading = true
        try {
          const res = await this.$store.dispatch('componentPermission/getPermissionByHandled', pageParams)
          res.data.results.forEach(item => {
            const hasApprovedItem = item.components.find(resource => resource.apply_status === 'approved')
            const hasRejectedItem = item.components.find(resource => resource.apply_status === 'rejected')

            if (hasApprovedItem && !hasRejectedItem) {
              item.statusText = this.$t('全部通过')
            } else if (hasApprovedItem && hasRejectedItem) {
              item.statusText = this.$t('部分通过')
            } else if (!hasApprovedItem && hasRejectedItem) {
              item.statusText = this.$t('全部驳回')
            } else {
              item.statusText = '--'
            }

            (item.components || []).forEach(subItem => {
              subItem.description = subItem.description || '--'
            })
          })
          this.permissionRecordList = res.data.results
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

      getSearchTimeRange () {
        const timeRange = this.datepickerShortcuts[this.shortcutSelectedIndex].value()
        return {
          time_start: parseInt((+new Date(timeRange[0])) / 1000),
          time_end: parseInt((+new Date(timeRange[1])) / 1000)
        }
      },

      getMonths (payload) {
        return `${Math.ceil(payload / 30)} ${this.$t('个月')}`
      },

      handlePageLimitChange (limit) {
        this.pagination.limit = limit
        this.pagination.current = 1
        this.getApigwPermissionRecordList(this.pagination.current)
      },

      handlePageChange (newPage) {
        this.pagination.current = newPage
        this.getApigwPermissionRecordList(newPage)
      },

      handleSearch () {
        this.searchParams.bk_app_code = this.keyword
      },

      handleTimeChange () {
        this.$nextTick(() => {
          this.searchParams.time_start = parseInt((+new Date(`${this.initDateTimeRange[0]}`)) / 1000)
          this.searchParams.time_end = parseInt((+new Date(`${this.initDateTimeRange[1]}`)) / 1000)
        })
      },

      handleShortcutChange (value, index) {
        this.shortcutSelectedIndex = index
      },

      handleTimeClear () {
        this.shortcutSelectedIndex = -1
        this.searchParams.time_start = ''
        this.searchParams.time_end = ''
      },

      handlePageExpandChange (row, expandedRows) {
        if (this.curExpandRow !== row) {
          this.$refs.permissionTable.toggleRowExpansion(this.curExpandRow, false)
        }
        this.curExpandRow = row
      },

      handleShowRecord (data) {
        this.detailSliderConf.title = `${this.$t('申请应用：')}${data.bk_app_code}`
        this.detailSliderConf.isShow = true
        this.getPermissionRecord(data.id)
      },

      async getPermissionRecord (id) {
        this.detailSliderConf.loading = true
        try {
          const res = await this.$store.dispatch('componentPermission/getPermissionRecord', { id })
          this.curRecord = Object.assign({}, res.data)
        } catch (e) {
          catchErrorHandler(e, this)
        } finally {
          this.detailSliderConf.loading = false
        }
      },

      handleRowClick (row) {
        this.$refs.permissionTable.toggleRowExpansion(row)
        this.curExpandRow = row
      },

      clearFilterKey () {
        this.keyword = ''
        this.initDateTimeRange = []
        this.handleTimeClear()
      },

      updateTableEmptyConfig () {
        const isEmpty = this.initDateTimeRange.some(Boolean)
        if (isEmpty || this.keyword) {
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

    .ag-resource-radio {
        label {
            display: block;
            margin-bottom: 10px;
        }
    }

    .ag-transfer-box {
        padding: 20px;
        background: #FAFBFD;
        border: 1px solid #F0F1F5;
        border-radius: 2px;
    }

    .ag-dl {
        padding: 15px 40px 5px 30px;
    }

    .ag-link {
        .apigateway-icon {
            cursor: pointer;
            color: #737987;
            font-size: 16px;
            margin-left: 5px;
        }
    }

    .ag-user-type {
        width: 560px;
        height: 80px;
        background: #FAFBFD;
        border-radius: 2px;
        border: 1px solid #DCDEE5;
        padding: 17px 20px 0 20px;
        position: relative;
        overflow: hidden;

        .apigateway-icon {
            font-size: 80px;
            position: absolute;
            color: #ECF2FC;
            top: 15px;
            right: 20px;
            z-index: 0;
        }

        strong {
            font-size: 14px;
            margin-bottom: 10px;
            line-height: 1;
            display: block;
        }

        p {
            font-size: 12px;
            color: #63656E;
        }
    }
</style>
