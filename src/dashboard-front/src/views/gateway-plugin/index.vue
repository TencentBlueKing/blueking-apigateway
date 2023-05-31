<template>
  <div class="app-content">
    <div class="ag-top-header">
      <bk-button theme="primary" @click="handleCreateStage"> {{ $t('启用插件') }} </bk-button>
      <bk-input
        class="fr"
        :clearable="true"
        v-model="keyword"
        :placeholder="$t('请输入插件名称，按Enter搜索')"
        :right-icon="'bk-icon icon-search'"
        style="width: 300px;"
        @enter="handleSearch">
      </bk-input>
    </div>
    <bk-table style="margin-top: 15px;"
      ref="pluginRef"
      :data="plugins"
      :size="'small'"
      :pagination="pagination"
      v-bkloading="{ isLoading: isDataLoading }"
      :ext-cls="'ag-stage-table'"
      :cell-style="{ 'overflow': 'visible', 'white-space': 'normal' }"
      @page-limit-change="handlePageLimitChange"
      @sort-change="handleSortChange(...arguments, 'plugin')"
      @filter-change="handleFilterChange"
      @page-change="handlePageChange">
      <div slot="empty">
        <table-empty
          :keyword="tableEmptyConf.keyword"
          :abnormal="tableEmptyConf.isAbnormal"
          @reacquire="getPlugins"
          @clear-filter="clearFilterKey"
        />
      </div>
      <bk-table-column :label="$t('名称')" prop="name" sortable column-key="name"></bk-table-column>
      <bk-table-column
        :label="$t('类型')"
        prop="type"
        column-key="type"
        :filters="typeFilters"
        :filter-method="sourceFilterMethod"
        :filter-multiple="false"
        :show-overflow-tooltip="true">
        <template slot-scope="props">
          <template>
            <span class="ag-auto-text">
              {{props.row.type_name || '--'}}
            </span>
          </template>
        </template>
      </bk-table-column>
      <bk-table-column :label="$t('更新时间')" prop="updated_time" sortable column-key="updated_time" :render-header="$renderHeader">
        <template slot-scope="{ row }">
          {{row.updated_time || '--'}}
        </template>
      </bk-table-column>
      <bk-table-column :label="$t('操作')" width="150" class="ag-action" :show-overflow-tooltip="false">
        <template slot-scope="props">
          <bk-button
            class="mr10"
            text
            theme="primary"
            @click="handleEdit(props.row, 'baseInfo')">
            {{ $t('编辑') }}
          </bk-button>
          <bk-dropdown-menu ref="dropdown" align="right">
            <i class="bk-icon icon-more ag-more-btn ml10" slot="dropdown-trigger"></i>
            <ul class="bk-dropdown-list" slot="dropdown-content">
              <li>
                <a href="javascript:;" @click.stop.prevent="handleBindStage(props.row)"> {{ $t('绑定环境') }} </a>
              </li>
              <li v-if="props.row.type_code !== 'bk-verified-user-exempted-apps'">
                <a href="javascript:;" @click.stop.prevent="handleBindResource(props.row)"> {{ $t('绑定资源') }} </a>
              </li>
              <li>
                <a href="javascript:;" @click.stop.prevent="handleDeleteDialog(props.row)"> {{ $t('删除') }} </a>
              </li>
            </ul>
          </bk-dropdown-menu>
        </template>
      </bk-table-column>
    </bk-table>

    <bk-sideslider
      :title="resourceBindSliderConf.title"
      :width="840"
      :is-show.sync="resourceBindSliderConf.isShow"
      :quick-close="true"
      :before-close="handleBeforeClose"
      @hidden="removeResourceScroll">
      <div slot="content" class="p30">
        <bk-form ref="resourceBindForm" :label-width="85" :model="curPlugin">
          <bk-form-item
            :label="$t('名称')">
            <span class="f12">{{curPlugin.name}}</span>
          </bk-form-item>
          <bk-form-item
            :label="$t('资源')">
            <bk-transfer
              ext-cls="resource-transfer-wrapper"
              :key="renderTransferIndex"
              :target-list="resourceTargetList"
              :source-list="resourceList"
              :display-key="'resourceName'"
              :setting-key="'id'"
              :title="[$t('未选资源'), $t('已选资源')]"
              :searchable="true"
              @change="handleResourceChange">
              <div
                slot="source-option"
                slot-scope="data"
                class="transfer-source-item"
                :title="data.resourceName"
              >
                {{ data.resourceName }}
              </div>
              <div
                slot="target-option"
                slot-scope="data"
                class="transfer-source-item"
                :title="data.resourceName"
              >
                {{ data.resourceName }}
              </div>
            </bk-transfer>
            <div class="ag-alert warning mt10">
              <i class="apigateway-icon icon-ag-info"></i>
              <p> {{ $t('如果资源已经绑定了一个插件，则会被本插件覆盖，请谨慎操作') }} </p>
            </div>
          </bk-form-item>
          <bk-form-item label="">
            <bk-button theme="primary" class="mr10" @click="checkBindeStage('resource')" :loading="isChecking"> {{ $t('保存') }} </bk-button>
            <bk-button @click="handleHideResourceSlider"> {{ $t('取消') }} </bk-button>
          </bk-form-item>
        </bk-form>
      </div>
    </bk-sideslider>

    <bk-sideslider
      :title="stageBindSliderConf.title"
      :width="560"
      :quick-close="true"
      :before-close="handleBeforeClose"
      :is-show.sync="stageBindSliderConf.isShow">
      <div slot="content" class="p30">
        <bk-form ref="stageBindForm" :label-width="68" :model="curPlugin" style="min-height: 600px;">
          <bk-form-item
            :label="$t('名称')">
            <span class="f12">{{curPlugin.name || '--'}}</span>
          </bk-form-item>
          <bk-form-item
            :label="$t('环境')">
            <bk-select
              searchable
              multiple
              show-select-all
              v-model="scopeIds">
              <bk-option v-for="option in stageList"
                :key="option.id"
                :id="option.id"
                :name="option.name">
              </bk-option>
            </bk-select>
            <div class="ag-alert warning mt10">
              <i class="apigateway-icon icon-ag-info"></i>
              <p> {{ $t('如果环境已经绑定了一个插件，则会被本插件覆盖，请谨慎操作') }} </p>
            </div>
          </bk-form-item>
          <bk-form-item label="">
            <bk-button theme="primary" class="mr10" @click="checkBindeStage('stage')" :loading="isChecking"> {{ $t('保存') }} </bk-button>
            <bk-button @click="handleHideStageSlider"> {{ $t('取消') }} </bk-button>
          </bk-form-item>
        </bk-form>
      </div>
    </bk-sideslider>

    <bk-dialog
      v-model="unbindResourceConf.isShow"
      theme="primary"
      :render-directive="'if'"
      :width="670"
      :title="`${curPlugin.scope_type === 'stage' ? $t('环境') : $t('资源') }${$t('绑定变更，请确认')}`"
      :mask-close="true"
      @cancel="unbindOperation"
      @confirm="submitBindingData">
      <div>
        <bk-table
          :data="bindChangeResources"
          :size="'small'"
          :max-height="280"
          :key="tableIndex">
          <div slot="empty">
            <table-empty empty />
          </div>
          <bk-table-column :label="$t('环境名称')" prop="name" v-if="curPlugin.scope_type === 'stage'" :render-header="$renderHeader"></bk-table-column>
          <bk-table-column :label="$t('请求路径')" prop="path" v-if="curPlugin.scope_type === 'resource'" :render-header="$renderHeader">
            <template slot-scope="props">
              <span class="ag-auto-text" v-bk-tooltips.right="props.row.path || '--'">{{props.row.path || '--'}}</span>
            </template>
          </bk-table-column>
          <bk-table-column :label="$t('请求方法')" prop="method" v-if="curPlugin.scope_type === 'resource'" :render-header="$renderHeader"></bk-table-column>
          <bk-table-column :label="$t('原插件')" :render-header="$renderHeader">
            <template slot-scope="props">
              <span v-if="props.row.bindStatus === 'add'">--</span>
              <span
                v-else
                class="ag-auto-text"
                v-bk-tooltips.right="props.row.oldStrategy.config_name || '--'">
                {{props.row.oldStrategy.config_name || '--'}}
              </span>
            </template>
          </bk-table-column>
          <bk-table-column :label="$t('目标插件')" :render-header="$renderHeader">
            <template slot-scope="props">
              <template v-if="props.row.bindStatus === 'delete'">
                --
              </template>
              <template v-else>
                <span class="ag-auto-text" v-bk-tooltips.right="props.row.newStrategy.name || '--'">{{props.row.newStrategy.name || '--'}}</span>
              </template>
            </template>
          </bk-table-column>
          <bk-table-column :label="$t('变更状态')" prop="bindStatus" :render-header="$renderHeader">
            <template slot-scope="props">
              <template v-if="props.row.bindStatus === 'add'">
                <span class="ag-tag primary"> {{ $t('绑定') }} </span>
              </template>
              <template v-else-if="props.row.bindStatus === 'delete'">
                <span class="ag-tag warning"> {{ $t('解绑') }} </span>
              </template>
              <template v-else-if="props.row.bindStatus === 'merge'">
                <span class="ag-tag danger"> {{ $t('覆盖') }} </span>
              </template>
            </template>
          </bk-table-column>
        </bk-table>
        <template v-if="curPlugin.scope_type === 'stage'">
          <div class="ag-alert warning mt10" v-if="mergeResources.length">
            <i class="apigateway-icon icon-ag-info"></i>
            <p> {{ $t('部分环境已经绑定了插件，如果继续操作，原来的插件将被本插件覆盖') }} </p>
          </div>
          <div class="ag-alert warning mt10" v-else-if="unbindResources.length">
            <i class="apigateway-icon icon-ag-info"></i>
            <p> {{ $t('部分环境被取消选中，如果继续操作，原来的绑定将被解绑') }} </p>
          </div>
        </template>
        <template v-else>
          <div class="ag-alert warning mt10" v-if="mergeResources.length">
            <i class="apigateway-icon icon-ag-info"></i>
            <p> {{ $t('部分资源已经绑定了插件，如果继续操作，原来的插件将被本插件覆盖') }} </p>
          </div>
          <div class="ag-alert warning mt10" v-else-if="unbindResources.length">
            <i class="apigateway-icon icon-ag-info"></i>
            <p> {{ $t('部分资源被取消选中，如果继续操作，原来的绑定将被解绑') }} </p>
          </div>
        </template>
      </div>
    </bk-dialog>

  </div>
