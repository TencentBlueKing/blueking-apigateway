<template>
  <div class="app-content">
    <div class="ag-top-header">
      <span v-bk-tooltips="{ content: $t('请选择要审批的权限'), disabled: permissionTableSelection.length }">
        <bk-button theme="primary" :disabled="!permissionTableSelection.length" @click="handleBatchApply"> {{ $t('批量审批') }} </bk-button>
      </span>
      <bk-form class="fr" form-type="inline">
        <bk-form-item :label="$t('蓝鲸应用ID')">
          <bk-input
            :clearable="true"
            v-model="keyword"
            :placeholder="$t('请输入应用ID，按Enter搜索')"
            :right-icon="'bk-icon icon-search'"
            style="width: 190px;"
            @enter="handleSearch">
          </bk-input>
        </bk-form-item>
        <bk-form-item :label="$t('申请人')">
          <user
            style="width: 300px;"
            :max-data="1"
            v-model="searchParams.operator">
          </user>
        </bk-form-item>
      </bk-form>
    </div>
    <bk-table style="margin-top: 15px;"
      ref="permissionTable"
      class="ag-apply-table"
      :data="permissionApplyList"
      :size="'medium'"
      :pagination="pagination"
      v-bkloading="{ isLoading: isDataLoading }"
      @page-limit-change="handlePageLimitChange"
      @page-change="handlePageChange"
      @select="handlePageSelect"
      @selection-change="handlePageSelectionChange"
      @expand-change="handlePageExpandChange"
      @row-click="handleRowClick">
      <div slot="empty">
        <table-empty
          :keyword="tableEmptyConf.keyword"
          :abnormal="tableEmptyConf.isAbnormal"
          @reacquire="getApigwPermissionApplyList"
          @clear-filter="clearFilterKey"
        />
      </div>
      <bk-table-column type="selection" width="60" align="center"></bk-table-column>
      <bk-table-column type="expand" width="30" class="ag-expand-cell">
        <template slot-scope="props">
          <bk-table
            :ref="`permissionDetail_${props.row.id}`"
            :max-height="378"
            :size="'small'"
            :key="props.row.id"
            :data="props.row.components"
            :outer-border="false"
            :header-cell-style="{ background: '#fafbfd', borderRight: 'none' }"
            ext-cls="ag-expand-table"
            @selection-change="handleRowSelectionChange(props.row, ...arguments)">
            <div slot="empty">
              <table-empty empty />
            </div>
            <bk-table-column type="index" label="" width="60"></bk-table-column>
            <bk-table-column type="selection" width="50"></bk-table-column>
            <bk-table-column prop="name" :label="$t('组件名称')"></bk-table-column>
            <bk-table-column prop="description" :label="$t('组件描述')"></bk-table-column>
          </bk-table>
        </template>
      </bk-table-column>
      <bk-table-column :label="$t('蓝鲸应用ID')" prop="bk_app_code" :render-header="$renderHeader"></bk-table-column>
      <bk-table-column :label="$t('组件系统')" prop="system_name" :render-header="$renderHeader">
        <template slot-scope="props">
          <span>{{props.row.system_name || '--'}}</span>
        </template>
      </bk-table-column>
      <bk-table-column :label="$t('权限期限')" prop="expire_days_display" :render-header="$renderHeader">
        <template slot-scope="props">
          <span>{{props.row.expire_days ? getMonths(props.row.expire_days) : '--'}}</span>
        </template>
      </bk-table-column>
      <bk-table-column :label="$t('申请理由')" prop="reason" :render-header="$renderHeader">
        <template slot-scope="props">
          <span>{{props.row.reason || '--'}}</span>
        </template>
      </bk-table-column>
      <bk-table-column :label="$t('申请人')" prop="applied_by"></bk-table-column>
      <bk-table-column :label="$t('申请时间')" prop="applied_time" width="200" :show-overflow-tooltip="true" :render-header="$renderHeader"></bk-table-column>
      <bk-table-column :label="$t('审批状态')" prop="status" :render-header="$renderHeader">
        <template slot-scope="props">
          {{statusMap[props.row['apply_status']]}}
        </template>
      </bk-table-column>
      <bk-table-column :label="$t('操作')" width="200" :key="renderTableIndex">
        <template slot-scope="props">
          <bk-popover :content="$t('请选择组件')" v-if="expandRows.includes(props.row.id) && props.row.selection.length === 0">
            <bk-button class="mr10 is-disabled" theme="primary" text @click.stop.prevent="handlePrevent"> {{ $t('全部通过') }} </bk-button>
          </bk-popover>
          <bk-button class="mr10" theme="primary" v-else text @click.native.stop @click.native.prevent @click="handleApplyApprove(props.row)">{{props.row.isSelectAll ? $t('全部通过') : $t('部分通过')}}</bk-button>
          <bk-button theme="primary" text @click.native.stop @click.native.prevent @click="handleApplyReject(props.row)"> {{ $t('全部驳回') }} </bk-button>
          <!-- <bk-button class="mr10" theme="primary" text @click.native.stop @click.native.prevent @click="handleApplyApprove(props.row)">{{props.row.isSelectAll ? '全部通过' : $t('部分通过')}}</bk-button> -->
          <!-- <bk-button theme="primary" text @click.native.stop @click.native.prevent @click="handleApplyReject(props.row)"> {{ $t('全部驳回') }} </bk-button> -->
        </template>
      </bk-table-column>
    </bk-table>

    <bk-dialog
      v-model="batchApplyDialogConf.isShow"
      theme="primary"
      :mask-close="false"
      :width="670"
      :loading="batchApplyDialogConf.isLoading"
      :title="batchApplyDialogConfTitle">
      <div slot="footer">
        <bk-button theme="primary" @click="batchApprovePermission" :loading="curAction.status === 'approved' && batchApplyDialogConf.isLoading"> {{ $t('全部通过') }} </bk-button>
        <bk-button theme="default" @click="batchRejectPermission" :loading="curAction.status === 'rejected' && batchApplyDialogConf.isLoading"> {{ $t('全部驳回') }} </bk-button>
        <bk-button theme="default" @click="batchApplyDialogConf.isShow = false"> {{ $t('取消') }} </bk-button>
      </div>
      <div>
        <bk-table
          :data="permissionSelectList"
          :size="'small'"
          :max-height="200"
          :key="permissionSelectList.length">
          <div slot="empty">
            <table-empty empty />
          </div>
          <bk-table-column width="250" :label="$t('蓝鲸应用ID')" prop="bk_app_code" :render-header="$renderHeader"></bk-table-column>
          <bk-table-column :label="$t('申请人')" prop="applied_by"></bk-table-column>
          <bk-table-column :label="$t('申请时间')" prop="applied_time" :render-header="$renderHeader"></bk-table-column>
        </bk-table>
        <bk-form
          :label-width="0"
          :model="curAction"
          :rules="rules"
          ref="batchForm"
          class="mt20">
          <bk-form-item
            class="bk-hide-label"
            label=""
            :required="true"
            :property="'comment'">
            <bk-input
              type="textarea"
              :placeholder="$t('请输入备注')"
              v-model="curAction.comment"
              :maxlength="100">
            </bk-input>
          </bk-form-item>
        </bk-form>
      </div>
    </bk-dialog>

    <bk-dialog
      v-model="applyActionDialogConf.isShow"
      theme="primary"
      :width="600"
      :mask-close="false"
      :header-position="'left'"
      :title="applyActionDialogConf.title"
      :loading="applyActionDialogConf.isLoading"
      @confirm="handleSubmitApprove">
      <bk-form
        :label-width="90"
        :model="curAction"
        :rules="rules"
        ref="approveForm"
        class="mt10 mr20 mb20">
        <bk-form-item
          :label="$t('备注')"
          :required="true"
          :property="'comment'">
          <bk-alert class="mb10" type="warning" :title="approveFormMessage"></bk-alert>
          <bk-input
            type="textarea"
            :placeholder="$t('请输入备注')"
            v-model="curAction.comment"
            :rows="4"
            :maxlength="100">
          </bk-input>
        </bk-form-item>
      </bk-form>
    </bk-dialog>
  </div>
