<template>
  <div class="app-content">
    <div class="ag-top-header release-header-wrapper">
      <bk-form form-type="inline" ext-cls="release-form-cls">
        <bk-form-item :label="$t('环境')">
          <bk-select
            style="width: 130px;"
            v-model="searchParams.stage_id"
            clearable
            searchable>
            <bk-option v-for="option in stageList"
              :key="option.id"
              :id="option.id"
              :name="option.name">
            </bk-option>
          </bk-select>
        </bk-form-item>
        <bk-form-item :label="$t('操作人')">
          <user
            style="width: 155px;"
            :max-data="1"
            v-model="searchParams.operator">
          </user>
        </bk-form-item>
        <bk-form-item :label="$t('选择时间')" class="ag-form-item-datepicker">
          <bk-date-picker
            class="ag-picker"
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
      </bk-form>
      <bk-input
        class="ml18"
        :clearable="true"
        v-model="keyword"
        :placeholder="$t('请输入环境、版本标题或版本号，按Enter搜索')"
        :right-icon="'bk-icon icon-search'"
        style="max-width: 370px;"
        @enter="handleSearch">
      </bk-input>
    </div>
    <bk-table style="margin-top: 15px;"
      :data="releaseHistory"
      :size="'small'"
      :pagination="pagination"
      v-bkloading="{ isLoading: isDataLoading }"
      v-if="!isPageLoading"
      @page-limit-change="handlePageLimitChange"
      @page-change="handlePageChange">
      <div slot="empty">
        <table-empty
          :keyword="releaseHistoryEmptyConf.keyword"
          :abnormal="releaseHistoryEmptyConf.isAbnormal"
          @reacquire="getApigwReleaseHistory"
          @clear-filter="clearFilterKey"
        />
      </div>
      <bk-table-column :label="$t('环境')">
        <template slot-scope="props">
          {{props.row.stage_names.join(',')}}
        </template>
      </bk-table-column>
      <bk-table-column width="200" :label="$t('发布时间')" prop="created_time" :render-header="$renderHeader"></bk-table-column>
      <bk-table-column :label="$t('发布日志')" :render-header="$renderHeader">
        <template slot-scope="props">
          <template v-if="props.row.comment">
            <span>
              {{props.row.comment}}
            </span>
          </template>
          <template v-else>
            --
          </template>
        </template>
      </bk-table-column>
      <bk-table-column width="300" :label="$t('版本号 (版本标题)')" :render-header="$renderHeader">
        <span class="ag-auto-text" slot-scope="props">
          {{props.row.resource_version_display || '--'}}
        </span>
      </bk-table-column>
      <bk-table-column :label="$t('操作人')" prop="created_by"></bk-table-column>
      <bk-table-column :label="$t('操作结果')" :render-header="$renderHeader">
        <template slot-scope="props">
          <template v-if="props.row.status === 'success'">
            <span class="ag-dot success mr5"></span> {{ $t('成功') }}
          </template>
          <template v-else-if="props.row.status === 'pending'">
            <span class="ag-dot primary mr5"></span> {{ $t('待发布') }}
          </template>
          <template v-else-if="props.row.status === 'releasing'">
            <round-loading />
            {{ $t('发布中') }}
          </template>
          <template v-else>
            <span class="ag-dot danger mr5"></span> {{ $t('失败') }}
          </template>
        </template>
      </bk-table-column>
      <bk-table-column :label="$t('操作日志')" prop="message" :render-header="$renderHeader"></bk-table-column>
    </bk-table>
  </div>
</template>

