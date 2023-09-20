<template>
  <div class="app-content apigw-access-manager-wrapper">
    <div :class="['left-system-nav', { 'is-expand': !isExpand }]">
      <div class="left-wrapper">
        <render-system
          :list="systemList"
          ref="systemFilterRef"
          @on-select="handleSelect" />
      </div>
      <div class="handle-icon" @click="isExpand = !isExpand">
        <i class="apigateway-icon icon-ag-down-small"></i>
      </div>
    </div>
    <div :class="['right-wrapper', { 'is-expand': !isExpand }]">
      <ag-loader
        :offset-top="0"
        :offset-left="0"
        loader="stage-loader"
        :is-loading="false">
        <bk-alert
          v-if="needNewVersion && syncEsbToApigwEnabled"
          class="mb15"
          type="warning"
          :title="$t('组件配置有更新，新增组件或更新组件请求方法、请求路径、权限级别、用户认证，需同步到网关才能生效')">
        </bk-alert>
        <div class="search-wrapper">
          <div class="action-wrapper">
            <bk-button
              theme="primary"
              @click="handleCreate">
              {{ $t('新建组件') }}
            </bk-button>
            <bk-button
              :disabled="curSelectList.length < 1"
              @click="handleBatchDelete">
              {{ $t('批量删除') }}
            </bk-button>
            <bk-button
              v-if="syncEsbToApigwEnabled"
              :disabled="isReleasing"
              :icon="isReleasing ? 'loading' : ''"
              @click="handlesync">
              <span v-bk-tooltips="{ content: $t('组件正在同步及发布中，请不要重复操作'), disabled: !isReleasing }"> {{ isReleasing ? $t('正在同步中') : $t('同步到网关') }} </span>
            </bk-button>
          </div>
          <div class="component-flex">
            <bk-input
              style="width: 300px; margin-right: 10px"
              :placeholder="$t('请输入组件名称、请求路径，按Enter搜索')"
              v-model="searchValue"
              clearable
              right-icon="bk-icon icon-search"
              @enter="handleSearch">
            </bk-input>
            <i class="apigateway-icon icon-ag-cc-history history-icon" v-bk-tooltips="$t('查看同步历史')" @click="handlerRouter" v-if="syncEsbToApigwEnabled"></i>
          </div>
        </div>
        <bk-table
          style="margin-top: 16px;"
          :data="componentList"
          :size="setting.size"
          :pagination="pagination"
          v-bkloading="{ isLoading, opacity: 1 }"
          @select="handlerChange"
          @select-all="handlerAllChange"
          @page-change="handlePageChange"
          @row-mouse-enter="changeEnter"
          @row-mouse-leave="changeLeave"
          @page-limit-change="handlePageLimitChange">
          <div slot="empty">
            <table-empty
              :keyword="tableEmptyConf.keyword"
              :abnormal="tableEmptyConf.isAbnormal"
              @reacquire="getComponents(true)"
              @clear-filter="clearFilterKey"
            />
          </div>
          <bk-table-column type="selection" width="60" :selectable="setDefaultSelect"></bk-table-column>
          <bk-table-column :label="$t('系统名称')" prop="system_name" :render-header="$renderHeader">
            <template slot-scope="props">
              {{ props.row.system_name || '--' }}
            </template>
          </bk-table-column>
          <bk-table-column
            v-if="flagComponentName.length"
            :label="$t('组件名称')"
            prop="name"
            key="name"
            :render-header="$renderHeader">
            <template slot-scope="props">
              <div class="ag-flex">
                <span class="ag-auto-text">
                  {{props.row.name || '--'}}
                </span>
                <div v-if="syncEsbToApigwEnabled">
                  <span class="ag-tag primary ml5" v-if="props.row.is_created"> {{ $t('新创建') }} </span>
                  <span class="ag-tag success ml5" v-else-if="props.row.has_updated"> {{ $t('有更新') }} </span>
                </div>
              </div>
            </template>
          </bk-table-column>
          <bk-table-column :label="$t('请求方法')" :width="90" :render-header="$renderHeader">
            <template slot-scope="{ row }">
              {{ row.method || '--' }}
            </template>
          </bk-table-column>
          <bk-table-column
            v-if="flagUrl.length"
            :label="$t('请求路径')"
            prop="path"
            :min-width="220"
            :show-overflow-tooltip="true"
            :render-header="$renderHeader">
          </bk-table-column>
          <bk-table-column
            v-if="flagApiUrl.length"
            :label="$t('API地址')"
            prop="api_url"
            :min-width="180"
            :max-width="260"
            :show-overflow-tooltip="true"
            :render-header="$renderHeader"
          >
            <template slot-scope="{ row }">
              <div class="path-wrapper">
                <span class="path-text">{{row.api_url}}</span>
                <span class="path-icon">
                  <i
                    v-show="cursorId === row.id"
                    class="apigateway-icon icon-ag-clipboard copy-btn"
                    @click="handleClickCopyField(row.api_url)">
                  </i>
                </span>
              </div>
            </template>
          </bk-table-column>
          <bk-table-column
            v-if="flagDocumnetUrl.length"
            :label="$t('文档地址')"
            prop="doc_link"
            :min-width="180"
            :max-width="260"
            :show-overflow-tooltip="true"
            :render-header="$renderHeader"
          >
            <template slot-scope="{ row }">
              <div class="path-wrapper">
                <span class="path-text">{{row.doc_link}}</span>
                <span class="path-icon">
                  <i
                    v-show="cursorId === row.id"
                    class="apigateway-icon icon-ag-clipboard copy-btn"
                    @click="handleClickCopyField(row.doc_link)">
                  </i>
                </span>
              </div>
            </template>
          </bk-table-column>
          <bk-table-column
            v-if="flagUpdatedTime.length"
            :label="$t('更新时间')"
            prop="updated_time"
            :min-width="90"
            :show-overflow-tooltip="true"
            :render-header="$renderHeader"
          ></bk-table-column>
          <bk-table-column :label="$t('操作')" width="150">
            <template slot-scope="{ row }">
              <bk-button theme="primary" class="mr10" text @click="handleEdit(row)"> {{ $t('编辑') }} </bk-button>
              <bk-button
                text
                theme="primary"
                :disabled="row.is_official"
                @click="handleDelete(row)">
                <template v-if="row.is_official">
                  <span v-bk-tooltips="$t('官方组件，不可删除')"> {{ $t('删除') }} </span>
                </template>
                <template v-else>
                  {{ $t('删除') }}
                </template>
              </bk-button>
            </template>
          </bk-table-column>
          <bk-table-column type="setting">
            <bk-table-setting-content
              :fields="setting.fields"
              :selected="setting.selectedFields"
              :size="setting.size"
              :max="setting.max"
              @setting-change="handleSettingChange">
            </bk-table-setting-content>
          </bk-table-column>
        </bk-table>
      </ag-loader>
    </div>

    <bk-sideslider
      :is-show.sync="isSliderShow"
      :width="850"
      :title="sliderTitle"
      :quick-close="true"
      :before-close="handleBeforeClose"
      ext-cls="apigw-access-manager-slider-cls"
      @animation-end="handleAnimationEnd">
      <div slot="content" style="padding: 20px; padding-bottom: 40px;" v-bkloading="{ isLoading: detailLoading, opacity: 1 }">
        <bk-form :label-width="180" :rules="rules" ref="form" :model="formData" v-show="!detailLoading">
          <bk-form-item :label="$t('系统')" :required="true" property="system_id" :error-display-type="'normal'">
            <bk-select
              :disabled="isDisabled"
              :clearable="false"
              v-model="formData.system_id"
              @selected="handleSysSelect">
              <bk-option v-for="option in systemList"
                :key="option.id"
                :id="option.id"
                :name="option.name">
              </bk-option>
            </bk-select>
          </bk-form-item>
          <bk-form-item :label="$t('组件名称simple')" :required="true" property="name" :error-display-type="'normal'">
            <bk-input :maxlength="128" :disabled="isDisabled" v-model="formData.name" :placeholder="$t('由字母、数字、下划线（_）组成，首字符必须是字母，长度小于128个字符')"></bk-input>
            <p class="tips" slot="tip"><i class="apigateway-icon icon-ag-info"></i> {{ $t('组件名称在具体系统下应唯一，将用于展示组件时的标识') }} </p>
          </bk-form-item>
          <bk-form-item :label="$t('组件描述simple')" :required="true" property="description" :error-display-type="'normal'">
            <bk-input :maxlength="128" :disabled="isDisabled" v-model="formData.description" :placeholder="$t('不超过128个字符')"></bk-input>
          </bk-form-item>
          <bk-form-item :label="$t('请求方法')" :required="true" property="method" :error-display-type="'normal'">
            <bk-select
              :disabled="isDisabled"
              :clearable="false"
              v-model="formData.method">
              <bk-option v-for="option in methodList"
                :key="option.id"
                :id="option.id"
                :name="option.name">
              </bk-option>
            </bk-select>
          </bk-form-item>
          <bk-form-item :label="$t('组件路径')" :required="true" property="path" :error-display-type="'normal'">
            <bk-input :disabled="isDisabled" :maxlength="255" v-model="formData.path" :placeholder="$t('以斜杠开头，可包含斜杠、字母、数字、下划线(_)、连接符(-)，长度小于255个字符')"></bk-input>
            <p class="tips" slot="tip"><i class="apigateway-icon icon-ag-info"></i>{{ $t(`可设置为'/{system_name}/{component_name}/'，例如'/host/get_host_list/'`) }}</p>
          </bk-form-item>
          <bk-form-item :label="$t('组件类代号')" :required="true" property="component_codename" :error-display-type="'normal'">
            <bk-input :disabled="isDisabled" v-model="formData.component_codename" :placeholder="$t('包含小写字母、数字、下划线或点号，长度小于255个字符')"></bk-input>
            <p class="tips" slot="tip"><i class="apigateway-icon icon-ag-info"></i>{{ $t('一般由三部分组成：“前缀(generic).小写的系统名.小写的组件类名”，例如 "generic.host.get_host_list"') }}</p>
          </bk-form-item>
          <bk-form-item :label="$t('权限级别')" :required="true" property="permission_level" :error-display-type="'normal'">
            <bk-select :clearable="false" v-model="formData.permission_level">
              <bk-option v-for="option in levelList"
                :key="option.id"
                :id="option.id"
                :name="option.name">
              </bk-option>
            </bk-select>
            <p class="tips" slot="tip"><i class="apigateway-icon icon-ag-info"></i> {{ $t('无权限，应用不需申请组件API权限；普通权限，应用需在开发者中心申请组件API权限，审批通过后访问') }} </p>
          </bk-form-item>
          <bk-form-item :label="$t('用户认证')" :required="true" property="verified_user_required" :error-display-type="'normal'">
            <bk-checkbox
              :true-value="true"
              :false-value="false"
              v-model="formData.verified_user_required">
            </bk-checkbox>
            <p slot="tip" class="ag-tip mt5">
              <i class="apigateway-icon icon-ag-info"></i>
              {{ $t('用户认证，请求方需提供蓝鲸用户身份信息') }}
            </p>
          </bk-form-item>
          <bk-form-item :label="$t('超时时长')">
            <bk-input type="number" :max="600" :min="1" :precision="0" v-model="formData.timeout">
              <section class="timeout-append" slot="append">
                <div>{{$t('秒')}}</div>
              </section>
            </bk-input>
            <p class="tips" slot="tip"><i class="apigateway-icon icon-ag-info"></i> {{ $t('未设置时使用系统的超时时长，最大600秒') }} </p>
          </bk-form-item>
          <bk-form-item :label="$t('组件配置')" v-if="formData.config_fields.length > 0">
            <render-config :list="formData.config_fields" ref="configRef" />
          </bk-form-item>
          <bk-form-item :label="$t('是否开启')">
            <bk-checkbox
              :true-value="true"
              :false-value="false"
              v-model="formData.is_active">
            </bk-checkbox>
          </bk-form-item>
        </bk-form>
      </div>
      <div slot="footer" style="padding-left: 90px;">
        <bk-button
          theme="primary"
          :loading="submitLoading"
          @click="handleSubmit">
          {{ $t('保存') }}
        </bk-button>
        <bk-button style="margin-left: 6px;" theme="default" @click="handleCancel"> {{ $t('取消') }} </bk-button>
      </div>
    </bk-sideslider>

    <bk-dialog
      width="480"
      :mask-close="true"
      v-model="deleteDialogConf.visiable"
      :title="$t('确认删除？')"
      @after-leave="handleAfterLeave">
      <div> {{ $t('该操作不可恢复，是否继续？') }} </div>
      <template slot="footer">
        <bk-button
          theme="primary"
          :loading="deleteDialogConf.loading"
          @click="handleDeleteComponent">
          {{ $t('确定') }}
        </bk-button>
        <bk-button theme="default" @click="deleteDialogConf.visiable = false"> {{ $t('取消') }} </bk-button>
      </template>
    </bk-dialog>
  </div>
