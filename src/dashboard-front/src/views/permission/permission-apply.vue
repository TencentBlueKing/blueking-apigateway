<template>
  <div class="app-content">
    <div class="ag-top-header">
      <span v-bk-tooltips="{ content: $t('请选择要审批的权限'), disabled: permissionTableSelection.length }">
        <bk-button theme="primary" :disabled="!permissionTableSelection.length" @click="handleBatchApply"> {{ $t('批量审批') }} </bk-button>
      </span>
      <bk-form class="fr" form-type="inline">
        <bk-form-item :label="$t('授权维度')">
          <bk-select
            v-model="searchParams.dimension"
            style="width: 150px;">
            <bk-option
              v-for="option of dimensionList"
              :key="option.id"
              :id="option.id"
              :name="option.name">
            </bk-option>
          </bk-select>
        </bk-form-item>
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
          <div class="bk-alert m20 bk-alert-error" v-if="props.row.grant_dimension === 'api'" style="display: block; text-align: center; line-height: 60px;">
            <div class="bk-alert-wraper">
              <i class="bk-icon icon-info" style="display: inline-block; margin-right: 1px;"></i>
              <div class="bk-alert-content" style="display: inline-block;">
                <div class="bk-alert-title">
                  {{ $t('将申请网关下所有资源的权限，包括未来新创建的资源，请谨慎审批') }}
                </div>
              </div>
            </div>
          </div>
          <bk-table
            v-else
            :ref="`permissionDetail_${props.row.id}`"
            :max-height="378"
            :size="'small'"
            :key="props.row.id"
            :data="props.row.resourceList"
            :outer-border="false"
            :header-cell-style="{ background: '#fafbfd', borderRight: 'none' }"
            ext-cls="ag-expand-table"
            @selection-change="handleRowSelectionChange(props.row, ...arguments)">
            <div slot="empty">
              <table-empty empty />
            </div>
            <bk-table-column type="index" label="" width="60"></bk-table-column>
            <bk-table-column type="selection" width="50"></bk-table-column>
            <bk-table-column prop="name" :label="$t('资源名称')" :render-header="$renderHeader"></bk-table-column>
            <bk-table-column prop="path" :label="$t('请求路径')" :render-header="$renderHeader"></bk-table-column>
            <bk-table-column prop="method" :label="$t('请求方法')" :render-header="$renderHeader"></bk-table-column>
          </bk-table>
        </template>
      </bk-table-column>
      <bk-table-column :label="$t('蓝鲸应用ID')" prop="bk_app_code" :render-header="$renderHeader"></bk-table-column>
      <bk-table-column :label="$t('授权维度')" prop="grant_dimension_display" :render-header="$renderHeader">
        <template slot-scope="props">
          <span>{{props.row.grant_dimension_display || '--'}}</span>
        </template>
      </bk-table-column>
      <bk-table-column :label="$t('权限期限')" prop="expire_days_display" :render-header="$renderHeader">
        <template slot-scope="props">
          <span>{{props.row.expire_days_display || '--'}}</span>
        </template>
      </bk-table-column>
      <bk-table-column :label="$t('申请理由')" prop="reason" :render-header="$renderHeader">
        <template slot-scope="props">
          <span>{{props.row.reason || '--'}}</span>
        </template>
      </bk-table-column>
      <bk-table-column :label="$t('申请人')" prop="applied_by"></bk-table-column>
      <bk-table-column :label="$t('申请时间')" prop="created_time" :render-header="$renderHeader"></bk-table-column>
      <bk-table-column :label="$t('审批状态')" prop="status" :render-header="$renderHeader">
        <template slot-scope="props">
          {{statusMap[props.row['status']]}}
        </template>
      </bk-table-column>
      <bk-table-column :label="$t('操作')" width="200" :key="renderTableIndex">
        <template slot-scope="props">
          <!-- 按网关，不需要选择对应资源 -->
          <bk-popover :content="$t('请选择资源')" v-if="expandRows.includes(props.row.id) && props.row.selection.length === 0 && props.row.grant_dimension !== 'api'">
            <bk-button class="mr10 is-disabled" theme="primary" text @click.stop.prevent="handlePrevent"> {{ $t('全部通过') }} </bk-button>
          </bk-popover>
          <bk-button class="mr10" v-else theme="primary" text @click.stop.prevent="handleApplyApprove(props)">{{props.row.isSelectAll ? $t('全部通过') : $t('部分通过')}}</bk-button>
          <bk-button theme="primary" text @click.stop.prevent="handleApplyReject(props.row)"> {{ $t('全部驳回') }} </bk-button>
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
          <bk-table-column :label="$t('申请时间')" prop="created_time" :render-header="$renderHeader"></bk-table-column>
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
          <bk-alert class="mb10" :type="alertType" :title="approveFormMessage"></bk-alert>
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

    <bk-sideslider
      :quick-close="true"
      :title="detailSliderConf.title"
      :width="600"
      :is-show.sync="detailSliderConf.isShow">
      <div slot="content" class="p30">
        <section class="ag-kv-list" style="margin-bottom: 70px;">
          <div class="item">
            <div class="key"> {{ $t('蓝鲸应用ID：') }} </div>
            <div class="value">{{curApply.bk_app_code}}</div>
          </div>
          <div class="item">
            <div class="key"> {{ $t('申请人：') }} </div>
            <div class="value">{{curApply.applied_by}}</div>
          </div>
          <div class="item">
            <div class="key"> {{ $t('申请时间：') }} </div>
            <div class="value">{{curApply.created_time}}</div>
          </div>
          <div class="item">
            <div class="key"> {{ $t('审批状态：') }} </div>
            <div class="value">{{statusMap[curApply['status']]}}</div>
          </div>
          <div class="item">
            <div class="key"> {{ $t('资源信息：') }} </div>
            <div class="value" style="line-height: 22px; padding-top: 10px">
              <bk-table style="margin-top: 5px;"
                :data="curApply.resourceList"
                :size="'small'">
                <div slot="empty">
                  <table-empty empty />
                </div>
                <bk-table-column :label="$t('请求路径')" prop="path" :render-header="$renderHeader"></bk-table-column>
                <bk-table-column :label="$t('请求方法')" prop="method" :render-header="$renderHeader"></bk-table-column>
              </bk-table>
              <div class="ag-alert warning mt10" v-if="curApply.resourceList.length && curApply.resourceList.length > curApply.resource_ids.length">
                <i class="apigateway-icon icon-ag-info"></i>
                <p> {{ $t('部分资源已被删除') }} </p>
              </div>
              <div class="ag-alert warning mt10" v-if="!curApply.resourceList.length && curApply.resource_ids.length">
                <i class="apigateway-icon icon-ag-info"></i>
                <p> {{ $t('资源已被删除') }} </p>
              </div>
            </div>
          </div>
        </section>

        <div class="bk-sideslider-footer">
          <bk-button theme="primary" class="mr15" @click="handleApplyApprove(curApply)"> {{ $t('通过') }} </bk-button>
          <bk-button @click="handleApplyReject(curApply)"> {{ $t('驳回') }} </bk-button>
        </div>
      </div>
    </bk-sideslider>
  </div>