<script>
  import { mapGetters } from 'vuex'
  import { catchErrorHandler } from '@/common/util'
  import User from '@/components/user'

  export default {
    components: {
      User
    },
    data () {
      return {
        keyword: '',
        time: ['00:00:00', '23:59:59'],
        isPageLoading: true,
        isDataLoading: false,
        releaseHistory: [],
        shortcutSelectedIndex: -1,
        pagination: {
          current: 1,
          count: 0,
          limit: 10
        },
        detailSidesliderConf: {
          isShow: false
        },
        initDateTimeRange: [],
        searchParams: {
          stage_id: '',
          operator: [],
          time_start: '',
          time_end: '',
          created_by: '',
          query: ''
        },
        stageList: [],
        releaseHistoryDialogConf: {
          isLoading: false,
          visiable: false,
          title: this.$t('新建标签')
        },
        curVersion: {
          name: ''
        },
        rules: {
          name: [
            {
              required: true,
              message: this.$t('必填项'),
              trigger: 'blur'
            },
            {
              max: 32,
              message: this.$t('不能多于32个字符'),
              trigger: 'blur'
            }
          ]
        },
        releaseHistoryEmptyConf: {
          keyword: '',
          isAbnormal: false
        }
      }
    },
    computed: {
      ...mapGetters('options', ['datepickerShortcuts']),
      apigwId () {
        return this.$route.params.id
      }
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
          this.getApigwReleaseHistory()
        }
      }
    },
    created () {
      this.init()
    },
    methods: {
      init () {
        this.getApigwReleaseHistory()
        this.getApigwStages()
      },

      async getApigwReleaseHistory (page) {
        const apigwId = this.apigwId
        const curPage = page || this.pagination.current
        this.searchParams.created_by = this.searchParams.operator.join(';')
        let pageParams = {
          limit: this.pagination.limit,
          offset: this.pagination.limit * (curPage - 1),
          name: this.keyword,
          ...this.searchParams
        }

        // 选择的是时间快捷项，需要实时计算时间值
        if (this.shortcutSelectedIndex !== -1) {
          const searchTimeRange = this.getSearchTimeRange()
          pageParams = { ...pageParams, ...searchTimeRange }
        }

        this.isDataLoading = true
        try {
          const res = await this.$store.dispatch('release/getApigwReleaseHistory', { apigwId, pageParams })
          res.data.results.forEach(item => {
            item.updated_time = item.updated_time || '--'
          })
          this.releaseHistory = res.data.results
          this.pagination.count = res.data.count
          this.updateTableEmptyConfig()
          this.releaseHistoryEmptyConf.isAbnormal = false
        } catch (e) {
          this.releaseHistoryEmptyConf.isAbnormal = true
          catchErrorHandler(e, this)
        } finally {
          this.isPageLoading = false
          this.isDataLoading = false
          this.$store.commit('setMainContentLoading', false)
        }
      },

      async getApigwStages (page) {
        const apigwId = this.apigwId
        const pageParams = {
          no_page: true,
          order_by: 'name'
        }

        try {
          const res = await this.$store.dispatch('stage/getApigwStages', { apigwId, pageParams })
          this.stageList = res.data.results
        } catch (e) {
          catchErrorHandler(e, this)
        }
      },

      getSearchTimeRange () {
        const timeRange = this.datepickerShortcuts[this.shortcutSelectedIndex].value()
        return {
          time_start: parseInt((+new Date(timeRange[0])) / 1000),
          time_end: parseInt((+new Date(timeRange[1])) / 1000)
        }
      },

      handlePageLimitChange (limit) {
        this.pagination.limit = limit
        this.pagination.current = 1
        this.getApigwReleaseHistory(this.pagination.current)
      },

      handlePageChange (newPage) {
        this.pagination.current = newPage
        this.getApigwReleaseHistory(newPage)
      },

      handleSearch () {
        this.searchParams.query = this.keyword
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

      clearFilterKey () {
        this.keyword = ''
        this.searchParams.stage_id = ''
        this.searchParams.operator = []
        if (this.initDateTimeRange.length) {
          this.handleTimeClear()
          this.initDateTimeRange = []
        }
      },

      updateTableEmptyConfig () {
        // 判断时间是否有值
        const isEmpty = this.initDateTimeRange.some(Boolean)
        if (this.keyword || this.searchParams.operator.length || this.searchParams.stage_id || isEmpty) {
          this.releaseHistoryEmptyConf.keyword = 'placeholder'
          return
        }
        this.releaseHistoryEmptyConf.keyword = ''
      }
    }
  }
</script>

<style lang="postcss" scoped>
    @import '@/css/variable.css';

    .ag-dl {
        padding: 15px 40px 5px 30px;
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

    .release-header-wrapper {
        display: flex;
        flex-wrap: nowrap;
        justify-content: space-between;

        .ml18 {
            margin-left: 8px;
        }

        .release-form-cls {
            display: flex;
            flex-wrap: nowrap;

            /deep/ .bk-form-item {
                display: flex;
                flex-wrap: nowrap;

                label {
                    white-space: nowrap;
                }
            }
        }
    }
</style>