</template>

<script>
  import { catchErrorHandler, clearFilter } from '@/common/util'
  import _ from 'lodash'
  import sidebarMixin from '@/mixins/sidebar-mixin'

  export default {
    mixins: [sidebarMixin],
    data () {
      return {
        keyword: '',
        isPageLoading: true,
        isDataLoading: false,
        stageList: [
        ],
        plugins: [],
        pagination: {
          current: 1,
          count: 0,
          limit: 10
        },
        isOfflineLoading: false,
        curStage: {
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
        offlineDialogConf: {
          visiable: false
        },
        deleteDialogConf: {
          visiable: false,
          delPlugin: false
        },
        resourceBindSliderConf: {
          isLoading: false,
          isShow: false,
          title: this.$t('绑定资源')
        },
        stageBindSliderConf: {
          isLoading: false,
          isShow: false,
          title: this.$t('绑定环境')
        },
        curPlugin: {},
        scopeIds: [],
        resourceTargetList: [],
        renderTransferIndex: 0,
        resourceList: [],
        isChecking: false,
        unbindResourceConf: {
          isShow: false
        },
        bindChangeResources: [],
        tableIndex: 0,
        mergeResources: [],
        unbindResources: [],
        rowId: '',
        typeList: [],
        delData: {},
        orderBy: {
          plugin: ''
        },
        filterType: '',
        tableEmptyConf: {
          keyword: '',
          isAbnormal: false
        },
        sourceEl: null
      }
    },
    computed: {
      apigwId () {
        return this.$route.params.id
      },
      typeFilters () {
        return this.typeList.map(item => {
          return { value: item.id, text: item.name }
        })
      },
      localLanguage () {
        return this.$store.state.localLanguage
      }
    },
    watch: {
      keyword (newVal, oldVal) {
        if (oldVal && !newVal) {
          this.handleSearch()
        }
      },
      filterType () {
        this.handleSearch()
      },
      'orderBy.plugin' () {
        this.handleSearch()
      }
    },
    created () {
      this.init()
    },
    methods: {
      async init () {
        await this.getPluginType()
        this.getApigwStages()
        await this.getPlugins()
        this.showBindInfo()
      },

      async getPluginType () {
        const apigwId = this.apigwId
        const type = await this.$store.dispatch('gatewayPlugin/getPluginType', { apigwId })
        this.typeList = type.data.results
      },

      async getPlugins (page) {
        const apigwId = this.apigwId
        const curPage = page || this.pagination.current
        const pageParams = {
          limit: this.pagination.limit,
          offset: this.pagination.limit * (curPage - 1),
          search: this.keyword
        }
        if (this.filterType) {
          pageParams['type'] = this.filterType
        }

        this.isDataLoading = true
        try {
          const res = await this.$store.dispatch('gatewayPlugin/getPlugins', { apigwId, pageParams })
          this.plugins = res.data.results
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

      handleSortChange (params, type) {
        if (params.prop === 'name') {
          if (params.order === 'descending') {
            this.orderBy[type] = '-name'
          } else if (params.order === 'ascending') {
            this.orderBy[type] = 'name'
          } else {
            this.orderBy[type] = ''
          }
        }

        if (params.prop === 'updated_time') {
          if (params.order === 'descending') {
            this.orderBy[type] = '-updated_time'
          } else if (params.order === 'ascending') {
            this.orderBy[type] = 'updated_time'
          } else {
            this.orderBy[type] = ''
          }
        }
      },

      handleFilterChange (filters) {
        if (filters.type) {
          this.filterType = filters.type[0] ? filters.type[0] : ''
        }
        return true
      },

      // 接口筛选
      sourceFilterMethod (value, row, column) {
        return true
      },

      handlePageLimitChange (limit) {
        this.pagination.limit = limit
        this.pagination.current = 1
        this.getPlugins(this.pagination.current)
      },

      handlePageChange (newPage) {
        this.pagination.current = newPage
        this.getPlugins(newPage)
      },

      handleCreateStage () {
        this.$router.push({
          name: 'apigwGatewayPluginCreate',
          query: {
            type: 'create'
          }
        })
      },

      handleSearch () {
        this.pagination.current = 1
        this.pagination.count = 0
                
        this.getPlugins()
      },

      handleDeleteDialog (data) {
        const self = this

        this.delData = data
        this.$bkInfo({
          extCls: 'info-del-plugin-cls',
          title: this.$t(`确定删除【{name}】插件？`, { name: data.name }),
          subTitle: this.$t('将删除相关配置，不可恢复，请确认是否删除？'),
          width: this.localLanguage === 'en' ? 650 : 500,
          confirmFn () {
            self.handleDeletePlugin()
          }
        })
      },
            
      async handleDeletePlugin () {
        try {
          const apigwId = this.apigwId
          const id = this.delData.id
          await this.$store.dispatch('gatewayPlugin/deletePlugin', { apigwId, id })
          // 当前页只有一条数据
          if (this.plugins.length === 1 && this.pagination.current > 1) {
            this.pagination.current--
          }
          this.getPlugins()

          this.$bkMessage({
            theme: 'success',
            message: this.$t('删除成功！')
          })
        } catch (e) {
          catchErrorHandler(e, this)
        }
      },

      handleEdit (data, TabActive) {
        this.$router.push({
          name: 'apigwGatewayPluginEdit',
          params: {
            id: this.apigwId
          },
          query: {
            plugId: data.id,
            type: 'edit',
            typeId: data.type_id,
            TabActive
          }
        })
      },

      handleResourceChange (sourceList, targetList, targetValueList) {
        this.scopeIds = targetValueList
      },

      handleHideStageSlider () {
        this.stageBindSliderConf.isShow = false
      },

      submitBindingData () {
        if (this.curPlugin.scope_type === 'stage') {
          this.submitStagePluginBinding()
        } else {
          this.submitresourcePluginBinding()
        }
      },

      handleHideResourceSlider () {
        this.resourceBindSliderConf.isShow = false
      },

      async checkBindeStage (type) {
        this.isChecking = true

        const apigwId = this.apigwId
        const id = this.rowId
        const originList = this.curPlugin.scope_type === 'stage' ? this.stageList : this.resourceList
        const data = {
          scope_type: type,
          scope_ids: this.scopeIds,
          dry_run: true
        }
        try {
          const res = await this.$store.dispatch('gatewayPlugin/createPluginBinding', { apigwId, id, data })
          const addList = res.data.creates.map(item => {
            return item.scope_id
          })

          const deleteList = res.data.unbinds.map(item => {
            return item.scope_id
          })

          const mergeList = res.data.overwrites.map(item => {
            return item.scope_id
          })

          this.addResources = originList.filter(resource => {
            return addList.includes(resource.id)
          })

          this.unbindResources = originList.filter(resource => {
            return deleteList.includes(resource.id)
          })

          this.mergeResources = originList.filter(resource => {
            return mergeList.includes(resource.id)
          })

          this.bindChangeResources = []

          this.mergeResources.forEach(item => {
            item.bindStatus = 'merge'
            item.newStrategy = this.curPlugin
            item.oldStrategy = res.data.overwrites.find(mergeItem => {
              return mergeItem.scope_id === item.id
            })
            this.bindChangeResources.push(item)
          })

          this.unbindResources.forEach(item => {
            item.bindStatus = 'delete'
            item.newStrategy = this.curPlugin
            item.oldStrategy = res.data.unbinds.find(deleteItem => {
              return deleteItem.scope_id === item.id
            })
            this.bindChangeResources.push(item)
          })

          this.addResources.forEach(item => {
            item.bindStatus = 'add'
            item.newStrategy = this.curPlugin
            item.oldStrategy = res.data.creates.find(addItem => {
              return addItem.scope_id === item.id
            })
            this.bindChangeResources.push(item)
          })

          if (this.bindChangeResources.length) {
            this.tableIndex++
            this.$nextTick(() => {
              this.unbindResourceConf.isShow = true
            })
          } else {
            this.submitBindingData()
          }
        } catch (e) {
          catchErrorHandler(e, this)
        } finally {
          this.isChecking = false
        }
      },

      async handleBindStage (data) {
        this.curPlugin = data
        this.rowId = data.id
        this.scopeIds = []
        this.curPlugin.scope_type = 'stage'
        this.stageBindSliderConf.isShow = true
        await this.getPluginBinding(data)
        this.initSidebarFormData(this.scopeIds)
      },

      async handleBindResource (data) {
        this.getApigwResources()
        this.curPlugin = data
        this.rowId = data.id
        this.scopeIds = []
        this.curPlugin.scope_type = 'resource'
        this.renderTransferIndex++
        this.resourceBindSliderConf.isShow = true
        await this.getPluginBindingResources(data)
        this.handleResourceScroll()
        this.initSidebarFormData(this.scopeIds)
      },

      // 获取绑定环境
      async getPluginBinding (rowData) {
        const apigwId = this.apigwId
        const id = rowData.id
        try {
          const res = await this.$store.dispatch('gatewayPlugin/getPluginBinding', { apigwId, id })
          this.curStrategyStages = res.data.binds
          res.data.binds.forEach(item => {
            if (item.scope_type === 'stage') {
              this.scopeIds.push(item.scope_id)
            }
          })
        } catch (e) {
          catchErrorHandler(e, this)
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

      async submitStagePluginBinding () {
        const apigwId = this.apigwId
        const id = this.curPlugin.id
        const data = {
          scope_type: 'stage',
          scope_ids: this.scopeIds,
          dry_run: false,
          creates: true
        }
        try {
          await this.$store.dispatch('gatewayPlugin/createPluginBinding', { apigwId, id, data })
          this.$bkInfo({
            extCls: 'plugin-tips-cls',
            type: 'success',
            title: this.$t('环境绑定成功'),
            cancelText: this.$t('关闭'),
            width: 460,
            subTitle: this.$t('绑定成功，绑定插件 5 分钟内生效，请稍候...')
          })
          this.stageBindSliderConf.isShow = false
        } catch (e) {
          catchErrorHandler(e, this)
        } finally {
          this.isChecking = false
        }
      },

      async submitresourcePluginBinding () {
        const apigwId = this.apigwId
        const id = this.curPlugin.id
        const data = {
          scope_type: 'resource',
          scope_ids: this.scopeIds,
          dry_run: false,
          creates: true
        }
        try {
          await this.$store.dispatch('gatewayPlugin/createPluginBinding', { apigwId, id, data })
          this.$bkInfo({
            extCls: 'plugin-tips-cls',
            type: 'success',
            title: this.$t('资源绑定成功'),
            cancelText: this.$t('关闭'),
            width: 460,
            subTitle: this.$t('绑定成功，绑定插件 5 分钟内生效，请稍候...')
          })
          this.resourceBindSliderConf.isShow = false
        } catch (e) {
          catchErrorHandler(e, this)
        } finally {
          this.isChecking = false
        }
      },

      async getPluginBindingResources () {
        const apigwId = this.apigwId
        const id = this.curPlugin.id
        try {
          const res = await this.$store.dispatch('gatewayPlugin/getPluginBinding', { apigwId, id })
          this.curStrategyResources = res.data.binds
          this.resourceTargetList = []
          this.resourceTargetListCache = []

          res.data.binds.forEach(item => {
            if (item.scope_type === 'resource') {
              this.scopeIds.push(item.scope_id)
              this.resourceTargetList.push(item.scope_id)
              this.resourceTargetListCache.push(item.scope_id)
            }
          })
        } catch (e) {
          catchErrorHandler(e, this)
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

          res.data.results.forEach(item => {
            item.resourceName = `${item.method}：${item.path}`
          })
          this.resourceList = res.data.results
        } catch (e) {
          catchErrorHandler(e, this)
        }
      },

      unbindOperation () {
        this.unbindResourceConf.isShow = false
        this.isChecking = false
      },

      clearFilterKey () {
        this.keyword = ''
        this.$refs.pluginRef.clearFilter()
        if (this.$refs.pluginRef && this.$refs.pluginRef.$refs.tableHeader) {
          clearFilter(this.$refs.pluginRef.$refs.tableHeader)
        }
      },

      updateTableEmptyConfig () {
        if (this.keyword || this.filterType !== '') {
          this.tableEmptyConf.keyword = 'placeholder'
          return
        }
        this.tableEmptyConf.keyword = ''
      },
            
      // 新建插件成功，提示用户是否绑定环境或资源
      showBindInfo () {
        const isCreate = this.$route.params.isCreate
        const pluginId = this.$route.params.createPluginId

        if (!isCreate && !pluginId) {
          return
        }

        const newPluginData = this.plugins.find(plugin => plugin.id === pluginId) || {}

        this.$nextTick(() => {
          this.$bkInfo({
            type: 'success',
            extCls: 'plugin-info-cls',
            title: this.$t('插件创建成功'),
            width: 540,
            okText: this.$t('立即绑定'),
            cancelText: this.$t('关闭'),
            subTitle: this.$t('插件创建成功后，需要“绑定环境”或“绑定资源”方可生效'),
            confirmFn: () => {
              this.handleEdit(newPluginData, 'stage')
            }
          })
        })
      },
      async handleResourceScroll () {
        this.$nextTick(() => {
          this.sourceEl = document.querySelectorAll('.resource-transfer-wrapper ul.content')
          this.sourceEl.forEach((el) => {
            el.addEventListener('scroll', this.hideToolTips)
          })
        })
      },
      hideToolTips: _.throttle(() => {
        const tipsEl = document.querySelectorAll('.tippy-popper')
        if (tipsEl.length) {
          tipsEl[0].parentNode.removeChild(tipsEl[tipsEl.length - 1])
        }
      }, 60),
      removeResourceScroll () {
        this.sourceEl.forEach((el) => {
          el.removeEventListener('scroll', this.hideToolTips)
        })
      },
      async handleBeforeClose () {
        return this.$isSidebarClosed(JSON.stringify(this.scopeIds))
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
    .transfer-source-item {
        white-space: nowrap;
        text-overflow: ellipsis;
        overflow: hidden;
    }
</style>
<style>
    .plugin-tips-cls .footer-wrapper  button[name=confirm] {
        display: none;
    }
    .bk-dialog-wrapper.plugin-info-cls .bk-info-box .bk-dialog-type-sub-header .header {
        word-wrap: normal;
        word-break: keep-all;
    }
    .bk-dialog-wrapper.info-del-plugin-cls .bk-dialog-header .bk-dialog-header-inner {
        white-space: normal;
        text-overflow: inherit;
        overflow: hidden;
    }
    .bk-dialog-wrapper.info-del-plugin-cls .bk-info-box .bk-dialog-sub-header .bk-dialog-header-inner {
        text-align: center;
    }
    .plugin-tips-cls .bk-dialog .bk-dialog-type-sub-header .header {
        word-break: break-word !important;
    }
</style>