</template>

<script>
  import { catchErrorHandler, sortByKey } from '@/common/util'
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
        curExpandedRow: null,
        pagination: {
          current: 1,
          count: 0,
          limit: 10
        },
        batchApplyDialogConf: {
          isLoading: false,
          isShow: false
        },
        resourceSourceList: [],
        resourceTargetList: [],
        permissionSelectList: [],
        permissionTableSelection: [],
        permissionRowSelection: [],
        expandRows: [],
        renderTableIndex: 0,
        curApply: {
          bk_app_code: '',
          expire_type: 'None',
          expire_days: '',
          resource_ids: [],
          dimension: 'api',
          resourceList: []
        },
        curPermission: {
          bk_app_code: '',
          resourceList: [],
          selection: []
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

        grantTypes: [
          {
            id: 'initialize',
            name: this.$t('主动授权')
          },
          {
            id: 'apply',
            name: this.$t('申请审批')
          }
        ],
        dimensionList: [
          {
            id: 'api',
            name: this.$t('按网关')
          },
          {
            id: 'resource',
            name: this.$t('按资源')
          }
        ],
        searchParams: {
          dimension: '',
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
        detailSliderConf: {
          title: '',
          isShow: false
        },
        resourceList: [],
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
      approveFormMessage () {
        const selectLength = this.curPermission.selection.length
        const resourceLength = this.curPermission.resourceList.length
        if (this.curPermission.grant_dimension === 'api') {
          if (this.curAction.status === 'approved') {
            return `${this.$t('应用将申请网关下所有资源的权限，包括未来新创建的资源，请谨慎审批')}`
          } else {
            return `${this.$t('应用将按网关申请全部驳回')}`
          }
        } else {
          if (this.curAction.status === 'approved') {
            if (selectLength && selectLength < resourceLength) {
              const rejectLength = resourceLength - selectLength
              return this.$t(`应用{appCode} 申请{applyForLength}个权限，通过{selectLength}个，驳回{rejectLength}个`, { appCode: this.curPermission.bk_app_code, applyForLength: this.curPermission.resourceList.length, selectLength, rejectLength })
            } else {
              return this.$t(`应用{appCode} 申请{applyForLength}个权限，全部通过`, { appCode: this.curPermission.bk_app_code, applyForLength: this.curPermission.resourceList.length })
            }
          } else {
            return this.$t(`应用{appCode} 申请{applyForLength}个权限，全部驳回`, { appCode: this.curPermission.bk_app_code, applyForLength: this.curPermission.resourceList.length })
          }
        }
      },
      batchApplyDialogConfTitle () {
        return this.$t(`将对以下{permissionSelectListTemplate}个权限申请单进行审批`, { permissionSelectListTemplate: this.permissionSelectList.length })
      },
      alertType () {
        if (this.curPermission.grant_dimension === 'api') {
          return this.curAction.status === 'approved' ? 'warning' : 'error'
        }
        return 'warning'
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
        this.getApigwResources(() => {
          this.getApigwPermissionApplyList()
        })
      },

      async getApigwPermissionApplyList (page) {
        const apigwId = this.apigwId
        const curPage = page || this.pagination.current
        const pageParams = {
          limit: this.pagination.limit,
          offset: this.pagination.limit * (curPage - 1),
          bk_app_code: this.searchParams.bk_app_code,
          applied_by: this.searchParams.applied_by,
          grant_dimension: this.searchParams.dimension
        }

        this.isDataLoading = true
        try {
          const res = await this.$store.dispatch('permission/getApigwPermissionApplyList', { apigwId, pageParams })
          res.data.results.forEach(item => {
            item.updated_time = item.updated_time || '--'
          })

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
          const results = []
          applyItem.resourceList = []
          applyItem.isSelectAll = true
          applyItem.selection = []
          applyItem.resource_ids.forEach(resourceId => {
            this.resourceList.forEach(item => {
              if (item.id === resourceId) {
                results.push(item)
              }
            })
          })
          applyItem.resourceList = sortByKey(results, 'path')
        })
        return permissionApplyList
      },

      handlePrevent () {
        return false
      },

      async getApigwResources (callback) {
        const apigwId = this.apigwId
        const pageParams = {
          no_page: true,
          order_by: 'name'
        }

        try {
          const res = await this.$store.dispatch('resource/getApigwResources', { apigwId, pageParams })
          this.resourceList = res.data.results
          callback && callback()
        } catch (e) {
          catchErrorHandler(e, this)
        }
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

      handleSearch (event) {
        this.searchParams.bk_app_code = this.keyword
      },

      handleApplyApprove (props) {
        const data = props.row
        console.log(props.store.states.expandRows)
        this.curPermission = data
        this.curAction = {
          ids: [data.id],
          status: 'approved',
          comment: this.$t('全部通过')
        }
        if (!this.curPermission.isSelectAll) {
          this.curAction.comment = this.$t('部分通过')
        }
        this.applyActionDialogConf.title = this.$t('通过申请')
        this.applyActionDialogConf.isShow = true
        this.$refs.approveForm.clearError()
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
          this.permissionRowSelection.isSelectAll = true
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
          this.permissionRowSelection.isSelectAll = true
          this.updatePermissionStatus()
        }).catch(() => {
          this.$nextTick(() => {
            this.batchApplyDialogConf.isLoading = false
          })
        })
      },

      async updatePermissionStatus () {
        const apigwId = this.apigwId
        const data = { ...this.curAction }

        // 部分通过
        const id = data.ids[0]
        if (data.status === 'approved' && this.expandRows.includes(id) && this.permissionRowSelection.length && !this.permissionRowSelection.isSelectAll) {
          data.part_resource_ids = {}
          data.status = 'partial_approved'
          data.part_resource_ids[id] = this.permissionRowSelection.map(item => item.id)
        }

        try {
          await this.$store.dispatch('permission/updateApigwPermissionStatus', { apigwId, data })

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
          this.detailSliderConf.isShow = false
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

      handleShowRecord (data) {
        this.curApply = data
        this.detailSliderConf.title = `${this.$t('申请应用：')}${data.bk_app_code}`
        this.curApply.resourceList = []

        const results = []

        this.curApply.resource_ids.forEach(resourceId => {
          this.resourceList.forEach(item => {
            if (item.id === resourceId) {
              results.push(item)
            }
          })
        })
        this.curApply.resourceList = sortByKey(results, 'path')
        this.detailSliderConf.isShow = true
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
          row.isSelectAll = row.resourceList.length === rowSelections.length
        } else {
          row.isSelectAll = true
        }
        this.permissionRowSelection.isSelectAll = row.isSelectAll
        this.renderTableIndex++
      },

      handleRowClick (row) {
        this.$refs.permissionTable.toggleRowExpansion(row)
        this.curExpandedRow = row
      },

      handleDimensionChange () {
        this.handleSearch()
      },

      clearFilterKey () {
        this.keyword = ''
        this.searchParams.operator = []
        this.searchParams.dimension = ''
      },

      updateTableEmptyConfig () {
        if (this.keyword || this.searchParams.operator.length || this.searchParams.dimension) {
          this.tableEmptyConf.keyword = 'Placeholder'
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
