<template>
  <div class="app-content">
    <bk-tab
      :active.sync="bindTabActive"
      :ext-cls="'ag-bind-tab form-tab-wrapper'"
      @tab-change="activeTab">
      <bk-tab-panel
        :label="$t('基本信息')"
        :name="'baseInfo'">
        <bk-form
          ref="form"
          :label-width="180"
          :model="curPlugin"
          class="pl20 pr20"
          style="max-width: 1280px;">
          <bk-form-item
            :label="$t('名称')"
            :required="true"
            :rules="rules.name"
            :property="'name'"
            :error-display-type="'normal'">
            <bk-input :placeholder="$t('请输入')" v-model="curPlugin.name"></bk-input>
          </bk-form-item>
          <bk-form-item
            :label="$t('插件')"
            :required="true"
            :rules="rules.type"
            :property="'type'"
            :error-display-type="'normal'">
            <bk-select v-model="curPlugin.type_id" @selected="typeSelect" :disabled="typeDisabled">
              <bk-option
                v-for="option in typeList"
                :key="option.code"
                :id="option.id"
                :name="option.name">
              </bk-option>
            </bk-select>
          </bk-form-item>
          <bk-form-item :label="$t('描述')">
            <bk-input type="textarea" v-model="curPlugin.description"></bk-input>
          </bk-form-item>

          <!-- 免用户认证应用白名单策略 -->
          <bk-form-item label="" v-if="curPlugin.type === bkVerifiedUserExemptedApps">
            <div class="white-list">
              <whitelist-table ref="whitelist" :type="plugType" :yaml-str="content" @parmas-yaml="getUserExemptedAppsYaml"></whitelist-table>
            </div>
          </bk-form-item>
                    
          <!-- style=raw 时，直接渲染 code-viewer -->
          <bk-form-item :label="$t('插件配置')" v-else-if="renderingMethod === 'raw'">
            <code-viewer
              ref="bodyCodeViewer"
              :value="content"
              :width="'100%'"
              :height="yamlViewerHeight"
              :lang="'yaml'"
              :key="uploadButtonKey"
              @input="handleInput"
              @focus="isViewerFocus = true"
              @blur="isViewerFocus = false">
            </code-viewer>
          </bk-form-item>

          <!-- style=dynamic 时，才读取 config 字段渲染动态表单 -->
          <BkSchemaForm
            v-if="isDynamicForm && renderingMethod === 'dynamic'"
            class="mt20"
            v-model="schemaFormData"
            ref="bkForm"
            :label-width="180"
            :schema="formConfig.schema"
            :layout="formConfig.layout"
            :rules="formConfig.rules">
          </BkSchemaForm>

          <bk-form-item class="mt20" v-if="typeSchemaDataNotes">
            <bk-alert type="info" :title="$t(typeSchemaDataNotes)"></bk-alert>
          </bk-form-item>

          <bk-form-item>
            <section class="ag-panel-action">
              <div class="panel-content">
                <div class="panel-wrapper tc mt20">
                  <bk-button class="mr5" theme="primary" style="width: 120px;" @click="submitApigwPlugin" :loading="isDataLoading"> {{ $t('提交') }} </bk-button>
                  <bk-button style="width: 120px;" @click="handleApigwPluginCancel"> {{ $t('取消') }} </bk-button>
                </div>
              </div>
            </section>
          </bk-form-item>
        </bk-form>
      </bk-tab-panel>

      <bk-tab-panel
        v-if="plugType === 'edit'"
        :name="'stage'"
        :label="$t('绑定环境列表')"
        style="padding-left: 20px; padding-right: 20px;">
        <bk-button
          class="mr10"
          @click="handleBatchUnbindStage">
          {{ $t('批量解绑') }}
        </bk-button>
        <bk-button
          @click="handleBindStage">
          {{ $t('绑定环境') }}
        </bk-button>
        <bk-table
          v-bkloading="{ isLoading: isStageLoading, zIndex: 10 }"
          ref="tabStage"
          style="margin-top: 15px;"
          :data="stageBindList"
          :size="'small'"
          @selection-change="handleStageSelect">
          <div slot="empty">
            <table-empty empty />
          </div>
          <bk-table-column type="selection" width="60" align="center"></bk-table-column>
          <bk-table-column :label="$t('环境名称')" prop="name" :render-header="$renderHeader"></bk-table-column>
          <bk-table-column :label="$t('环境描述')" prop="description" :render-header="$renderHeader"></bk-table-column>
          <bk-table-column :label="$t('操作')" width="200">
            <template slot-scope="props">
              <bk-popconfirm
                placement="top"
                @confirm="handleUnbindStage(props.row)">
                <bk-button theme="primary" text> {{ $t('解绑') }} </bk-button>
              </bk-popconfirm>
            </template>
          </bk-table-column>
        </bk-table>
      </bk-tab-panel>

      <bk-tab-panel
        v-if="plugType === 'edit' && curPlugin.type !== bkVerifiedUserExemptedApps"
        :name="'resource'"
        :label="$t('绑定资源列表')"
        style="padding-left: 20px; padding-right: 20px;">
        <bk-button
          class="mr10"
          @click="handleBatchUnbindResource">
          {{ $t('批量解绑') }}
        </bk-button>
        <bk-button
          @click="handleBindResource">
          {{ $t('绑定资源') }}
        </bk-button>
        <bk-table
          v-bkloading="{ isLoading: isResourceLoading, zIndex: 10 }"
          ref="tabResource"
          style="margin-top: 15px;"
          :data="resourceBindList"
          :size="'small'"
          @selection-change="handleResourceSelect">
          <div slot="empty">
            <table-empty empty />
          </div>
          <bk-table-column type="selection" width="60" align="center"></bk-table-column>
          <bk-table-column :label="$t('请求路径')" prop="path" :render-header="$renderHeader"></bk-table-column>
          <bk-table-column :label="$t('请求方法')" prop="method" :render-header="$renderHeader"></bk-table-column>
          <bk-table-column :label="$t('操作')" width="200">
            <template slot-scope="props">
              <bk-popconfirm
                placement="top"
                @confirm="handleUnbindResource(props.row)">
                <bk-button theme="primary" text> {{ $t('解绑') }} </bk-button>
              </bk-popconfirm>
            </template>
          </bk-table-column>
        </bk-table>
      </bk-tab-panel>

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
        :is-show.sync="stageBindSliderConf.isShow"
        :quick-close="true"
        :before-close="handleBeforeClose">
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
    </bk-tab>

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
          <bk-table-column :label="$t('原插件')">
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
  import { catchErrorHandler, sortByKey, json2yaml } from '@/common/util'
  import whitelistTable from './whitelist-table.vue'
  import createForm from '@blueking/bkui-form'
  import jsYaml from 'js-yaml'
  import '@blueking/bkui-form/dist/bkui-form.css'
  import _ from 'lodash'
  import sidebarMixin from '@/mixins/sidebar-mixin'

  const BkSchemaForm = createForm()

  export default {
    components: { whitelistTable, BkSchemaForm },
    mixins: [sidebarMixin],
    data () {
      return {
        content: '',
        typeList: [],
        curPlugin: {
          name: '',
          type: '',
          description: '',
          id: 0,
          type_id: ''
        },
        bindTabActive: this.$route.query.TabActive || 'baseInfo',
        yamlViewerHeight: 300,
        uploadButtonKey: 0,
        isViewerFocus: false,
        isDataLoading: false,
        rules: {
          name: [
            {
              required: true,
              message: this.$t('必填项'),
              trigger: 'blur'
            }
          ],
          type: [
            {
              required: true,
              message: this.$t('必填项'),
              trigger: 'blur'
            }
          ]
        },
        showDoc: false,
        docsTip: {
          theme: 'dark',
          allowHtml: true,
          content: this.$t('提示信息'),
          html: `${this.$t('Swagger 协议中描述了接口说明，利用其中内容生成资源文档')}，<a target="_blank" href=${this.GLOBAL_CONFIG.DOC.IMPORT_RESOURCE_DOCS} style="color: #3a84ff">${this.$t('更多详情')}</a>`,
          placements: ['top']
        },
        language: 'zh',
        resource: {
          content: '',
          allow_overwrite: true
        },
        userExemptedAppsConf: {},
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
        scopeIds: [],
        isChecking: false,
        unbindResourceConf: {
          isShow: false
        },
        bindChangeResources: [],
        tableIndex: 0,
        mergeResources: [],
        unbindResources: [],
        stageList: [],
        resourceList: [],
        curStrategyStages: [],
        stageUnbindList: [],
        renderTransferIndex: 0,
        resourceTargetList: [],
        curStrategyResources: [],
        resourceTargetListCache: [],
        resourceUnbindList: [],
        typeDisabled: false,

        formConfig: {},
        schemaFormData: {},
        schemaYaml: '',
        isDynamicForm: false,
        context: {
          baseURL: ''
        },
        isResourceLoading: false,
        isStageLoading: false,
        renderingMethod: '',
        typeSchemaDataNotes: '',
        sourceEl: null,
        curPluginType: '',
        bkVerifiedUserExemptedApps: 'bk-verified-user-exempted-apps'
      }
    },
    computed: {
      apigwId () {
        return this.$route.params.id
      },
      strategyId () {
        return this.$route.query.stageId
      },
      plugId () {
        return this.$route.query.plugId
      },
      pluginTypeId () {
        return this.$route.query.typeId
      },
      plugType () {
        return this.$route.query.type || 'create'
      },
      stageSelect () {
        const apigwList = this.$store.state.apis.apigwList
        const toApigwId = this.apigwId
        const result = apigwList.find(item => {
          return String(item.id) === String(toApigwId)
        })
        return result.stages
      },
      stageBindList () {
        const results = []
        this.curStrategyStages.forEach(item => {
          const matchItem = this.stageList.find(stage => item.scope_id === stage.id)

          if (matchItem) {
            results.push({
              id: matchItem.id,
              name: matchItem.name,
              description: matchItem.description || '--'
            })
          }
        })
        return results
      },

      // 资源数据
      resourceBindList () {
        const results = []
        this.curStrategyResources.forEach(item => {
          const matchItem = this.resourceList.find(resource => item.scope_id === resource.id)
          if (matchItem) {
            results.push({
              id: matchItem.id,
              path: matchItem.path,
              method: matchItem.method,
              description: matchItem.description || '--'
            })
          }
        })
        return sortByKey(results, 'path')
      }
    },

    watch: {
      'curPlugin.type': {
        handler (newVal, oldVal) {
          if (newVal && newVal !== oldVal) {
            this.isDynamicForm = newVal !== this.bkVerifiedUserExemptedApps && this.curPluginType !== this.bkVerifiedUserExemptedApps
            if (this.isDynamicForm) {
              this.fetchDynamicFormData(this.curPlugin.type_id)
            } else {
              this.typeSchemaDataNotes = ''
              this.schemaFormData = {}
            }
          }
        },
        deep: true
      }
    },

    created () {
      this.init()
    },

    methods: {
      async init () {
        await this.getPluginType()
        this.getApigwStages()
        if (this.plugType === 'edit') {
          this.typeDisabled = true
          this.getIdPlugin()
          this.getApigwResources()
        }
        this.isPageLoading = false
        this.$store.commit('setMainContentLoading', false)
      },

      // 获取插件类型
      async getPluginType () {
        const apigwId = this.apigwId
        try {
          const res = await this.$store.dispatch('gatewayPlugin/getPluginType', { apigwId })
          // 启用插件不展示私有化类型
          if (this.plugType === 'edit') {
            this.typeList = res.data.results
          } else {
            this.typeList = res.data.results.filter(plugin => plugin.is_public)
          }
          const pluginData = res.data.results.find(item => item.id === Number(this.pluginTypeId)) || {}
          this.curPluginType = pluginData.code
          // 新建插件默认插件类型为第一项
          if (this.plugType !== 'edit') {
            this.curPlugin.id = this.typeList[0].id
            this.curPlugin.type = this.typeList[0].code
            this.curPlugin.type_id = this.typeList[0].id
          }
        } catch (e) {
          catchErrorHandler(e, this)
        }
      },

      activeTab (name) {
        this.scopeIds = []
        if (name !== 'baseInfo') {
          if (name === 'stage') {
            this.getPluginBinding('loading')
          } else {
            this.getPluginBindingResources('loading')
          }
          this.$refs.tabStage.doLayout()
        }
        if (name === 'stage') {
          this.$nextTick(() => {
            this.$refs.tabStage.doLayout()
          })
        }
      },

      async typeSelect (formId) {
        const typeData = this.typeList.find(v => v.id === formId)
        this.curPlugin.type = typeData.code
      },

      async fetchDynamicFormData (formId) {
        const apigwId = this.apigwId
        try {
          const res = await this.$store.dispatch('gatewayPlugin/getDynamicForm', { apigwId, formId })
          this.renderingMethod = res.data.style || 'raw'
          this.typeSchemaDataNotes = res.data.notes || ''
          if (res.data.style === 'raw') {
            this.uploadButtonKey++
            this.content = res.data.default_value || ''
          } else {
            if (this.plugType !== 'edit') {
              this.schemaFormData = {}
            }
            this.formConfig = res.data.config
          }
        } catch (e) {
          catchErrorHandler(e, this)
        }
      },

      setContent (val) {
        this.content = val
      },

      submitApigwPlugin () {
        const formArr = [this.$refs.form.validate()]
        // 动态表单校验
        if (this.$refs.bkForm) {
          formArr.push(this.$refs.bkForm.validate())
        }
        Promise.all(formArr).then(validator => {
          this.schemaYaml = json2yaml(JSON.stringify(this.schemaFormData)).data
          if (this.$refs.whitelist) {
            this.$refs.whitelist.sendPolicyData()
          }
          if (this.plugType === 'create') {
            this.submitApigwPluginPost()
          } else {
            this.submitApigwPluginEdit()
          }
          this.isDataLoading = false
        }).catch(validator => {
          this.isDataLoading = false
          console.error(validator)
        })
      },

      // 新建插件
      async submitApigwPluginPost () {
        const apigwId = this.apigwId
        const data = {
          name: this.curPlugin.name,
          type_id: this.curPlugin.type_id,
          description: this.curPlugin.description
        }
        if (this.curPlugin.type === this.bkVerifiedUserExemptedApps) {
          // 免认证白名单
          data.yaml = this.userExemptedAppsConf
        } else {
          if (this.renderingMethod === 'raw') {
            data.yaml = this.content
          } else {
            // 动态表单
            data.yaml = this.schemaYaml
          }
        }
        try {
          const res = await this.$store.dispatch('gatewayPlugin/createPlugin', { apigwId, data })
          this.$router.push({
            name: 'apigwGatewayPlugin',
            params: {
              isLeave: true,
              isCreate: true,
              createPluginId: res.data.id
            }
          })
        } catch (e) {
          catchErrorHandler(e, this)
        }
      },

      // 编辑插件
      async submitApigwPluginEdit () {
        const apigwId = this.apigwId
        const id = this.plugId
        const data = {
          name: this.curPlugin.name,
          type_id: this.curPlugin.type_id,
          description: this.curPlugin.description
        }
        if (this.curPlugin.type === this.bkVerifiedUserExemptedApps) {
          // 免认证白名单
          data.yaml = this.userExemptedAppsConf
        } else {
          if (this.renderingMethod === 'raw') {
            data.yaml = this.content
          } else {
            // 动态表单
            data.yaml = this.schemaYaml
          }
        }
        try {
          await this.$store.dispatch('gatewayPlugin/updatePlugin', { apigwId, id, data })
          this.$bkMessage({
            theme: 'success',
            message: this.$t('更新网关插件成功')
          })
          this.$router.push({
            name: 'apigwGatewayPlugin'
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

      // 获取插件详情
      async getIdPlugin () {
        const apigwId = this.apigwId
        const id = this.plugId
        try {
          const { data } = await this.$store.dispatch('gatewayPlugin/getIdPlugin', { apigwId, id })
          this.curPlugin = data
          this.curPlugin.type = data.type_code
          // style=raw 与 免认证白名单
          this.content = data.yaml
          // 动态表单
          this.schemaFormData = jsYaml.load(data.yaml)
        } catch (e) {
          catchErrorHandler(e, this)
        }
      },

      handleInput (content) {
        this.content = content
      },

      handleApigwPluginCancel () {
        this.$router.push({
          name: 'apigwGatewayPlugin',
          params: {
            id: this.apigwId
          }
        })
      },

      handleStageSelect (selectedList) {
        this.stageUnbindList = selectedList
      },

      handleResourceChange (sourceList, targetList, targetValueList) {
        this.scopeIds = targetValueList
      },
            
      async handleUnbindStage (stage) {
        const apigwId = this.apigwId
        const id = this.plugId
        const data = {
          scope_type: 'stage',
          scope_ids: [],
          dry_run: false
        }

        if (Array.isArray(stage)) {
          stage.forEach(item => {
            data.scope_ids.push(item.id)
          })
        } else {
          data.scope_ids.push(stage.id)
        }
        try {
          await this.$store.dispatch('gatewayPlugin/deletePluginBinding', { apigwId, id, data })
          this.$bkMessage({
            theme: 'success',
            message: this.$t('解绑环境成功')
          })
          this.getPluginBinding('loading')
        } catch (e) {
          catchErrorHandler(e, this)
        }
      },

      handleBatchUnbindStage () {
        const self = this
        if (!this.stageUnbindList.length) {
          this.$bkMessage({
            theme: 'error',
            message: this.$t('请选择要解绑的环境')
          })
          return false
        }

        this.$bkInfo({
          title: this.$t('确认要批量解绑环境？'),
          confirmFn () {
            self.handleUnbindStage(self.stageUnbindList)
          }
        })
      },

      handleFileInput () {
        const fileInput = this.$refs.fileInput
        const self = this
        if (fileInput.files && fileInput.files.length) {
          const file = fileInput.files[0]
          if (window.FileReader) {
            const reader = new FileReader()
            reader.onloadend = function (event) {
              if (event.target.readyState === FileReader.DONE) {
                self.content = event.target.result
                self.resource.content = event.target.result
                setTimeout(() => {
                  self.$refs.bodyCodeViewer.$ace.scrollToLine(1, true, true)
                  self.$refs.bodyCodeViewer.$ace.scrollToLine(1, true, true)
                }, 0)
                self.uploadButtonKey++
              }
            }
            reader.readAsText(file)
          }
        }
      },

      // 获取已绑定环境列表
      async getPluginBinding (isLoading = false) {
        if (isLoading) {
          this.isStageLoading = true
        }
        const apigwId = this.apigwId
        const id = this.plugId
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
        } finally {
          setTimeout(() => {
            this.isStageLoading = false
          }, 200)
        }
      },

      // 获取资源列表
      async getPluginBindingResources (isLoading = false) {
        if (isLoading) {
          this.isResourceLoading = true
        }
        const apigwId = this.apigwId
        const id = this.plugId
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
        } finally {
          setTimeout(() => {
            this.isResourceLoading = false
          }, 200)
        }
      },

      handleBatchUnbindResource () {
        const self = this
        if (!this.resourceUnbindList.length) {
          this.$bkMessage({
            theme: 'error',
            message: this.$t('请选择要解绑的资源')
          })
          return false
        }

        this.$bkInfo({
          title: this.$t('确认要批量解绑资源？'),
          confirmFn () {
            self.handleUnbindResource(self.resourceUnbindList)
          }
        })
      },

      async handleBindResource () {
        this.scopeIds = []
        this.curPlugin.scope_type = 'resource'
        this.renderTransferIndex++
        this.resourceBindSliderConf.isShow = true
        await this.getPluginBindingResources()
        this.handleResourceScroll()
        // 收集状态
        this.initSidebarFormData(this.scopeIds)
      },

      async handleBindStage () {
        this.scopeIds = []
        this.curPlugin.scope_type = 'stage'
        this.stageBindSliderConf.isShow = true
        await this.getPluginBinding()
        // 收集状态
        this.initSidebarFormData(this.scopeIds)
      },

      handleResourceSelect (selectedList) {
        this.resourceUnbindList = selectedList
      },
            
      // 绑定环境
      async submitStagePluginBinding () {
        const apigwId = this.apigwId
        const id = this.plugId
        // dry_run: true（为diff获取） false （为真实绑定）
        const data = {
          scope_type: 'stage',
          scope_ids: this.scopeIds,
          type: this.curPlugin.type,
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
          this.getPluginBinding('loading')
        } catch (e) {
          catchErrorHandler(e, this)
        } finally {
          this.isChecking = false
        }
      },

      async submitresourcePluginBinding () {
        const apigwId = this.apigwId
        const id = this.plugId
        const data = {
          scope_type: 'resource',
          scope_ids: this.scopeIds,
          type: this.curPlugin.type,
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
          this.getPluginBindingResources('loading')
        } catch (e) {
          catchErrorHandler(e, this)
        } finally {
          this.isChecking = false
        }
      },

      submitBindingData () {
        if (this.curPlugin.scope_type === 'stage') {
          this.submitStagePluginBinding()
        } else {
          this.submitresourcePluginBinding()
        }
      },

      async handleUnbindResource (resource) {
        const apigwId = this.apigwId
        const id = this.plugId
        const data = {
          scope_type: 'resource',
          scope_ids: [],
          dry_run: false
        }

        if (Array.isArray(resource)) {
          resource.forEach(item => {
            data.scope_ids.push(item.id)
          })
        } else {
          data.scope_ids.push(resource.id)
        }
        try {
          await this.$store.dispatch('gatewayPlugin/deletePluginBinding', { apigwId, id, data })
          this.$bkMessage({
            theme: 'success',
            message: this.$t('解绑资源成功')
          })
          this.getPluginBindingResources('loading')
        } catch (e) {
          catchErrorHandler(e, this)
        }
      },

      // 绑定环境/资源Diff
      async checkBindeStage (type) {
        this.isChecking = true

        const apigwId = this.apigwId
        const id = this.plugId
        const originList = this.curPlugin.scope_type === 'stage' ? this.stageList : this.resourceList
        const data = {
          scope_type: type,
          scope_ids: this.scopeIds,
          type: this.curPlugin.type,
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

      handleHideStageSlider () {
        this.stageBindSliderConf.isShow = false
      },

      handleHideResourceSlider () {
        this.resourceBindSliderConf.isShow = false
      },

      getUserExemptedAppsYaml (yamlData) {
        if (!yamlData.error) {
          this.userExemptedAppsConf = yamlData.data
        }
      },

      unbindOperation () {
        this.unbindResourceConf.isShow = false
        this.isChecking = false
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
    .token-area {
        border-radius: 2px;
        border: 1px solid #F0F1F5;
        background: #FAFBFD;
        padding: 20px;
    }

    .import-btn {
        position: relative;
        overflow: hidden;
        padding-left: 10px;
        .file-input {
            position: absolute;
            width: 100%;
            height: 100px;
            left: 0;
            right: 0;
            bottom: 0;
            top: 0;
            opacity: 0;
            cursor: pointer;
        }
    }

    .import-tip {
        vertical-align: middle;
        font-size: 12px;
        color: #979ba5;
    }

    .ag-radio-header{
        width: auto;
        margin: 0 32px 0 0;
        display: flex;
        align-items: center;
    }
    .mt10  {
        margin-top: 6px !important;
    }
    .ag-bind-tab ::v-deep .bk-form-content>[name].bk-form-control {
        display: inline-block;
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
</style>
