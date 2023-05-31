<template>
  <div class="app-content">
    <div class="ag-top-header">
      <span v-bk-tooltips="{ content: $t('请选择待续期的权限'), disabled: permissionTableSelection.length }">
        <bk-button theme="primary" class="mr10 fl" :disabled="!permissionTableSelection.length" @click="handleBatchApply"> {{ $t('批量续期') }} </bk-button>
      </span>
      <bk-form class="fr" form-type="inline">
        <bk-form-item label="">
          <bk-search-select
            style="width: 500px;"
            :placeholder="$t('搜索')"
            :show-popover-tag-change="true"
            :clearable="true"
            :data="searchResourceCondition"
            :show-condition="false"
            v-model="searchFilters"
            @change="formatFilterData">
          </bk-search-select>
        </bk-form-item>
      </bk-form>
    </div>
    <bk-table style="margin-top: 15px;"
      :data="permissionList"
      :size="'small'"
      :pagination="pagination"
      v-bkloading="{ isLoading: isDataLoading }"
      @page-limit-change="handlePageLimitChange"
      @page-change="handlePageChange"
      @select="handlePageSelect"
      @select-all="handlePageSelectAll">
      <div slot="empty">
        <table-empty
          :keyword="tableEmptyConf.keyword"
          :abnormal="tableEmptyConf.isAbnormal"
          @reacquire="getApigwPermissionList"
          @clear-filter="clearFilterKey"
        />
      </div>
      <bk-table-column type="selection" width="60" align="center"></bk-table-column>
      <bk-table-column :label="$t('蓝鲸应用ID')" prop="bk_app_code" :render-header="$renderHeader"></bk-table-column>
      <bk-table-column :label="$t('组件系统')" prop="system_name" :render-header="$renderHeader"></bk-table-column>
      <bk-table-column :label="$t('组件名称')" prop="component_name" :render-header="$renderHeader"></bk-table-column>
      <bk-table-column :label="$t('组件描述')" prop="component_description" :render-header="$renderHeader"></bk-table-column>
      <bk-table-column :label="$t('过期时间')" prop="expires" :render-header="$renderHeader">
        <template slot-scope="props">
          {{props.row['expires'] || $t('永久有效')}}
        </template>
      </bk-table-column>
      <bk-table-column width="150" :label="$t('操作')">
        <template slot-scope="props">
          <template v-if="props.row.renewable">
            <bk-button class="mr10" theme="primary" text @click="handleSingleApply(props.row)"> {{ $t('续期') }} </bk-button>
          </template>
          <template v-else>
            <span v-bk-tooltips.left="$t('权限有效期大于 30 天时，暂无法续期')"><bk-button class="mr10" theme="primary" text disabled> {{ $t('续期') }} </bk-button></span>
          </template>
          <bk-button theme="primary" text @click="handleRemove(props.row)"> {{ $t('删除') }} </bk-button>
        </template>
      </bk-table-column>
    </bk-table>

    <bk-dialog
      v-model="batchApplyDialogConf.isShow"
      theme="primary"
      :width="800"
      :title="$t('批量续期')"
      :mask-close="true"
      @cancel="batchApplyDialogConf.isShow = false">
      <div>
        <div class="ag-alert primary mb10">
          <i class="apigateway-icon icon-ag-info"></i>
          <p v-html="templateString"></p>
        </div>
        <bk-table
          :data="permissionSelectList"
          :size="'small'"
          :max-height="250"
          :key="applyKey">
          <div slot="empty">
            <table-empty empty />
          </div>
          <bk-table-column width="180" :label="$t('蓝鲸应用ID')" prop="bk_app_code" :render-header="$renderHeader"></bk-table-column>
          <bk-table-column :label="$t('组件名称')" prop="component_name" :render-header="$renderHeader"></bk-table-column>
          <bk-table-column :label="$t('续期前的过期时间')" prop="expires" :render-header="$renderHeader">
            <template slot-scope="props">
              {{props.row['expires'] || '--'}} <span class="ag-strong default fn" v-if="!props.row.renewable && props.row['expires']"> {{ $t('(有效期大于30天)') }} </span>
            </template>
          </bk-table-column>
          <bk-table-column width="180" :label="$t('续期后的过期时间')" prop="expires" :render-header="$renderHeader">
            <template slot-scope="props">
              <span class="ag-strong danger fn" v-if="!props.row.renewable"> {{ $t('不可续期') }} </span>
              <span v-else class="ag-strong warning fn">{{applyNewTime}}</span>
            </template>
          </bk-table-column>
        </bk-table>
      </div>
      <template slot="footer">
        <template v-if="applyCount">
          <bk-button theme="primary" :disabled="applyCount === 0" @click="batchApplyPermission" :loading="isBatchApplyLoaading"> {{ $t('确定') }} </bk-button>
        </template>
        <template v-else>
          <bk-popover placement="top" :content="$t('无可续期的权限')">
            <bk-button theme="primary" :disabled="true"> {{ $t('确定') }} </bk-button>
          </bk-popover>
        </template>
        <bk-button theme="default" @click="batchApplyDialogConf.isShow = false"> {{ $t('取消') }} </bk-button>
      </template>
    </bk-dialog>

    <!-- <bk-sideslider
            :title="applySliderConf.title"
            :width="800"
            :is-show.sync="applySliderConf.isShow">
            <div slot="content" class="p30">
                <p class="ag-span-title">你将对指定的蓝鲸应用添加访问资源的权限</p>
                <bk-form class="mb30 ml15" :label-width="100" :model="curIPGroup">
                    <bk-form-item
                        :label="$t('蓝鲸应用ID')"
                        :required="true">
                        <bk-input
                            placeholder="请输入应用ID"
                            v-model="curApply.bk_app_code"
                            style="width: 256px;">
                        </bk-input>
                    </bk-form-item>
                    <bk-form-item
                        label="有效时间"
                        :required="true">
                        <bk-radio-group v-model="curApply.expire_type">
                            <bk-radio :value="'custom'" style="margin-right: 65px;">
                                <bk-input
                                    type="number"
                                    :min="0"
                                    v-model="curApply.expire_days"
                                    class="mr5"
                                    :show-controls="false"
                                    style="width: 68px; display: inline-block;"
                                    @focus="curApply.expire_type = 'custom'">
                                </bk-input>
                                天
                            </bk-radio>
                            <bk-radio :value="'None'">永久有效</bk-radio>
                        </bk-radio-group>
                    </bk-form-item>
                </bk-form>
                <p class="ag-span-title">请选择要授权的资源</p>
                <div class="ml20">
                    <bk-radio-group class="ag-resource-radio" v-model="curApply.dimension">
                        <bk-radio :value="'api'">所有资源</bk-radio>
                        <bk-radio :value="'resource'">
                            部分资源
                        </bk-radio>
                    </bk-radio-group>

                    <div class="ag-transfer-box" v-if="curApply.dimension === 'resource'">
                        <bk-transfer
                            :source-list="resourceList"
                            :display-key="'name'"
                            :setting-key="'id'"
                            :title="['未选资源', '已选资源']"
                            :searchable="true"
                            @change="handleResourceChange">
                        </bk-transfer>
                    </div>

                    <div class="action mt20">
                        <bk-button theme="primary" class="mr10" @click="submitApigwApply">保存</bk-button>
                        <bk-button @click="handleHideApplySlider"> {{ $t('取消') }} </bk-button>
                    </div>
                </div>
            </div>
        </bk-sideslider> -->

    <bk-dialog
      v-model="removeDialogConf.isShow"
      theme="primary"
      :width="940"
      :title="removeDialogConfTitle"
      :mask-close="true"
      @cancel="removeDialogConf.isShow = false"
      @confirm="removePermission">
      <div>
        <bk-table style="margin-top: 15px;"
          :data="curPermission.details"
          :size="'small'"
          :key="tableIndex">
          <div slot="empty">
            <table-empty empty />
          </div>
          <bk-table-column :label="$t('蓝鲸应用ID')" prop="bk_app_code"></bk-table-column>
          <bk-table-column :label="$t('组件系统')" prop="system_name"></bk-table-column>
          <bk-table-column :label="$t('组件名称')" prop="component_name"></bk-table-column>
        </bk-table>
      </div>
    </bk-dialog>
  </div>
