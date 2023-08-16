<template>
  <div class="app-content online-test">
    <div class="panel-content">
      <div class="request-panel">
        <div class="panel-title"> {{ $t('请求') }} </div>
        <bk-form ref="form" :label-width="120">
          <bk-form-item :label="$t('环境')" :property="'name'">
            <bk-select
              :clearable="false"
              searchable
              v-model="params.stage_id"
              @change="handleStageChange">
              <bk-option v-for="option in stageList"
                :key="option.id"
                :id="option.id"
                :name="option.name">
              </bk-option>
            </bk-select>
          </bk-form-item>
          <bk-form-item :required="true" :label="$t('请求资源')" :error-display-type="'normal'">
            <bk-select
              :clearable="false"
              searchable
              v-model="formData.path"
              @change="handleResourceChange">
              <bk-option v-for="option in resourceList"
                :key="option"
                :id="option"
                :name="option">
              </bk-option>
            </bk-select>
            <div class="resource-empty" v-show="!isPageLoading && resourceEmpty">
              {{ $t('未找到可用的请求资源，因为当前选择环境未发布版本，请先发布版本到该环境') }}
            </div>
            <p class="ag-tip mt5" slot="tip">
              <i class="apigateway-icon icon-ag-info"></i>{{ $t('资源必须发布到对应环境，才支持选择及调试') }}
            </p>
          </bk-form-item>
          <bk-form-item :required="true" :label="$t('请求方法')" :error-display-type="'normal'">
            <bk-select
              :clearable="false"
              v-model="formData.method"
              @change="handleMethodChange">
              <bk-option v-for="option in methodList"
                :key="option.id"
                :id="option.id"
                :name="option.name">
              </bk-option>
            </bk-select>
          </bk-form-item>
          <bk-form-item :label="$t('子路径')" v-if="isMatchAnyMethod || isShowSubpath">
            <bk-input v-model="formData.subpath"></bk-input>
            <p class="ag-tip mt5">
              <i class="apigateway-icon icon-ag-info"></i>
              {{ $t('请求资源中，资源请求路径*部分的子路径') }}
            </p>
          </bk-form-item>
          <bk-form-item
            v-show="hasPathParmas"
            :required="true"
            :label="$t('路径参数')">
            <apigw-key-valuer
              style="margin-right: 69px;"
              class="kv-wrapper"
              ref="pathKeyValuer"
              :key-readonly="true"
              :key-regex-rule="{}"
              :buttons="false"
              :value="formData.params.path">
            </apigw-key-valuer>
          </bk-form-item>
          <bk-form-item
            label="Headers">
            <apigw-key-valuer
              class="kv-wrapper"
              ref="headerKeyValuer"
              :value="formData.headers"
              @toggle-height="controlToggle">
            </apigw-key-valuer>
          </bk-form-item>
          <bk-form-item
            label="Query">
            <apigw-key-valuer
              class="kv-wrapper"
              ref="queryKeyValuer"
              :key-regex-rule="{ regex: /^[\w-]+$/, message: $t('键由英文字母、数字、连接符（-）、下划线（_）组成') }"
              :value="formData.params.query"
              @toggle-height="controlToggle">
            </apigw-key-valuer>
          </bk-form-item>
          <bk-form-item label="Body">
            <bk-input
              class="ag-textarea"
              ext-cls="body-textarea"
              type="textarea"
              :placeholder="$t('请输入')"
              v-model="params.body">
            </bk-input>
          </bk-form-item>
          <bk-form-item :label="$t('online-test-应用认证')">
            <div class="bk-button-group">
              <bk-button
                class="ag-tab-button"
                :class="{ 'is-selected': isDefaultAppAuth }"
                @click="formData.appAuth = 'use_test_app'">
                {{ $t('默认测试应用') }}
              </bk-button>
              <bk-button
                class="ag-tab-button"
                :class="{ 'is-selected': formData.appAuth === 'use_custom_app' }"
                @click="formData.appAuth = 'use_custom_app'">
                {{ $t('自定义应用') }}
              </bk-button>
            </div>
            <template v-if="isDefaultAppAuth">
              <bk-input
                class="mt5"
                :value="testAppCode"
                :disabled="true"
                :placeholder="$t('请输入蓝鲸应用ID')">
                <template slot="prepend">
                  <div class="group-text" style="width: 130px; text-align: right;">bk_app_code</div>
                </template>
              </bk-input>
              <bk-input
                class="mt5"
                :value="'******'"
                :disabled="true"
                :placeholder="$t('请输入蓝鲸应用密钥')">
                <template slot="prepend">
                  <div class="group-text" style="width: 130px; text-align: right;">bk_app_secret</div>
                </template>
              </bk-input>
            </template>
            <template v-else>
              <bk-input
                class="mt5"
                v-model="formData.authorization.bk_app_code"
                :placeholder="$t('请输入蓝鲸应用ID')">
                <template slot="prepend">
                  <div class="group-text" style="width: 130px; text-align: right;">bk_app_code</div>
                </template>
              </bk-input>
              <bk-input
                class="mt5"
                v-model="formData.authorization.bk_app_secret"
                :placeholder="$t('请输入蓝鲸应用密钥')">
                <template slot="prepend">
                  <div class="group-text" style="width: 130px; text-align: right;">bk_app_secret</div>
                </template>
              </bk-input>
            </template>
            <p class="ag-tip mt5">
              <i class="apigateway-icon icon-ag-info"></i>
              {{ $t('默认测试应用，网关自动为其短期授权；自定义应用，需主动为应用授权资源访问权限') }}
            </p>
          </bk-form-item>
          <bk-form-item :label="$t('online-test-用户认证')" :key="tokenInputRender" v-if="curResource.verified_user_required">
            <div class="bk-button-group">
              <bk-button
                class="ag-tab-button"
                :class="{ 'is-selected': formData.useUserFromCookies }"
                @click="formData.useUserFromCookies = true">
                {{ $t('默认用户认证') }}
              </bk-button>
              <bk-button
                class="ag-tab-button"
                :class="{ 'is-selected': !formData.useUserFromCookies }"
                @click="formData.useUserFromCookies = false">
                {{ $t('自定义用户认证') }}
              </bk-button>
            </div>
            <template>
              <template v-if="formData.useUserFromCookies">
                <bk-input
                  v-for="(item, index) in cookieNames"
                  class="mt5 token-input"
                  v-model="userPlaceholder"
                  :key="index"
                  :disabled="true">
                  <template slot="prepend">
                    <div class="group-text" style="width: 130px; text-align: right;">{{item[0]}}</div>
                  </template>
                </bk-input>
              </template>
              <!-- 自定义 -->
              <template v-else>
                <bk-input
                  v-for="(item, index) in cookieNames"
                  class="mt5 token-input"
                  v-model="formData.authorization[item[0]]"
                  :placeholder="$t(`请输入 Cookies 中字段 {tokenName} 的值`, { tokenName: item[1] })"
                  :key="index">
                  <template slot="prepend">
                    <div class="group-text" style="width: 130px; text-align: right;">{{item[0]}}</div>
                  </template>
                </bk-input>
              </template>
              <p class="ag-tip mt5">
                <i class="apigateway-icon icon-ag-info"></i>
                {{ $t('默认用户认证，将默认从 Cookies 中获取用户认证信息；自定义用户认证，可自定义用户认证信息') }}
              </p>
            </template>
          </bk-form-item>
        </bk-form>
        <div class="footer-btn-wrapper">
          <bk-button
            v-if="!sendButtonDisabled"
            theme="primary"
            class="mr10"
            :loading="requestStatus === 0"
            @click.stop.prevent="handleSendRequest">
            {{ $t('发送请求') }}
          </bk-button>
          <bk-popover :content="$t('请完善请求信息')" v-else>
            <bk-button
              theme="primary"
              class="mr10"
              disabled>
              {{ $t('发送请求') }}
            </bk-button>
          </bk-popover>
          <bk-button
            theme="default"
            @click.stop.prevent="handleReset"> {{ $t('重置') }} </bk-button>
        </div>
      </div>
      <div class="divider"></div>
      <div class="response-panel">
        <div class="panel-title"> {{ $t('请求详情') }} </div>
        <div class="request-detail">
          <div v-if="requestStatus !== -1">{{response.curl}}</div>
          <div v-else>
            <i class="apigateway-icon icon-ag-info"></i>
            {{ $t('无') }}
          </div>
        </div>
        <div class="panel-title"> {{ $t('响应') }} </div>
        <template v-if="requestStatus !== -1">
          <bk-form class="response-form" :label-width="90">
            <bk-form-item label="Time：" ext-cls="response-form-item">
              <span class="value">{{response.proxy_time}}</span>
              <span class="unit"> {{ $t('毫秒') }} </span>
            </bk-form-item>
            <bk-form-item label="Status：" ext-cls="response-form-item">
              <span class="value">{{response.status_code}}</span>
            </bk-form-item>
            <bk-form-item label="Size：" ext-cls="response-form-item">
              <span class="value">{{response.size}}</span>
              <span class="unit">KB</span>
            </bk-form-item>
            <bk-form-item :label-width="0" ext-cls="response-form-item code">
              <bk-tab :active.sync="responseActiveTab" ext-cls="response-content-tab" @tab-change="tabchange">
                <bk-tab-panel name="body" label="Body">
                  <div class="tab-content body">
                    <code-viewer
                      ref="bodyCodeViewer"
                      :value="formattedResBody"
                      :width="'100%'"
                      :height="460"
                      :lang="isResponseBodyJson ? 'json' : 'text'"
                      :read-only="true">
                    </code-viewer>
                  </div>
                </bk-tab-panel>
                <bk-tab-panel name="headers" label="Headers">
                  <div class="tab-content headers">
                    <code-viewer
                      ref="headerCodeViewer"
                      :value="formattedResHeaders"
                      :width="'100%'"
                      :height="460"
                      :lang="'json'"
                      :read-only="true">
                    </code-viewer>
                  </div>
                </bk-tab-panel>
              </bk-tab>
            </bk-form-item>
          </bk-form>
        </template>
        <div v-else>
          <span class="unsent">
            <i class="apigateway-icon icon-ag-info"></i>
            {{ $t('请先发送请求') }}
          </span>
        </div>
      </div>
    </div>
    <!-- 吸顶按钮组 -->
    <div class="fixed-footer-btn-wrapper" :style="{ paddingLeft: fixedLeft + 'px' }" v-show="isAdsorb">
      <bk-button
        v-if="!sendButtonDisabled"
        theme="primary"
        class="mr10"
        :loading="requestStatus === 0"
        @click.stop.prevent="handleSendRequest">
        {{ $t('发送请求') }}
      </bk-button>
      <bk-popover :content="$t('请完善请求信息')" v-else>
        <bk-button
          theme="primary"
          class="mr10"
          disabled>
          {{ $t('发送请求') }}
        </bk-button>
      </bk-popover>
      <bk-button
        theme="default"
        @click.stop.prevent="handleReset"> {{ $t('重置') }} </bk-button>
    </div>
  </div>