</template>

<script>
  import { catchErrorHandler } from '@/common/util'
  import User from '@/components/user'

  export default {
    components: {
      User
    },
    data () {
      return {
        keyword: '',
        isPageLoading: true,
        isDataLoading: false,
        permissionApplyList: [],
        pagination: {
          current: 1,
          count: 0,
          limit: 10
        },
        batchApplyDialogConf: {
          isLoading: false,
          isShow: false
        },
        permissionSelectList: [],
        permissionTableSelection: [],
        permissionRowSelection: [],
        renderTableIndex: 0,
        expandRows: [],
        curPermission: {
          bk_app_code: '',
          selection: [],
          components: []
        },
        rules: {
          comment: [
            {
              required: true,
              message: this.$t('必填项'),
              trigger: 'blur'
            }
          ]
        },
        searchParams: {
          bk_app_code: '',
          applied_by: '',
          operator: []
        },
        statusMap: {
          approved: this.$t('通过'),
          rejected: this.$t('驳回'),
          pending: this.$t('未审批')
        },
        applyActionDialogConf: {
          isShow: false,
          title: this.$t('通过申请'),
          isLoading: false
        },
        curAction: {
          ids: [],
          status: '',
          comment: ''
        },
        tableEmptyConf: {
          keyword: '',
          isAbnormal: false
        }
      }
    },
    computed: {
      approveFormMessage () {
        const selectLength = this.curPermission.selection.length
        const resourceLength = this.curPermission.components.length
        if (this.curAction.status === 'approved') {
          if (selectLength && selectLength < resourceLength) {
            const rejectLength = resourceLength - selectLength
            return this.$t(`应用{appCode} 申请{applyForLength}个权限，通过{selectLength}个，驳回{rejectLength}个`, { appCode: this.curPermission.bk_app_code, applyForLength: this.curPermission.components.length, selectLength, rejectLength })
          } else {
            return this.$t(`应用{appCode} 申请{applyForLength}个权限，全部通过`, { appCode: this.curPermission.bk_app_code, applyForLength: this.curPermission.components.length })
          }
        } else {
          return this.$t(`应用{appCode} 申请{applyForLength}个权限，全部驳回`, { appCode: this.curPermission.bk_app_code, applyForLength: this.curPermission.components.length })
        }
      },
      batchApplyDialogConfTitle () {
        return this.$t(`将对以下{permissionSelectListTemplate}个权限申请单进行审批`, { permissionSelectListTemplate: this.permissionSelectList.length })
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
          this.pagination.current = 1
          this.pagination.count = 0
          this.searchParams.applied_by = this.searchParams.operator.join(';')
          this.getApigwPermissionApplyList()
        }
      }
    },
    mounted () {
      this.init()
    },
    methods: {
      async init () {
        await this.getApigwPermissionApplyList()
      },

      async getApigwPermissionApplyList (page) {
        const curPage = page || this.pagination.current
        const pageParams = {
          limit: this.pagination.limit,
          offset: this.pagination.limit * (curPage - 1),
          bk_app_code: this.searchParams.bk_app_code,
          applied_by: this.searchParams.applied_by
        }
        this.isDataLoading = true
        try {
          const res = await this.$store.dispatch('componentPermission/getPermissionByPending', pageParams)
          this.permissionApplyList = this.initReourceList(res.data.results)
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

      initReourceList (permissionApplyList = []) {
        permissionApplyList.forEach(applyItem => {
          applyItem.isSelectAll = true
          applyItem.selection = []
        })
        return permissionApplyList
      },

      getMonths (payload) {
        return `${Math.ceil(payload / 30)} ${this.$t('个月')}`
      },

      handlePageLimitChange (limit) {
        this.pagination.limit = limit
        this.pagination.current = 1
        this.getApigwPermissionApplyList(this.pagination.current)
      },

      handlePageChange (newPage) {
        this.pagination.current = newPage
        this.getApigwPermissionApplyList(newPage)
      },

      handleSearch () {
        this.searchParams.bk_app_code = this.keyword
      },

      handleApplyApprove (data) {
        this.curPermission = data
        this.curAction = {
          ids: [data.id],
          status: 'approved',
          comment: this.$t('全部通过'),
          part_component_ids: {}
        }
        if (!this.curPermission.isSelectAll) {
          this.curAction.comment = this.$t('部分通过')
        } else {
          this.curAction.part_component_ids[data.id] = this.curPermission.components.map(item => item.id)
        }
        this.applyActionDialogConf.title = this.$t('通过申请')
        this.applyActionDialogConf.isShow = true
        this.$refs.approveForm.clearError()
      },

      handlePrevent () {
        return false
      },

      handleApplyReject (data) {
        this.curPermission = data
        this.curAction = {
          ids: [data.id],
          status: 'rejected',
          comment: this.$t('全部驳回')
        }
        this.applyActionDialogConf.title = this.$t('驳回申请')
        this.applyActionDialogConf.isShow = true
        this.$refs.approveForm.clearError()
      },

      handleBatchApply () {
        this.curAction = {
          ids: [],
          status: '',
          comment: ''
        }
        if (!this.permissionTableSelection.length) {
          this.$bkMessage({
            theme: 'error',
            message: this.$t('请选择要审批的权限')
          })
          return false
        }

        this.permissionSelectList = this.permissionTableSelection
        this.$refs.batchForm.clearError()
        this.batchApplyDialogConf.isShow = true
      },

      handlePageSelect (selection, row) {
        this.permissionTableSelection = selection
      },

      async batchApprovePermission () {
        if (this.batchApplyDialogConf.isLoading) {
          return false
        }
        this.batchApplyDialogConf.isLoading = true
        this.$refs.batchForm.validate().then(() => {
          this.curAction.ids = this.permissionSelectList.map(permission => permission.id)
          this.curAction.status = 'approved'
          this.updatePermissionStatus()
        }).catch(() => {
          this.$nextTick(() => {
            this.batchApplyDialogConf.isLoading = false
          })
        })
      },

      async batchRejectPermission () {
        if (this.batchApplyDialogConf.isLoading) {
          return false
        }
        this.batchApplyDialogConf.isLoading = true
        this.$refs.batchForm.validate().then(() => {
          this.curAction.ids = this.permissionSelectList.map(permission => permission.id)
          this.curAction.status = 'rejected'
          this.updatePermissionStatus()
        }).catch(() => {
          this.$nextTick(() => {
            this.batchApplyDialogConf.isLoading = false
          })
        })
      },

      async updatePermissionStatus () {
        const data = { ...this.curAction }

        // 部分通过
        if (data.status === 'approved' && this.permissionRowSelection.length && !this.curPermission.isSelectAll) {
          const id = data.ids[0]
          data.part_component_ids = {}
          data.status = 'partial_approved'
          data.part_component_ids[id] = this.permissionRowSelection.map(item => item.id)
        }

        try {
          await this.$store.dispatch('componentPermission/permApproval', data)

          // 当前页只有一条数据
          if (this.permissionApplyList.length === 1 && this.pagination.current > 1) {
            this.pagination.current--
          }

          this.$bkMessage({
            theme: 'success',
            message: this.$t('操作成功！')
          })

          this.applyActionDialogConf.isShow = false
          this.batchApplyDialogConf.isShow = false
          this.getApigwPermissionApplyList()
        } catch (e) {
          catchErrorHandler(e, this)
        } finally {
          this.applyActionDialogConf.isLoading = false
          this.batchApplyDialogConf.isLoading = false
        }
      },

      handleSubmitApprove () {
        if (this.applyActionDialogConf.isLoading) {
          return false
        }
        this.applyActionDialogConf.isLoading = true
        this.$refs.approveForm.validate().then(() => {
          this.updatePermissionStatus()
        }).catch(() => {
          this.$nextTick(() => {
            this.applyActionDialogConf.isLoading = false
          })
        })
      },

      handlePageExpandChange (row, expandedRows) {
        this.expandRows = expandedRows.map(item => {
          return item.id
        })
        if (this.curExpandRow !== row) {
          this.$refs.permissionTable.toggleRowExpansion(this.curExpandRow, false)
        }
        this.curExpandRow = row
        this.$nextTick(() => {
          const table = this.$refs[`permissionDetail_${row.id}`]
          if (table) {
            table.toggleAllSelection()
          }
        })
      },

      handlePageSelectionChange (selection) {
        this.permissionTableSelection = selection
      },

      handleRowSelectionChange (row, rowSelections) {
        this.permissionRowSelection = rowSelections
        row.selection = rowSelections
        if (rowSelections.length) {
          row.isSelectAll = row.components.length === rowSelections.length
        } else {
          row.isSelectAll = true
        }
        this.renderTableIndex++
      },

      handleRowClick (row) {
        this.$refs.permissionTable.toggleRowExpansion(row)
        this.curExpandRow = row
      },

      clearFilterKey () {
        this.keyword = ''
        this.searchParams.operator = []
      },

      updateTableEmptyConfig () {
        if (this.keyword || this.searchParams.operator.length) {
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

    /deep/ .bk-table-medium .cell {
        -webkit-line-clamp: 1 !important;
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