</template>

<script>
  import { catchErrorHandler } from '@/common/util'
  import dayjs from 'dayjs'

  export default {
    data () {
      return {
        searchResourceCondition: [
          {
            name: this.$t('蓝鲸应用ID'),
            id: 'bk_app_code',
            children: []
          },
          {
            name: this.$t('组件系统'),
            id: 'system_id',
            children: []
          },
          {
            name: this.$t('组件名称'),
            id: 'component_id',
            children: []
          }
        ],
        applyNewTime: '',
        searchFilters: [],
        keyword: '',
        isPageLoading: true,
        isDataLoading: false,
        isBatchApplyLoaading: false,
        permissionList: [],
        pagination: {
          current: 1,
          count: 0,
          limit: 10
        },
        isExportDropdownShow: false,
        applySliderConf: {
          isLoading: false,
          isShow: false,
          title: this.$t('主动授权')
        },
        resourceList: [],
        batchApplyDialogConf: {
          isShow: false
        },
        resourceSourceList: [],
        resourceTargetList: [],
        permissionSelectList: [],
        permissionTableSelection: [],
        applyKey: 0,
        curApply: {
          bk_app_code: '',
          expire_type: 'custom',
          expire_days: 180,
          resource_ids: [],
          dimension: 'api'
        },
        curPermission: {
          bk_app_code: ''
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
        searchParams: {
          bk_app_code: '',
          system_id: '',
          component_id: ''
        },
        removeDialogConf: {
          isShow: false
        },
        tableIndex: 0,
        tableEmptyConf: {
          keyword: '',
          isAbnormal: false
        }
      }
    },
    computed: {
      apigwId () {
        return this.$route.params.id || 3
      },
      hasSelected () {
        return this.permissionTableSelection.length > 0
      },
      applyCount () {
        return this.permissionSelectList.filter(item => item.renewable).length
      },
      unApplyCount () {
        return this.permissionSelectList.filter(item => !item.renewable).length
      },
      templateString () {
        return this.$t(`将给以下  <i class="ag-strong success m5">{applyCount}</i> 个权限续期<i class="ag-strong">180</i>天<span v-if="unApplyCount">；<i class="ag-strong danger m5">{unApplyCount}</i> 个权限不可续期，权限大于30天不支持续期</span>`, { applyCount: this.applyCount, unApplyCount: this.unApplyCount })
      },
      removeDialogConfTitle () {
        return this.$t(`确定要删除蓝鲸应用【{appCode}】的权限？`, { appCode: this.curPermission.bk_app_code })
      }
    },
    watch: {
      keyword (newVal, oldVal) {
        if (oldVal && !newVal) {
          this.handleSearch()
        }
      },
      searchParams: {
        handler () {
          this.pagination.current = 1
          this.pagination.count = 0
          this.getApigwPermissionList()
        },
        immediate: true,
        deep: true
      },
      searchFilters () {
        this.$nextTick(() => {
          if (this.searchFilters.length < 1) {
            this.searchParams = {
              bk_app_code: '',
              system_id: '',
              component_id: ''
            }
            return
          }
          this.searchFilters.forEach(item => {
            this.searchParams[item.id] = item.values[0].id
          })
        })
      },
      'curApply.expire_type' (value) {
        if (value === 'custom') {
          this.curApply.expire_days = 180
        } else {
          this.curApply.expire_days = ''
        }
      }
    },
    created () {
      this.init()
    },
    methods: {
      init () {
        this.getApigwPermissionList()
        this.getSystems()
        this.getComponents()
      },

      async getSystems () {
        try {
          const res = await this.$store.dispatch('system/getSystems')
          this.searchResourceCondition[1].children = res.data.map(item => {
            return {
              id: item.id,
              name: item.name
            }
          })
        } catch (e) {
          catchErrorHandler(e, this)
        }
      },

      async getComponents () {
        try {
          const res = await this.$store.dispatch('component/getComponents')
          this.searchResourceCondition[2].children = res.data.map(item => {
            return {
              id: item.id,
              name: item.name
            }
          })
        } catch (e) {
          catchErrorHandler(e, this)
        }
      },

      async getApigwPermissionList (page) {
        const curPage = page || this.pagination.current
        const pageParams = {
          limit: this.pagination.limit,
          offset: this.pagination.limit * (curPage - 1),
          ...this.searchParams
        }

        this.isDataLoading = true
        this.permissionTableSelection = []
        try {
          const res = await this.$store.dispatch('componentPermission/getPermissions', pageParams)
          this.permissionList = res.data.results
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

      handlePageLimitChange (limit) {
        this.pagination.limit = limit
        this.pagination.current = 1
        this.getApigwPermissionList(this.pagination.current)
      },

      handlePageChange (newPage) {
        this.pagination.current = newPage
        this.getApigwPermissionList(newPage)
      },

      async addPermissionApply (data) {
        try {
          const apigwId = this.apigwId
          await this.$store.dispatch('permission/addApigwPermissionApply', { apigwId, data })

          this.searchParams.dimension = data.dimension
          this.getApigwPermissionList()
          this.$bkMessage({
            theme: 'success',
            message: this.$t('授权成功！')
          })
          this.handleHideApplySlider()
        } catch (e) {
          catchErrorHandler(e, this)
        }
      },

      async updatePermission () {
        try {
          const data = { name: this.curPermission.name }
          const apigwId = this.apigwId
          const permissionId = this.curPermission.id
          await this.$store.dispatch('permission/updateApigwPermission', { apigwId, permissionId, data })
          this.permissionDialogConf.visiable = false
          this.getApigwPermissionList()

          this.$bkMessage({
            theme: 'success',
            message: this.$t('更新成功！')
          })
        } catch (e) {
          catchErrorHandler(e, this)
        }
      },

      async removePermission () {
        try {
          const ids = [this.curPermission.id]

          const data = {
            ids: ids
          }

          await this.$store.dispatch('componentPermission/permDelete', data)

          // 当前页只有一条数据
          if (this.permissionList.length === 1 && this.pagination.current > 1) {
            this.pagination.current--
          }
          this.getApigwPermissionList()

          this.$bkMessage({
            theme: 'success',
            message: this.$t('删除成功！')
          })
        } catch (e) {
          catchErrorHandler(e, this)
        }
      },

      formatFilterData () {
        const map = {}
        this.searchFilters.forEach(filter => {
          map[filter.id] = filter
        })
        const keys = Object.keys(map)
        this.searchFilters = []
        keys.forEach(key => {
          this.searchFilters.push(map[key])
        })
      },

      handleSearch () {
        this.searchParams.bk_app_code = this.keyword
      },

      handleRemove (data) {
        this.curPermission = data
        this.curPermission.details = [data]
        this.tableIndex++
        this.removeDialogConf.isShow = true
      },

      submitApigwApply () {
        const params = this.formatData()

        if (this.checkData(params)) {
          this.addPermissionApply(params)
        }
      },

      checkData (params) {
        const codeReg = /^[a-z][a-z0-9-_]+$/

        if (!params.bk_app_code) {
          this.$bkMessage({
            theme: 'error',
            message: this.$t('请输入蓝鲸应用ID')
          })
          return false
        }

        if (!codeReg.test(params.bk_app_code)) {
          this.$bkMessage({
            theme: 'error',
            delay: 5000,
            message: this.$t('蓝鲸应用ID格式不正确，只能包含：小写字母、数字、连字符(-)、下划线(_)，首字母必须是字母')
          })
          return false
        }

        if (params.expire_type === 'custom' && !params.expire_days) {
          this.$bkMessage({
            theme: 'error',
            message: this.$t('请输入有效时间')
          })
          return false
        }

        if (params.dimension === 'resource' && !params.resource_ids.length) {
          this.$bkMessage({
            theme: 'error',
            message: this.$t('请选择要授权的资源')
          })
          return false
        }
        return true
      },

      formatData () {
        const params = JSON.parse(JSON.stringify(this.curApply))
        if (params.expire_type === 'None') {
          params.expire_days = null
        }

        if (params.dimension === 'api') {
          params.resource_ids = null
        }

        return params
      },

      handleResourceChange (sourceList, targetList, targetValueList) {
        this.curApply.resource_ids = targetValueList
      },

      handleHideApplySlider () {
        this.curApply = {
          bk_app_code: '',
          expire_type: 'custom',
          expire_days: 180,
          resource_ids: [],
          dimension: 'api'
        }
        this.applySliderConf.isShow = false
      },

      handleSingleApply (data) {
        this.permissionSelectList = [data]
        this.applyNewTime = dayjs(Date.now() + 180 * 24 * 60 * 60 * 1000).format('YYYY-MM-DD hh:mm:ss')
        this.applyKey++
        this.batchApplyDialogConf.isShow = true
      },

      handleBatchApply () {
        if (!this.permissionTableSelection.length) {
          this.$bkMessage({
            theme: 'error',
            message: this.$t('请选择要续期的权限')
          })
          return false
        }

        this.applyNewTime = dayjs(Date.now() + 180 * 24 * 60 * 60 * 1000).format('YYYY-MM-DD hh:mm:ss')
        this.applyKey++
        this.permissionSelectList = this.permissionTableSelection.sort((a, b) => {
          if ((a.renewable && b.renewable) || (!a.renewable && !b.renewable)) {
            return 0
          } else if (a.renewable && !b.renewable) {
            return -1
          } else if (!a.renewable && b.renewable) {
            return 1
          }
        })
        this.batchApplyDialogConf.isShow = true
      },

      handlePageSelect (selection, row) {
        this.permissionTableSelection = selection
      },

      handlePageSelectAll (selection, row) {
        this.permissionTableSelection = selection
      },

      async batchApplyPermission () {
        if (this.isBatchApplyLoaading) {
          return false
        }
        this.isBatchApplyLoaading = true

        const ids = this.permissionSelectList.map(permission => permission.id)
        const data = {
          ids: ids
        }

        try {
          await this.$store.dispatch('componentPermission/permRenew', data)
          this.getApigwPermissionList()
          this.batchApplyDialogConf.isShow = false
          this.$bkMessage({
            theme: 'success',
            message: this.$t('续期成功！')
          })
        } catch (e) {
          catchErrorHandler(e, this)
        } finally {
          this.isBatchApplyLoaading = false
        }
      },

      clearFilterKey () {
        this.searchFilters = []
      },

      updateTableEmptyConfig () {
        if (this.searchFilters.length) {
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

    .dropdown-icon {
        margin: 0 -4px;
        &.open {
            transform: rotate(180deg);
        }
    }

    .bk-dropdown-item {
        .disabled {
            color: #C4C6CC;
            cursor: not-allowed;

            &:hover {
                color: #C4C6CC;
            }
        }
    }
</style>