</template>

<script>
  import { mapGetters } from 'vuex'
  import ApigwKeyValuer from '@/components/key-valuer'
  import { catchErrorHandler } from '@/common/util'
  import { bus } from '@/common/bus'
  import { cloneDeep } from 'lodash'

  const defaultValue = {
    params: {
      stage_id: '',
      resource_id: '',
      method: '',
      headers: {},
      path_params: {},
      query_params: {},
      body: '',
      use_test_app: true
    },
    formData: {
      path: '',
      method: '',
      subpath: '',
      appAuth: 'use_test_app',
      authorization: {
        'bk_app_code': '',
        'bk_app_secret': '',
        'uin': '',
        'skey': ''
      },
      params: {
        path: {},
        query: {}
      },
      headers: {},
      // 用户认证
      useUserFromCookies: true
    }
  }

  const expandWidth = 384
  const awayWidth = 204

  export default {
    components: {
      ApigwKeyValuer
    },
    data () {
      return {
        isPageLoading: true,
        requestStatus: -1,
        stageList: [],
        resources: {},
        methodList: [],
        responseActiveTab: 'body',
        params: { ...defaultValue.params },
        formData: { ...defaultValue.formData },
        response: {},
        isResponseBodyJson: false,
        isMatchAnyMethod: false,
        tokenInputRender: 0,
        curApigw: {
          name: '',
          description: '',
          status: 0,
          statusBoolean: false,
          statusForFe: false,
          is_public: true,
          user_auth_type: '',
          maintainers: [],
          maintainersForFe: []
        },
        testAppCode: BK_TEST_APP_CODE,
        cookieNames: [],
        isAdsorb: false,
        fixedLeft: expandWidth,
        userPlaceholder: '******'
      }
    },
    computed: {
      ...mapGetters('options', { allMethodList: 'methodList' }),
      apigwId () {
        return this.$route.params.id
      },
      resourceList () {
        return Object.keys(this.resources)
      },
      resourceEmpty () {
        return !this.resourceList.length
      },
      hasPathParmas () {
        return Object.keys(this.formData.params.path).length > 0
      },
      sendButtonDisabled () {
        return this.resourceEmpty || !this.params.resource_id
      },
      formattedResBody () {
        let body = this.response.body
        try {
          const bodyJSON = JSON.parse(this.response.body)
          body = JSON.stringify(bodyJSON, null, 4)
        } catch (e) {
          // nothing
        }
        return body
      },
      formattedResHeaders () {
        return JSON.stringify(this.response.headers, null, 4)
      },
      isShowSubpath () {
        if (this.formData.method && this.formData.path) {
          let paths = []
          const resourceId = this.formData.method.split('_')[0]
          for (const key in this.resources) {
            if (key === this.formData.path) {
              paths = this.resources[key]
            }
          }
          const resource = paths.find(item => String(item.id) === String(resourceId))
          return resource && resource.match_subpath
        }
        return false
      },
      authTypeDetail () {
        const types = this.$store.state.userAuthType
        const match = types.find(item => item.name === this.curApigw.user_auth_type)
        return match
      },
      tokenName () {
        if (!this.authTypeDetail) {
          return 'bk_ticket'
        } else {
          const tokens = this.authTypeDetail.login_ticket.key_to_cookie_name
          if (tokens.length) {
            this.cookieNames = tokens
            return tokens[0][0]
          }
          return 'bk_ticket'
        }
      },
      curResource () {
        if (this.resources[this.formData.path]) {
          return this.resources[this.formData.path][0] || {}
        }
        return {}
      },
      isDefaultAppAuth () {
        return this.formData.appAuth === 'use_test_app'
      }
    },
    watch: {
      'response.body' (body) {
        try {
          const bodyJson = JSON.parse(body)
          this.isResponseBodyJson = bodyJson && typeof bodyJson === 'object'
        } catch (e) {
          this.isResponseBodyJson = false
        }
      },
      'isShowSubpath' () {
        this.formData.subpath = ''
      }
    },
    created () {
      this.init()
      // 导航是否收起
      bus.$on('nav-toggle', (opened) => {
        this.fixedLeft = opened ? expandWidth : awayWidth
      })
    },
    mounted () {
      this.$nextTick(() => {
        // 初始化判断按钮组是否吸附
        this.controlToggle()
        this.observerBtnScroll()
      })
    },
    beforeDestroy () {
      this.destroyEvent()
      this.clearAuthData()
    },
    methods: {
      async init () {
        this.getApigwStages()
        await this.getApigwDetail()
        this.setUserToken()
      },
      async getApigwReleaseResources () {
        const apigwId = this.apigwId
        const stageId = this.params.stage_id

        try {
          const res = await this.$store.dispatch('release/getApigwReleaseResources', { apigwId, stageId })
          this.resources = res.data || []

          // 环境变更会触发资源列表更新，资源更新后需要清空已有的选择
          this.formData.path = ''
          this.formData.method = ''
        } catch (e) {
          catchErrorHandler(e, this)
        } finally {
          this.isPageLoading = false
          this.$store.commit('setMainContentLoading', false)
        }
      },
      async getApigwStages () {
        const apigwId = this.apigwId
        const pageParams = {
          no_page: true,
          order_by: 'name'
        }

        try {
          const res = await this.$store.dispatch('stage/getApigwStages', { apigwId, pageParams })
          this.stageList = res.data.results

          this.params.stage_id = (this.stageList[0] || {}).id
        } catch (e) {
          catchErrorHandler(e, this)
        }
      },
      async postApigwAPITest (data) {
        const apigwId = this.apigwId
        this.requestStatus = 0
        try {
          const res = await this.$store.dispatch('apiTest/postApigwAPITest', { apigwId, data })

          this.response = res.data

          this.$nextTick(() => {
            this.$refs.bodyCodeViewer.$ace.scrollToLine(1, true, true)
            this.$refs.headerCodeViewer.$ace.scrollToLine(1, true, true)
          })
        } catch (e) {
          catchErrorHandler(e, this)
        } finally {
          this.responseActiveTab = 'body'
          this.requestStatus = 1
        }
      },
      tabchange (name) {
        this.$nextTick(() => {
          if (name === 'headers') {
            this.$refs.headerCodeViewer.$ace.setValue(this.formattedResHeaders, 1)
          } else {
            this.$refs.bodyCodeViewer.$ace.setValue(this.formattedResBody, 1)
          }
        })
      },
      checkFormData (data) {
        const pathParams = Object.values(data.path_params)
        const reg = /^[\w{}/.-]*$/
        const codeReg = /^[a-z][a-z0-9-_]+$/
        if ((this.isMatchAnyMethod || this.isShowSubpath) && !reg.test(data.subpath)) {
          this.$bkMessage({
            theme: 'error',
            message: this.$t('请输入合法的子路径')
          })
          this.$refs.form.validate()
          return false
        }
        if (this.hasPathParmas && pathParams.some(val => !val.length)) {
          this.$bkMessage({
            theme: 'error',
            message: this.$t('请输入完整的路径参数')
          })
          this.$refs.form.validate()
          return false
        }
        if (data.authorization.bk_app_code && !codeReg.test(data.authorization.bk_app_code)) {
          this.$bkMessage({
            theme: 'error',
            delay: 5000,
            message: this.$t('应用ID格式不正确，只能包含：小写字母、数字、连字符(-)、下划线(_)，首字母必须是字母')
          })
          return false
        }

        return true
      },
      async handleSendRequest () {
        this.params.headers = this.$refs.headerKeyValuer.getValue()
        this.params.query_params = this.$refs.queryKeyValuer.getValue()
        this.params.path_params = this.$refs.pathKeyValuer.getValue()
        this.params.subpath = this.isMatchAnyMethod || this.isShowSubpath ? this.formData.subpath : ''
        // 用户认证
        this.params.use_user_from_cookies = this.curResource.verified_user_required ? this.formData.useUserFromCookies : false
        this.params.authorization = this.formData.authorization
        this.params.use_test_app = this.isDefaultAppAuth
        const data = cloneDeep(this.params)

        // 默认应用认证数据过滤
        if (this.isDefaultAppAuth) {
          data.authorization.bk_app_secret = ''
          data.authorization.bk_app_code = ''
        }
        // 默认用户认证数据过滤
        if (this.formData.useUserFromCookies) {
          this.cookieNames.forEach(item => {
            data.authorization[item[0]] = ''
          })
        }
                
        try {
          await this.$refs.form.validate()

          if (this.checkFormData(data)) {
            this.postApigwAPITest(data)
          }
        } catch (e) {
          console.error(e)
        }
      },
      handleResourceChange (value) {
        // 环境/资源/方法类似三级联动，上级改变了下级值需要清空
        this.formData.method = ''

        // 重置选择后value可能为空
        const resourceList = this.resources[value] || []
        // 取得指定资源路径下的请求方法列表
        this.methodList = resourceList.map(resource => ({
          id: `${resource.id}_${resource.method}`,
          name: resource.method
        }))

        // 只有一个时，any需要转换为全部，否则默认选中
        if (this.methodList.length === 1) {
          if (this.methodList[0].name === 'ANY') {
            this.methodList = this.allMethodList.slice(0, -1)
            this.isMatchAnyMethod = true
          } else {
            this.formData.method = this.methodList[0].id
            this.isMatchAnyMethod = false
          }
        }

        this.formData.params.path = {}
        if (value) {
          const matches = value.matchAll(/{([\w-]+?)}/g)
          for (const match of matches) {
            this.formData.params.path[match[1]] = ''
          }
        }
      },
      handleMethodChange (value) {
        const methodValue = value.split('_')
        const path = this.formData.path
        const resourceList = this.resources[path] || []

        // 路径与方法确定一个资源
        const resource = resourceList.find(resource => resource.path === path && resource.method === methodValue[1])

        if (resource) {
          this.params.resource_id = resource.id
          this.params.method = resource.method
        } else if (resourceList.length && value) {
          // 存在资源但匹配不到则认为是any，any取第一个元素的id
          this.params.resource_id = resourceList[0].id
          // any没有id值，[0]元素即为method名称
          this.params.method = methodValue[0]
        } else {
          this.params.resource_id = ''
          this.params.method = ''
        }
      },
      handleStageChange () {
        this.getApigwReleaseResources()
      },
      handleReset () {
        const params = { ...defaultValue.params }
        params.stage_id = this.params.stage_id
        this.params = params
        this.formData = { ...defaultValue.formData }
        this.formData.params.query = {}
        this.formData.headers = {}
        this.formData.authorization = {
          'bk_app_code': '',
          'bk_app_secret': '',
          'uin': '',
          'skey': '',
          'bk_ticket': ''
        }
        this.$nextTick(() => {
          this.controlToggle()
        })
      },
      handleAuthChange (index, data) {
        this.formData.authorization['bk_app_code'] = ''
        this.formData.authorization['bk_app_secret'] = ''
      },
      async getApigwDetail () {
        const apigwId = this.$route.params.id

        try {
          const res = await this.$store.dispatch('apis/getApisDetail', apigwId)
          this.curApigw = res.data
          this.curApigw.statusBoolean = Boolean(this.curApigw.status)
        } catch (e) {
          catchErrorHandler(e, this)
        }
      },

      setUserToken () {
        this.formData.authorization[this.tokenName] = ''
        this.tokenInputRender++
      },

      // 元素滚动判断元素是否吸顶
      controlToggle () {
        const el = document.querySelector('.footer-btn-wrapper')
        const bottomDistance = this.getDistanceToBottom(el)
        const maxDistance = 1000
        // 是否吸附
        if (bottomDistance < 25 || bottomDistance > maxDistance) {
          this.isAdsorb = true
          el.classList.add('is-pinned')
        } else {
          this.isAdsorb = false
          el.classList.remove('is-pinned')
        }
      },

      observerBtnScroll () {
        const container = document.querySelector('.container-content')
        container.addEventListener('scroll', this.controlToggle)
      },

      destroyEvent () {
        const container = document.querySelector('.container-content')
        container.removeEventListener('scroll', this.controlToggle)
      },

      // 获取按钮底部距离
      getDistanceToBottom (element) {
        const rect = element && element.getBoundingClientRect()
        return Math.max(0, window.innerHeight - rect.bottom)
      },

      clearAuthData () {
        this.formData.authorization.bk_app_secret = ''
        this.formData.authorization.bk_app_code = ''
        this.cookieNames.forEach(item => {
          this.formData.authorization[item[0]] = ''
        })
      }
    }
  }
