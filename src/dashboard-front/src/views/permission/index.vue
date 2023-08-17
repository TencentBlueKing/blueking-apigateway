<template>
  <div class="app-content">
    <div class="ag-top-header permissions-header">
      <div class="flex-nowrap">
        <span v-bk-tooltips="{ content: $t('请选择待续期的权限'), disabled: permissionTableSelection.length }">
          <bk-button theme="primary" class="mr10 fl" @click="handleBatchApply" :disabled="!permissionTableSelection.length"> {{ $t('批量续期') }} </bk-button>
        </span>
        <bk-dropdown-menu
          trigger="click"
          style="vertical-align: middle; margin-right: 5px;"
          @show="isExportDropdownShow = true"
          @hide="isExportDropdownShow = false"
          font-size="medium">
          <bk-button slot="dropdown-trigger">
            <span> {{ $t('导出') }} </span>
            <i :class="['dropdown-icon bk-icon icon-angle-down', { 'open': isExportDropdownShow }]"></i>
          </bk-button>
          <ul class="bk-dropdown-list" slot="dropdown-content">
            <li class="bk-dropdown-item">
              <a
                href="javascript:;"
                @click="handleExportAll($event)">
                {{ $t('全部应用权限') }}
              </a>
            </li>
            <li class="bk-dropdown-item">
              <a
                href="javascript:;"
                :class="{ disabled: !hasFiltered }"
                v-bk-tooltips.right="{ disabled: hasFiltered, content: $t('请先筛选资源') , boundary: 'window' }"
                @click="handleExportFiltered($event, !hasFiltered)">
                {{ $t('已筛选应用权限') }}
              </a>
            </li>
            <li class="bk-dropdown-item">
              <a
                href="javascript:;"
                :class="{ disabled: !hasSelected }"
                v-bk-tooltips.right="{ disabled: hasSelected, content: $t('请先勾选资源') , boundary: 'window' }"
                @click="handleExportSelected($event, !hasSelected)">
                {{ $t('已选应用权限') }}
              </a>
            </li>
          </ul>
        </bk-dropdown-menu>
        <bk-button @click="handleApplyShow" class="ml5 mr10"> {{ $t('主动授权') }} </bk-button>
      </div>

      <bk-form class="fr flex-nowrap form-box-cls" form-type="inline">
        <bk-form-item :label="$t('授权维度')" class="flex-nowrap">
          <bk-select
            style="width: 190px;"
            v-model="searchParams.dimension"
            :clearable="false"
            @change="handleDimensionChange">
            <bk-option v-for="option in dimensionList"
              :key="option.id"
              :id="option.id"
              :name="option.name">
            </bk-option>
          </bk-select>
        </bk-form-item>
        <!-- <bk-form-item :label="$t('授权类型')">
                    <bk-select
                        style="width: 190px;"
                        v-model="searchParams.grant_type"
                        clearable>
                        <bk-option v-for="option in grantTypes"
                            :key="option.id"
                            :id="option.id"
                            :name="option.name">
                        </bk-option>
                    </bk-select>
                </bk-form-item> -->
        <bk-form-item label="" class="search-select-wrapper" style="flex: 1;">
          <bk-search-select
            :placeholder="$t('搜索')"
            :show-popover-tag-change="true"
            :clearable="true"
            :data="searchParams.dimension === 'resource' ? searchResourceCondition : searchApiCondition"
            :show-condition="false"
            v-model="searchFilters"
            :readonly="searchReadonly"
            @menu-select="handleMenuSelect"
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
      <bk-table-column :label="$t('资源名称')" prop="resource_name" v-if="searchParams.dimension === 'resource'" :render-header="$renderHeader"></bk-table-column>
      <bk-table-column :label="$t('请求路径')" prop="resource_path" v-if="searchParams.dimension === 'resource'" :render-header="$renderHeader">
        <template slot-scope="props">
          <span class="ag-auto-text">
            {{props.row['resource_path'] || '--'}}
          </span>
        </template>
      </bk-table-column>
      <bk-table-column width="100" :label="$t('请求方法')" prop="resource_method" v-if="searchParams.dimension === 'resource'" :render-header="$renderHeader">
        <template slot-scope="props">
          {{props.row['resource_method'] || '--'}}
        </template>
      </bk-table-column>
      <bk-table-column :label="$t('过期时间')" prop="expires" :render-header="$renderHeader">
        <template slot-scope="props">
          {{props.row['expires'] || $t('永久有效')}}
        </template>
      </bk-table-column>
      <bk-table-column width="150" :label="$t('授权类型')" prop="expires" :render-header="$renderHeader">
        <template slot-scope="props">
          {{props.row['grant_type'] === 'initialize' ? $t('主动授权') : $t('申请审批')}}
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
      :width="searchParams.dimension === 'resource' ? 950 : 800"
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
          <bk-table-column :label="$t('资源名称')" prop="resource_name" v-if="searchParams.dimension === 'resource'" :render-header="$renderHeader"></bk-table-column>
          <!-- <bk-table-column :label="$t('请求路径')" prop="resource_path" v-if="searchParams.dimension === 'resource'">
                        <template slot-scope="props">
                            {{props.row['resource_path'] || '--'}}
                        </template>
                    </bk-table-column>
                    <bk-table-column :label="$t('请求方法')" prop="resource_method" v-if="searchParams.dimension === 'resource'">
                        <template slot-scope="props">
                            {{props.row['resource_method'] || '--'}}
                        </template>
                    </bk-table-column> -->
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

    <bk-sideslider
      :title="applySliderConf.title"
      :width="800"
      :is-show.sync="applySliderConf.isShow"
      :quick-close="true"
      :before-close="handleBeforeClose"
      @hidden="handleHidden">
      <div slot="content" class="p30">
        <p class="ag-span-title"> {{ $t('你将对指定的蓝鲸应用添加访问资源的权限') }} </p>
        <bk-form class="mb30 ml15" :label-width="120" :model="curApply">
          <bk-form-item
            :label="$t('蓝鲸应用ID')"
            :required="true">
            <bk-input
              :placeholder="$t('请输入应用ID')"
              v-model="curApply.bk_app_code"
              style="width: 256px;">
            </bk-input>
          </bk-form-item>
          <bk-form-item
            :label="$t('有效时间')"
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
                {{ $t('天') }}
              </bk-radio>
              <bk-radio :value="'None'"> {{ $t('永久有效') }} </bk-radio>
            </bk-radio-group>
          </bk-form-item>
        </bk-form>
        <p class="ag-span-title"> {{ $t('请选择要授权的资源') }} </p>
        <div class="ml20">
          <bk-radio-group class="ag-resource-radio" v-model="curApply.dimension">
            <bk-radio value="api">
              {{ $t('按网关') }}
              <span v-bk-tooltips="$t('包括网关下所有资源，包括未来新创建的资源')">
                <i class="apigateway-icon icon-ag-help"></i>
              </span>
            </bk-radio>
            <bk-radio value="resource">
              {{ $t('按资源') }}
              <span v-bk-tooltips="$t('仅包含当前选择的资源')">
                <i class="apigateway-icon icon-ag-help"></i>
              </span>
            </bk-radio>
          </bk-radio-group>

          <div class="ag-transfer-box" v-if="curApply.dimension === 'resource'">
            <bk-transfer
              ext-cls="resource-transfer-wrapper"
              :source-list="resourceList"
              :display-key="'name'"
              :setting-key="'id'"
              :title="[$t('未选资源'), $t('已选资源')]"
              :searchable="true"
              @change="handleResourceChange">
              <div
                slot="source-option"
                slot-scope="data"
                class="transfer-source-item"
                :title="data.name"
              >
                {{ data.name }}
              </div>
              <div
                slot="target-option"
                slot-scope="data"
                class="transfer-source-item"
                :title="data.name"
              >
                {{ data.name }}
              </div>
            </bk-transfer>
          </div>

          <div class="action mt20">
            <bk-button theme="primary" class="mr10" @click="submitApigwApply"> {{ $t('保存') }} </bk-button>
            <bk-button @click="handleHideApplySlider"> {{ $t('取消') }} </bk-button>
          </div>
        </div>
      </div>
    </bk-sideslider>

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
          <bk-table-column :label="$t('请求路径')" prop="resource_path"></bk-table-column>
          <bk-table-column :label="$t('请求方法')" prop="resource_method"></bk-table-column>
        </bk-table>
      </div>
    </bk-dialog>
  </div>
