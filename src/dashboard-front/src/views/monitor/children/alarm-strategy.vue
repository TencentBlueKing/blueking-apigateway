<template>
  <div class="alarm-strategy">
    <div class="ag-top-header">
      <bk-button theme="primary" @click="handleCreate"> {{ $t('新建') }} </bk-button>
      <bk-input
        class="fr mr10"
        :clearable="true"
        v-model="keyword"
        :placeholder="$t('请输入告警策略名称，按Enter搜索')"
        :right-icon="'bk-icon icon-search'"
        style="width: 240px;"
        @enter="handleSearch">
      </bk-input>
    </div>
    <bk-table
      ref="tableRef"
      :data="table.list"
      :size="'small'"
      :pagination="pagination"
      v-bkloading="{ isLoading: isDataLoading }"
      v-if="!pageLoading"
      @filter-change="handleFilterChange"
      @page-limit-change="handlePageLimitChange"
      @page-change="handlePageChange">
      <div slot="empty">
        <table-empty
          :keyword="tableEmptyConf.keyword"
          :abnormal="tableEmptyConf.isAbnormal"
          @reacquire="getApigwAlarmStrategies"
          @clear-filter="clearFilterKey"
        />
      </div>
      <bk-table-column :label="$t('告警策略名称')" prop="name" :render-header="$renderHeader"></bk-table-column>
      <bk-table-column
        :label="$t('标签')"
        column-key="label"
        prop="api_label_names"
        :filters="tagFilters"
        :filter-multiple="false"
        :show-overflow-tooltip="false">
        <template slot-scope="props">
          <template v-if="props.row.api_label_names.length">
            <div class="pt5" style="display: inline-block;" v-bk-tooltips.top="props.row.labelText.join('; ')">
              <template v-for="(label, index) of props.row.api_label_names">
                <span class="ag-label vm mb5" v-if="index < 4" :key="index">
                  {{label}}
                </span>
              </template>
              <template v-if="props.row.api_label_names.length > 4">
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
      <bk-table-column :label="$t('是否启用')" width="200" prop="type">
        <template slot-scope="{ row }">
          <bk-switcher
            v-model="row.enabled"
            theme="primary"
            :disabled="statusSwitcherDisabled"
            @change="(enabled) => handleChangeStatus(enabled, row)">
          </bk-switcher>
        </template>
      </bk-table-column>
      <bk-table-column :label="$t('更新时间')" width="300" prop="updated_time"></bk-table-column>
      <bk-table-column :label="$t('操作')" width="200">
        <template slot-scope="{ row }">
          <bk-button
            class="mr10"
            theme="primary"
            text
            @click="handleEdit(row)">
            {{ $t('编辑') }}
          </bk-button>
          <bk-button
            theme="primary"
            text
            @click="handleDelete(row)">
            {{ $t('删除') }}
          </bk-button>
        </template>
      </bk-table-column>
    </bk-table>

    <bk-sideslider
      :title="slider.title"
      :width="750"
      :is-show.sync="slider.isShow"
      :quick-close="true"
      :before-close="handleBeforeClose">
      <div slot="content" class="p30">
        <alarm-strategy-form
          ref="alarmStrategyFormRef"
          :strategy="slider.data"
          @save-success="handleSaveSuccess"
          @cancel="handleFormCancel"
          @init-data="initEditData">
        </alarm-strategy-form>
      </div>
    </bk-sideslider>

    <bk-dialog v-model="deleteDialog.isShow"
      theme="primary"
      :loading="deleteDialog.loading"
      :width="525"
      :title="`${$t('确定要删除告警策略')}【${deleteDialog.data.name}】？`"
      :mask-close="true"
      @cancel="deleteDialog.isShow = false"
      @confirm="handleConfirmDelete">
      <p class="tc p10"> {{ $t('策略删除后，将不再接收相关通知') }} </p>
    </bk-dialog>
  </div>
</template>