</script>

<style lang="postcss" scoped>
    @import '@/css/variable.css';

    .panel-content {
        display: flex;
        min-height: calc(100vh - 260px);

        .request-panel {
            flex: 1;
            min-width: 590px;
            padding-bottom: 60px;

            .resource-empty {
                font-size: 12px;
                color: $fontColor;
            }

            .auth-checkbox {
                line-height: 32px;
            }

            /deep/.kv-wrapper {
                margin-bottom: 0;

                .values {
                    width: 100%;

                    .biz-key-item {
                        display: flex;
                        align-items: center;

                        .bk-form {
                            flex: 1;

                        }
                        .operator + .bk-form {
                            flex: 2;
                        }

                        &:last-child {
                            margin-bottom: 0;
                        }
                    }
                }
            }
        }
        .response-panel {
            flex: 1;
            max-width: 100%;

            .unsent {
                color: $fontColor;
                font-size: 14px;
                margin-left: 12px;
            }
        }

        .panel-title {
            font-size: 14px;
            font-weight: 700;
            color: #313238;
            margin-bottom: 16px;
        }

        .divider {
            flex: none;
            margin: 0 40px;
            width: 1px;
            background: #DCDEE5;
        }

        .response-form {
            .bk-form-item + .bk-form-item {
                margin-top: 0px;
            }
        }

        .response-form-item {
            /deep/.bk-form-content {
                display: flex;
                align-items: center;
                font-size: unset;

                .value {
                    font-size: 12px;
                    color: #313238;
                }

                .unit {
                    font-size: 12px;
                    color: #63656E;
                    margin-left: 4px;
                }
            }

            &.code {
                /deep/.bk-label {
                    padding: 0;
                }
            }
        }

        .response-content-tab {
            width: 100%;
            background: #fff;
            margin-top: 10px;

            .tab-content {
                padding: 0 16px;
                color: $fontColor;
                font-size: 14px;
                min-height: 70px;
                line-height: 22px;
            }
        }

        .request-detail {
            background: #fff;
            padding: 8px 12px;
            margin-bottom: 48px;
            font-size: 14px;
            line-height: 22px;
            color: #63656E;
            font-family: 'Courier New', Courier, monospace;
        }

        .form-wrap {
            display: flex;
            margin-top: 10px;

            .label {
                width: 120px;
                font-size: 14px;
                text-align: right;
            }
            .input-wrap {
                flex: 1;
            }
        }

        .wrapper {
            display: flex;
            border: 1px solid #dcdee5;
            margin-top: 10px;
            background: #FFF;
            border-radius: 2px;
            
            .left {
                width: 70px;
                text-align: center;
                line-height: 95px;
                background: #f1f4f8;
                border-right: 1px solid #dcdee5;
            }

            .right {
                padding: 10px;
                flex: 1;
            }
        }
    }

    /deep/ .token-input {
        .right-icon {
            right: 65px !important;
        }
    }

    .ag-inner-btn {
        background: #3a84ff;
        color: #FFF !important;
        width: 60px;
        height: 30px;
        line-height: 30px;
        border-radius: 0 2px 2px 0;
        font-size: 13px;
        text-align: center;
        -webkit-box-shadow: 0px 0 0px 1px #3a84ff;
        box-shadow: 0px 0 0px 1px #3a84ff;
        cursor: pointer;
    }

    .footer-btn-wrapper {
        position: sticky;
        bottom: 0;
        margin-top: 8px;
        height: 52px;
        background: #f6f7fb;
        padding-left: 120px;
        width: 101%;
        display: flex;
        align-items: center;
        z-index: 9;
    }
    .fixed-footer-btn-wrapper {
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        padding: 10px 0;
        background: #fff;
        box-shadow: 0 -2px 4px 0 #0000000f;
        z-index: 9;
        transition: .3s;
    }
    .is-pinned {
        opacity: 0;
    }
    .user-tips {
        font-size: 12px;
        color: #63656E;
        line-height: 16px;
    }
    .online-test /deep/ .panel-content .request-panel[data-v-c1d2eab6] .kv-wrapper .values .biz-key-item {
      align-items: unset;
    }

    .body-textarea /deep/ .bk-textarea-wrapper {
      width: 100%;
    }
</style>