</template>

<script>
  import { catchErrorHandler, sortByKey } from '@/common/util'
  import dayjs from 'dayjs'
  import sidebarMixin from '@/mixins/sidebar-mixin'

  export default {
    mixins: [sidebarMixin],
    data () {
      return {
        searchResourceCondition: [
          {
            name: this.$t('蓝鲸应用ID'),
            id: 'bk_app_code',
            children: []
          },
          {
            name: this.$t('资源名称'),
            id: 'resource_id',
            children: []
          },
          {
            name: this.$t('模糊搜索'),
            id: 'query'
          }
        ],
        searchApiCondition: [
          {
            name: this.$t('蓝鲸应用ID'),
            id: 'bk_app_code',
            children: []
          },
          {
            name: this.$t('模糊搜索'),
            id: 'query'
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
          bk_app_code: '',
          query: '',
          resource_id: '',
          grant_type: '',
          dimension: 'resource'
        },
        removeDialogConf: {
          isShow: false
        },
        tableIndex: 0,
        tableEmptyConf: {
          keyword: '',
          isAbnormal: false
        },
        searchReadonly: false
      }
    },
    computed: {
      apigwId () {
        return this.$route.params.id
      },
      hasSelected () {
        return this.permissionTableSelection.length > 0
      },
      hasFiltered () {
        return !!(this.searchParams.resource_id || this.searchParams.query || this.searchParams.bk_app_code)
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
        deep: true,
        handler () {
          this.pagination.current = 1
          this.pagination.count = 0
          this.getApigwPermissionList()
        }
      },
      searchFilters () {
        this.$nextTick(() => {
          this.searchParams.query = ''
          this.searchParams.bk_app_code = ''
          this.searchParams.resource_id = ''
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
        this.getApigwResources()
        this.getBkAppCodes()
      },

      async getApigwPermissionList (page) {
        const apigwId = this.apigwId
        const curPage = page || this.pagination.current
        const pageParams = {
          limit: this.pagination.limit,
          offset: this.pagination.limit * (curPage - 1),
          dimension: this.searchParams.dimension,
          bk_app_code: this.searchParams.bk_app_code,
          grant_type: this.searchParams.grant_type,
          resource_id: this.searchParams.resource_id,
          query: this.searchParams.query
        }

        this.isDataLoading = true
        this.permissionTableSelection = []
        try {
          const res = await this.$store.dispatch('permission/getApigwPermissionList', { apigwId, pageParams })
          res.data.results.forEach(item => {
            item.updated_time = item.updated_time || '--'
          })
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

      async getApigwResources (page) {
        const apigwId = this.apigwId
        const pageParams = {
          no_page: true,
          order_by: 'path'
        }

        try {
          const res = await this.$store.dispatch('resource/getApigwResources', { apigwId, pageParams })
          const results = res.data.results.map(item => {
            return {
              id: item.id,
              name: item.name,
              path: item.path,
              method: item.method,
              resourceName: `${item.method}：${item.path}`
            }
          })

          this.resourceList = sortByKey(results, 'name')
          this.searchResourceCondition[1].children = this.resourceList.map(item => {
            return {
              id: item.id,
              name: item.name
            }
          })
        } catch (e) {
          catchErrorHandler(e, this)
        }
      },

      async getBkAppCodes (page) {
        const apigwId = this.apigwId
        const pageParams = {
          dimension: this.searchParams.dimension
        }

        try {
          const res = await this.$store.dispatch('getBkAppCodes', { apigwId, pageParams })
          const resources = res.data.map(item => {
            return {
              id: item,
              name: item
            }
          })
          this.searchResourceCondition[0].children = resources
          this.searchApiCondition[0].children = resources
        } catch (e) {
          catchErrorHandler(e, this)
        }
      },

      handleExportAll (event, disabled) {
        const data = {
          export_type: 'all',
          dimension: this.searchParams.dimension
        }

        this.exportDownload(data)
      },

      handleExportSelected (event, disabled) {
        if (disabled) {
          event.stopPropagation()
          return false
        }

        const data = {
          export_type: 'selected',
          dimension: this.searchParams.dimension,
          permission_ids: this.permissionTableSelection.map(item => item.id)
        }

        this.exportDownload(data)
      },

      handleExportFiltered (event, disabled) {
        if (disabled) {
          event.stopPropagation()
          return false
        }

        const data = {
          export_type: 'filtered',
          ...this.searchParams
        }

        this.exportDownload(data)
      },

      handleApplyShow () {
        this.applySliderConf.isShow = true
        // 收集初始化状态
        this.initSidebarFormData(this.curApply)
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

      async exportDownload (data) {
        const apigwId = this.apigwId
        this.isDataLoading = true

        if (!data.resource_id) {
          delete data.resource_id
        }

        try {
          const res = await this.$store.dispatch('permission/exportApigwPermission', { apigwId, data })
          // 成功则触发下载文件
          if (res.ok) {
            const blob = await res.blob()
            const disposition = res.headers.get('Content-Disposition') || ''
            const url = URL.createObjectURL(blob)
            const elment = document.createElement('a')
            elment.download = (disposition.match(/filename="(\S+?)"/) || [])[1]
            elment.href = url
            elment.click()
            URL.revokeObjectURL(blob)

            this.$bkMessage({
              theme: 'success',
              message: this.$t('导出成功！')
            })
          } else {
            this.$bkMessage({
              theme: 'error',
              message: this.$t('导出失败！')
            })
          }
        } catch (e) {
          catchErrorHandler(e, this)
        } finally {
          this.isDataLoading = false
        }
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
          const apigwId = this.apigwId
          const ids = [this.curPermission.id]

          const data = {
            dimension: this.searchParams.dimension,
            ids: ids
          }

          await this.$store.dispatch('permission/deleteApigwPermission', { apigwId, data })

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
        // this.handleSearch()
      },

      handleSearch (event) {
        this.searchParams.bk_app_code = this.keyword
      },

      handleRemove (data) {
        // const self = this
        this.curPermission = data
        this.curPermission.details = [data]
        // this.$bkInfo({
        //     title: `确定删除【${data.bk_app_code}】权限？`,
        //     subTitle: '删除后将无法恢复，请确认是否删除？',
        //     confirmFn () {
        //         self.removePermission()
        //     }
        // })
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
        this.initCurApplyData()
        this.applySliderConf.isShow = false
      },

      handleSingleApply (data) {
        this.permissionSelectList = [data]
        this.applyNewTime = dayjs(Date.now() + 180 * 24 * 60 * 60 * 1000).format('YYYY-MM-DD HH:mm:ss')
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

        this.applyNewTime = dayjs(Date.now() + 180 * 24 * 60 * 60 * 1000).format('YYYY-MM-DD HH:mm:ss')
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

      handleDimensionChange () {
        this.searchFilters = []
      },

      async batchApplyPermission () {
        if (this.isBatchApplyLoaading) {
          return false
        }
        this.isBatchApplyLoaading = true

        const ids = this.permissionSelectList.map(permission => permission.id)
        const data = {
          dimension: this.searchParams.dimension,
          ids: ids
        }
        const apigwId = this.apigwId

        try {
          await this.$store.dispatch('permission/batchUpdateApigwPermission', { apigwId, data })
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

      checkPermissionSelect (row, index) {
        return row.renewable
      },

      clearFilterKey () {
        this.searchFilters = []
      },

      updateTableEmptyConfig () {
        if (this.searchFilters.length) {
          this.tableEmptyConf.keyword = 'placeholder'
          return
        } else if (this.searchParams.dimension) {
          this.tableEmptyConf.keyword = '$CONSTANT'
          return
        }
        this.tableEmptyConf.keyword = ''
      },

      initCurApplyData () {
        this.curApply = {
          bk_app_code: '',
          expire_type: 'custom',
          expire_days: 180,
          resource_ids: [],
          dimension: 'api'
        }
      },

      handleHidden () {
        this.initCurApplyData()
      },

      async handleBeforeClose () {
        return this.$isSidebarClosed(JSON.stringify(this.curApply))
      },

      handleMenuSelect (data) {
        this.searchReadonly = data.id === 'resource_id'
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

    .permissions-header {
        display: flex;
        justify-content: space-between;

        .flex-nowrap {
            display: flex;
            flex-wrap: nowrap;
            /deep/ .bk-label {
                white-space: nowrap;
            }
        }
        .form-box-cls {
            flex: 1;
            max-width: 770px;
        }
        .search-select-wrapper /deep/ .bk-form-content {
            width: 100%;
        }
    }
</style>