</template>
<script>
  import { catchErrorHandler } from '@/common/util'
  import RenderSystem from './components/render-system'
  import RenderConfig from './components/config'
  import sidebarMixin from '@/mixins/sidebar-mixin'

  const getDefaultData = () => {
    return {
      system_id: '',
      name: '',
      description: '',
      method: '',
      path: '',
      component_codename: ``,
      permission_level: '',
      timeout: 30,
      is_active: true,
      config_fields: [],
      verified_user_required: true
    }
  }

  export default {
    name: '',
    components: {
      RenderSystem,
      RenderConfig
    },
    mixins: [sidebarMixin],
    data () {
      const fields = [{
        id: 'systemName',
        label: this.$t('系统名称'),
        disabled: true
      }, {
        id: 'componentName',
        label: this.$t('组件名称')
      }, {
        id: 'type',
        label: this.$t('请求方法'),
        disabled: true
      }, {
        id: 'url',
        label: this.$t('请求路径')
      }, {
        id: 'updated_time',
        label: this.$t('更新时间')
      }, {
        id: 'api_url',
        label: this.$t('API地址')
      }, {
        id: 'documnet_url',
        label: this.$t('文档地址')
      }]
      return {
        searchValue: '',
        componentList: [],
        pagination: {
          current: 1,
          count: 0,
          limit: 10
        },
        formData: getDefaultData(),
        componentData: {},
        isSliderShow: false,
        systemList: [],
        methodList: [
          {
            id: 'GET',
            name: 'GET'
          },
          {
            id: 'POST',
            name: 'POST'
          },
          {
            id: 'PUT',
            name: 'PUT'
          },
          {
            id: 'PATCH',
            name: 'PATCH'
          },
          {
            id: 'DELETE',
            name: 'DELETE'
          },
          {
            id: '*',
            name: 'GET/POST'
          }
        ],
        levelList: [
          {
            id: 'unlimited',
            name: this.$t('无限制')
          },
          {
            id: 'normal',
            name: this.$t('普通')
          }
        ],
        requestQueue: ['system', 'component'],
        allData: [],
        displayData: [],
        submitLoading: false,
        isLoading: false,
        curSelectList: [],
        deleteDialogConf: {
          visiable: false,
          loading: false,
          ids: []
        },
        detailLoading: false,
        isReleasing: false,
        needNewVersion: false,
        versionMessage: '',
        isCursor: false,
        cursorId: '',
        setting: {
          max: 9,
          fields: fields,
          selectedFields: fields.slice(0, 5),
          size: 'small'
        },
        syncEsbToApigwEnabled: false,
        tableEmptyConf: {
          keyword: '',
          isAbnormal: false
        },
        isExpand: true
      }
    },
    computed: {
      isEdit () {
        return Object.keys(this.componentData).length > 0
      },
      isDisabled () {
        return this.isEdit && this.componentData.is_official
      },
      sliderTitle () {
        return this.isEdit ? this.$t('编辑组件') : this.$t('新建组件')
      },
      flagComponentName () {
        return this.setting.selectedFields.filter(v => v.label === this.$t('组件名称'))
      },
      flagUrl () {
        return this.setting.selectedFields.filter(v => v.label === this.$t('请求路径'))
      },
      flagApiUrl () {
        return this.setting.selectedFields.filter(v => v.label === this.$t('API地址'))
      },
      flagDocumnetUrl () {
        return this.setting.selectedFields.filter(v => v.label === this.$t('文档地址'))
      },
      flagUpdatedTime () {
        return this.setting.selectedFields.filter(v => v.label === this.$t('更新时间'))
      }
    },
    watch: {
      searchValue (newVal, oldVal) {
        if (newVal === '' && oldVal !== '' && this.isFilter) {
          this.isFilter = false
          this.pagination.current = 1
          this.pagination.limit = 10
          this.displayData = this.allData
          this.pagination.count = this.displayData.length
          this.componentList = this.getDataByPage()
        }
      },
      requestQueue (value) {
        if (value.length < 1) {
          this.$store.commit('setMainContentLoading', false)
        }
      }
    },
    created () {
      this.init()
      this.curSelectSystemId = '*'
      this.isFilter = false
      this.rules = {
        system_id: [
          {
            required: true,
            message: this.$t('必填项'),
            trigger: 'blur'
          }
        ],
        name: [
          {
            required: true,
            message: this.$t('必填项'),
            trigger: 'blur'
          },
          {
            regex: /^[a-zA-Z][a-zA-Z0-9_]{0,128}$|^$/,
            message: this.$t('由字母、数字、下划线（_）组成，首字符必须是字母，长度小于128个字符'),
            trigger: 'blur'
          }
        ],
        description: [
          {
            required: true,
            message: this.$t('必填项'),
            trigger: 'blur'
          }
        ],
        method: [
          {
            required: true,
            message: this.$t('必填项'),
            trigger: 'blur'
          }
        ],
        component_codename: [
          {
            required: true,
            message: this.$t('必填项'),
            trigger: 'blur'
          }
        ],
        path: [
          {
            required: true,
            message: this.$t('必填项'),
            trigger: 'blur'
          },
          {
            regex: /^\/[\w{}/.-]*$/,
            message: this.$t('以斜杠开头，可包含斜杠、字母、数字、下划线(_)、连接符(-)，长度小于255个字符'),
            trigger: 'blur'
          }
        ],
        permission_level: [
          {
            required: true,
            message: this.$t('必填项'),
            trigger: 'blur'
          }
        ],
        verified_user_required: [
          {
            required: true,
            message: this.$t('必填项'),
            trigger: 'blur'
          }
        ]
      }
    },
    methods: {
      init () {
        this.getSystemList()
        this.getComponents()
        this.getStatus()
        this.getFeature()
      },

      async getComponents (isLoading = false) {
        this.isLoading = isLoading
        try {
          const res = await this.$store.dispatch('component/getComponents')
          this.allData = Object.freeze(res.data)
          this.displayData = res.data
          this.pagination.count = this.displayData.length
          this.componentList = this.getDataByPage()
          if (this.curSelectSystemId !== '*') {
            this.handleSelect({ id: this.curSelectSystemId })
          }
          this.tableEmptyConf.isAbnormal = false
        } catch (e) {
          this.tableEmptyConf.isAbnormal = true
          catchErrorHandler(e, this)
        } finally {
          if (this.requestQueue.length > 0) {
            this.requestQueue.shift()
          }
          this.isLoading = false
        }
      },

      setDefaultSelect (payload) {
        return !payload.is_official
      },

      handlerChange (payload) {
        this.curSelectList = [...payload]
      },

      handlerAllChange (payload) {
        this.curSelectList = [...payload]
      },

      handleSysSelect (value, option) {
        const tempList = this.formData.component_codename.split('.')
        let customStr = ''
        if (tempList.length === 3) {
          customStr = tempList[2]
        }
        this.formData.component_codename = `generic.${option.lowerName}.${customStr}`
        this.$refs.systemFilterRef.setSelected(value)
      },

      async getSystemList () {
        try {
          const res = await this.$store.dispatch('system/getSystems')
          this.systemList = Object.freeze(res.data)
          // 获取组件是否需要发版本更新
          this.checkNeedNewVersion()
          // 子组件状态更新
          this.$nextTick(() => {
            this.$refs.systemFilterRef && this.$refs.systemFilterRef.updateTableEmptyConfig()
          })
        } catch (e) {
          catchErrorHandler(e, this)
        } finally {
          if (this.requestQueue.length > 0) {
            this.requestQueue.shift()
          }
        }
      },

      async checkNeedNewVersion () {
        try {
          const res = await this.$store.dispatch('component/checkNeedNewVersion')
          this.needNewVersion = res.data.need_new_release
        } catch (e) {
          // catchErrorHandler(e, this)
          this.needNewVersion = false
        }
      },

      handleCancel () {
        this.isSliderShow = false
      },

      handleSubmit () {
        this.$refs.form.validate().then(async validator => {
          this.submitLoading = true
          const tempData = Object.assign({}, this.formData)
          if (!tempData.timeout) {
            tempData.timeout = null
          }
          if (tempData.method === '*') {
            tempData.method = ''
          }
          if (tempData.config_fields.length > 0) {
            tempData.config = this.$refs.configRef.getData()
            delete tempData.config_fields
          }
          if (!this.isEdit) {
            delete tempData.config_fields
          }
          try {
            const methods = this.isEdit ? 'updateComponent' : 'addComponent'
            const params = this.isEdit ? {
              id: this.componentData.id,
              data: tempData
            } : tempData
            await this.$store.dispatch(`component/${methods}`, params)
            this.isSliderShow = false
            this.getComponents(true)
            this.getSystemList()
          } catch (e) {
            catchErrorHandler(e, this)
          } finally {
            this.submitLoading = false
          }
        }, validator => {
          console.error(validator)
        })
      },

      handleAnimationEnd () {
        this.componentData = {}
        this.formData = Object.assign({}, getDefaultData())
      },

      handleSelect ({ id }) {
        this.curSelectSystemId = id
        if (this.curSelectSystemId === '*') {
          this.displayData = this.allData
        } else {
          this.displayData = this.allData.filter(item => item.system_id === this.curSelectSystemId)
        }
        this.pagination.current = 1
        this.pagination.limit = 10
        this.pagination.count = this.displayData.length
        this.componentList = this.getDataByPage()
      },

      handleCreate () {
        this.componentData = {}
        const curSystem = this.systemList.find(item => item.id === this.curSelectSystemId)
        let curSystemName = ''
        if (curSystem) {
          curSystemName = curSystem.name.toLocaleLowerCase()
        }
        this.formData = Object.assign(getDefaultData(), {
          method: 'GET',
          permission_level: 'unlimited',
          system_id: this.curSelectSystemId === '*' ? '' : this.curSelectSystemId,
          component_codename: curSystemName === '' ? 'generic.{system_name}' : `generic.${curSystemName}.`
        })
        this.isSliderShow = true
        this.$nextTick(() => {
          // 收集初始化状态
          this.initSidebarFormData(this.formData)
        })
      },

      handleSearch (payload) {
        if (payload === '') {
          return
        }
        this.pagination.current = 1
        this.pagination.limit = 10
        this.isFilter = true
        this.displayData = this.allData.filter(item => {
          const reg = new RegExp('(' + payload + ')', 'gi')
          return item.path.match(reg) || item.name.match(reg)
        })
        this.pagination.count = this.displayData.length
        this.componentList = this.getDataByPage()
      },

      handlePageLimitChange (limit) {
        this.pagination.limit = limit
        this.pagination.current = 1
        this.handlePageChange(this.pagination.current)
      },

      handlePageChange (page) {
        this.pagination.current = page
        const data = this.getDataByPage(page)
        this.componentList.splice(0, this.componentList.length, ...data)
      },

      getDataByPage (page) {
        if (!page) {
          this.pagination.current = page = 1
        }
        let startIndex = (page - 1) * this.pagination.limit
        let endIndex = page * this.pagination.limit
        if (startIndex < 0) {
          startIndex = 0
        }
        if (endIndex > this.displayData.length) {
          endIndex = this.displayData.length
        }
        this.updateTableEmptyConfig()
        return this.displayData.slice(startIndex, endIndex)
      },

      async handleEdit (payload) {
        this.componentData = Object.assign({}, payload)
        this.isSliderShow = true
        this.detailLoading = true
        try {
          const res = await this.$store.dispatch('component/getComponentsDetail', {
            id: this.componentData.id
          })
          const {
            name,
            description,
            method,
            path,
            timeout
          } = res.data
          this.formData.description = description
          this.formData.name = name
          this.formData.method = method === '' ? '*' : method
          this.formData.path = path
          this.formData.timeout = timeout
          this.formData.system_id = res.data.system_id
          this.formData.component_codename = res.data.component_codename
          this.formData.permission_level = res.data.permission_level
          this.formData.is_active = res.data.is_active
          this.formData.config_fields = res.data.config_fields || []
          this.formData.verified_user_required = res.data.verified_user_required
          this.$nextTick(() => {
            this.initSidebarFormData(this.formData)
          })
        } catch (e) {
          console.warn(e)
          return false
        } finally {
          this.detailLoading = false
        }
      },

      handleAfterLeave () {
        this.deleteDialogConf.ids = []
      },

      async handleDeleteComponent () {
        this.deleteDialogConf.loading = true
        try {
          await this.$store.dispatch('component/deleteComponentByBatch', {
            ids: this.deleteDialogConf.ids
          })
          this.$bkMessage({
            message: this.$t('删除成功'),
            theme: 'success'
          })
          this.deleteDialogConf.visiable = false
          this.curSelectList = []
          this.getComponents(true)
          this.getSystemList()
          return true
        } catch (e) {
          console.warn(e)
          return false
        } finally {
          this.deleteDialogConf.loading = false
        }
      },

      handleBatchDelete () {
        this.deleteDialogConf.ids = [...this.curSelectList.map(item => item.id)]
        this.deleteDialogConf.visiable = true
      },

      handleDelete ({ id }) {
        this.deleteDialogConf.ids.push(id)
        this.deleteDialogConf.visiable = true
      },

      async getStatus () {
        try {
          const res = await this.$store.dispatch('component/getReleaseStatus')
          this.isReleasing = res.data.is_releasing
          if (this.isReleasing) {
            setTimeout(() => {
              this.getStatus()
            }, 5000)
          }
        } catch (e) {
          console.warn(e)
          return false
        }
      },

      async handlesync () {
        this.$router.push({
          name: 'syncApigwAccess'
        })
      },

      handlerRouter () {
        this.$router.push({
          name: 'syncHistory'
        })
      },

      handleClickCopyField (field) {
        this.$copyText(field).then((e) => {
          this.$bkMessage({
            theme: 'success',
            limit: 1,
            message: this.$t('复制成功')
          })
        }, () => {
          this.$bkMessage({
            theme: 'error',
            limit: 1,
            message: this.$t('复制失败')
          })
        })
      },

      changeEnter (col, even, rowData) {
        this.cursorId = rowData.id
        this.isCursor = true
      },

      changeLeave (row) {
        this.cursorId = ''
        this.isCursor = false
      },

      handleSettingChange ({ fields, size }) {
        this.setting.size = size
        this.setting.selectedFields = fields
      },

      async getFeature () {
        try {
          const res = await this.$store.dispatch('apis/getFeature')
          this.syncEsbToApigwEnabled = res.data.SYNC_ESB_TO_APIGW_ENABLED
        } catch (e) {
          catchErrorHandler(e, this)
        }
      },

      clearFilterKey () {
        this.searchValue = ''
      },

      updateTableEmptyConfig () {
        this.tableEmptyConf.keyword = this.searchValue
      },
            
      // 侧栏关闭处理操作
      async handleBeforeClose () {
        return this.$isSidebarClosed(JSON.stringify(this.formData))
      }
    }
  }