<script>
  import { catchErrorHandler, clearFilter } from '@/common/util'
  import AlarmStrategyForm from './alarm-strategy-form'
  import sidebarMixin from '@/mixins/sidebar-mixin'

  export default {
    components: {
      AlarmStrategyForm
    },
    mixins: [sidebarMixin],
    props: {
      pageLoading: {
        type: Boolean,
        default: false
      }
    },
    data () {
      return {
        keyword: '',
        isDataLoading: false,
        statusSwitcherDisabled: false,
        labelList: [],
        filterLabel: '',
        table: {
          list: [],
          fields: [],
          headers: []
        },
        slider: {
          isShow: false,
          title: '',
          data: {}
        },
        pagination: {
          current: 1,
          count: 0,
          limit: 10
        },
        deleteDialog: {
          isShow: false,
          loading: false,
          data: {}
        },
        tableEmptyConf: {
          keyword: '',
          isAbnormal: false
        }
      }
    },
    computed: {
      apigwId () {
        return this.$route.params.id
      },
      tagFilters () {
        const labels = this.labelList.map(item => {
          return {
            value: item.id,
            text: item.name
          }
        })
        return labels
      }
    },
    watch: {
      keyword (newVal, oldVal) {
        if (oldVal && !newVal) {
          this.handleSearch()
        }
      },
      filterLabel () {
        this.handleSearch()
      }
    },
    created () {
      this.getApigwAlarmStrategies()
      this.getApigwLabels()
    },
    methods: {
      async getApigwAlarmStrategies () {
        const apigwId = this.apigwId
        const params = {
          offset: (this.pagination.current - 1) * this.pagination.limit,
          limit: this.pagination.limit,
          query: this.keyword
        }

        if (this.filterLabel) {
          params['api_label_id'] = this.filterLabel
        }

        this.isDataLoading = true

        try {
          const res = await this.$store.dispatch('monitor/getApigwAlarmStrategies', { apigwId, params })
          res.data.results.forEach(item => {
            item.labelText = item.api_label_names.map(label => label)
          })
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

      async getApigwLabels () {
        const apigwId = this.apigwId
        const pageParams = {
          no_page: true,
          order_by: 'name'
        }

        try {
          const res = await this.$store.dispatch('label/getApigwLabels', { apigwId, pageParams })
          this.labelList = res.data.results
        } catch (e) {
          catchErrorHandler(e, this)
        }
      },

      handleSearch (event) {
        this.pagination.current = 1
        this.pagination.count = 0
        this.getApigwAlarmStrategies()
      },

      async handleChangeStatus (enabled, { id }) {
        const apigwId = this.apigwId
        const data = { enabled }
        this.statusSwitcherDisabled = true
        try {
          await this.$store.dispatch('monitor/updateApigwAlarmStrategyStatus', { apigwId, id, data })
        } catch (e) {
          catchErrorHandler(e, this)
        } finally {
          this.statusSwitcherDisabled = false
        }
      },

      async handleConfirmDelete () {
        try {
          const apigwId = this.apigwId
          const { id } = this.deleteDialog.data
          this.deleteDialog.loading = true
          await this.$store.dispatch('monitor/deleteApigwAlarmStrategy', { apigwId, id })
          // 当前页只有一条数据
          if (this.table.list.length === 1 && this.pagination.current > 1) {
            this.pagination.current--
          }
          this.getApigwAlarmStrategies()

          this.$bkMessage({
            theme: 'success',
            message: this.$t('删除成功！')
          })
          this.deleteDialog.isShow = false
        } catch (e) {
          catchErrorHandler(e, this)
        } finally {
          this.deleteDialog.loading = false
        }
      },

      handleSaveSuccess () {
        this.getApigwAlarmStrategies()
        this.slider.isShow = false
      },

      handleFilterChange (filters) {
        if (filters.label) {
          this.filterLabel = filters.label[0] ? filters.label[0] : ''
        }
      },

      handleFormCancel () {
        this.slider.isShow = false
      },

      handleDelete (row) {
        this.deleteDialog.isShow = true
        this.deleteDialog.data = row
      },

      handleEdit (row) {
        this.slider.isShow = true
        this.slider.title = this.$t('编辑告警策略')
        this.slider.data = row
      },

      handleCreate () {
        this.slider.isShow = true
        this.slider.title = this.$t('新建告警策略')
        this.slider.data = {}
        this.$nextTick(() => {
          if (this.$refs.alarmStrategyFormRef) {
            this.initSidebarFormData(this.$refs.alarmStrategyFormRef.formData || {})
          }
        })
      },

      handlePageLimitChange (limit) {
        this.pagination.limit = limit
        this.pagination.current = 1
        this.getApigwAlarmStrategies()
      },

      handlePageChange (newPage) {
        this.pagination.current = newPage
        this.getApigwAlarmStrategies()
      },

      clearFilterKey () {
        this.keyword = ''
        this.$refs.tableRef.clearFilter()
        if (this.$refs.tableRef && this.$refs.tableRef.$refs.tableHeader) {
          clearFilter(this.$refs.tableRef.$refs.tableHeader)
        }
      },

      updateTableEmptyConfig () {
        if (this.keyword || this.filterLabel) {
          this.tableEmptyConf.keyword = 'placeholder'
          return
        }
        this.tableEmptyConf.keyword = ''
      },

      // 编辑收集状态
      initEditData (data) {
        this.initSidebarFormData(data || {})
      },

      async handleBeforeClose () {
        return this.$isSidebarClosed(JSON.stringify(this.$refs.alarmStrategyFormRef.formData || {}))
      }
    }
  }
</script>

<style lang="postcss" scoped>
</style>