</script>
<style lang="postcss" scoped>
    .app-content {
        min-height: calc(100vh - 104px);
        padding: 0;
    }
    .apigw-access-manager-wrapper {
        background: #fff;
        display: flex;
        justify-content: flex-start;
        .left-system-nav {
            position: relative;
            max-height: calc(100vh - 104px);
            background: #fff;
            width: 300px;
            &.is-expand {
                width: 0;
                .left-wrapper {
                    width: 0;
                }
                .handle-icon i {
                    transform: rotate(270deg);
                }
            }
        }
        .left-wrapper {
            padding: 10px 0;
            margin-right: 16px;
            width: 300px;
            overflow: hidden;
            height: 100%;
            background: #f6f7fb;
        }
        .handle-icon  {
            position: absolute;
            top: 50%;
            transform: translateY(-50%);
            right: -16px;
            width: 16px;
            height: 64px;
            background: #DCDEE5;
            border-radius: 0 4px 4px 0;
            cursor: pointer;
            display: flex;
            align-items: center;

            i {
                display: inline-block;
                margin-left: -5px;
                font-size: 24px;
                color: #fff;
                transform: rotate(90deg);
            }
        }
        .right-wrapper {
            padding: 0 10px;
            margin: 24px;
            width: calc(100% - 348px);
            &.is-expand {
                margin-left: 20px;
                width: calc(100% - 40px);
            }
            
        }
        .search-wrapper {
            display: flex;
            justify-content: space-between;
        }
        .component-flex{
            display: flex;
            justify-content: space-between;
            align-items: center;
            .history-icon{
                cursor: pointer;
                display: inline-block;
                height: 32px;
                line-height: 32px;
                width: 30px;
                border: 1px solid #c4c6cc;
                border-radius: 2px;
                background: #fff;
                color: #979ba5;
                &:hover {
                    border-color: #979ba5;
                    color: #63656e;
                }
            }
        }
        .bk-table {
            .api-name,
            .docu-link {
                max-width: 200px;
                display: inline-block;
                word-break: break-all;
                overflow: hidden;
                white-space: nowrap;
                text-overflow: ellipsis;
                vertical-align: bottom;
            }
            .copy-icon {
                font-size: 14px;
                cursor: pointer;
                &:hover {
                    color: #3a84ff;
                }
            }
        }
    }
    .apigw-access-manager-slider-cls {
        .tips {
            line-height: 24px;
            font-size: 12px;
            color: #63656e;
            i {
                position: relative;
                top: -1px;
                margin-right: 3px;
            }
        }
        .timeout-append {
            width: 50px;
            line-height: 32px;
            font-size: 12px;
            text-align: center;
        }
    }

    .ag-flex {
        display: flex;
    }
    .ag-auto-text {
        vertical-align: middle;
    }
    .ag-tag.success {
        width: 44px;
    }

    .path-wrapper {
        position: relative;
        display: flex;
        width: 100%;
    }

    .path-text{
        display: inline-block;
        width: 200px;
        overflow: hidden;
        text-overflow:ellipsis; white-space: nowrap;
    }
    .path-icon {
        position: absolute;
        right: 0px;
        cursor: pointer;
        color: #3a84ff;
    }

    .copyCursor {
        cursor : pointer;
    }
</style>
<style>
    .tippy-content{
        max-width: 550px;
    }
    .bk-table-setting-content{
        width: 550px;
    }
</style>
