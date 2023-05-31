<template>
  <div class="component-doc">
    <div class="component-content">
      <div class="component-metedata mb10">
        <strong class="name mr5" v-bk-tooltips.top="curComponent.name">{{curComponent.name || '--'}}</strong>
        <span class="label" v-bk-tooltips.top="{ content: curComponent.description, allowHTML: false }">{{curComponent.description || $t('暂无描述')}}</span>
      </div>
      <div style="position: relative;">
        <bk-breadcrumb separator-class="bk-icon icon-angle-right" class="mb20">
          <bk-breadcrumb-item :to="{ name: 'apigwDoc' }"> {{ $t('网关API文档') }} </bk-breadcrumb-item>
          <bk-breadcrumb-item>{{curApigw.name || '--'}}</bk-breadcrumb-item>
          <bk-breadcrumb-item>{{curComponent.name || '--'}}</bk-breadcrumb-item>
        </bk-breadcrumb>

        <chat
          class="ag-chat"
          v-if="GLOBAL_CONFIG.PLATFORM_FEATURE.ALLOW_CREATE_APPCHAT"
          :default-user-list="userList"
          :owner="curUser.username"
          :name="chatName"
          :content="chatContent"
          :is-query="true">
        </chat>
      </div>

      <bk-tab :active.sync="active" class="bk-special-tab">
        <bk-tab-panel
          :name="'doc'"
          :label="$t('文档')">
          <div class="ag-kv-box mb30">
            <div class="kv-row">
              <div class="k"> {{ $t('更新时间') }}: </div>
              <div class="v">{{curDocUpdated || '--'}}</div>
            </div>
            <div class="kv-row">
              <div class="k"> {{ $t('应用认证') }} <i class="ml5 bk-icon icon-question-circle" v-bk-tooltips="$t('应用访问该网关API时，是否需提供应用认证信息')"></i>：</div>
              <div class="v">{{curComponent.app_verified_required ? $t('是') : $t('否')}}</div>
            </div>
            <div class="kv-row">
              <div class="k"> {{ $t('用户认证') }} <i class="ml5 bk-icon icon-question-circle" v-bk-tooltips="$t('应用访问该组件API时，是否需要提供用户认证信息')"></i>：</div>
              <div class="v">{{curComponent.user_verified_required ? $t('是') : $t('否')}}</div>
            </div>
            <div class="kv-row">
              <div class="k"> {{ $t('是否需申请权限') }} <i class="ml5 bk-icon icon-question-circle" v-bk-tooltips="$t('应用访问该网关API前，是否需要在开发者中心申请该网关API权限')"></i>：</div>
              <div class="v">{{curComponent.resource_perm_required ? $t('是') : $t('否')}}</div>
            </div>
          </div>
          <div class="ag-markdown-view" id="markdown" :key="renderHtmlIndex" v-html="curComponent.markdownHtml"></div>
          <zan class="mt30 mb50" v-if="GLOBAL_CONFIG.PLATFORM_FEATURE.ENABLE_FEEDBACK"></zan>
        </bk-tab-panel>
        <bk-tab-panel
          :name="'sdk'"
          :label="$t('SDK及示例')"
          v-if="GLOBAL_CONFIG.PLATFORM_FEATURE.ENABLE_SDK">
          <div id="sdk-markdown">
            <div class="bk-button-group">
              <bk-button class="is-selected">Python</bk-button>
              <!-- <bk-button disabled>GO</bk-button> -->
            </div>

            <h3 class="f16">
              {{ $t('SDK信息-doc') }}
              <span class="ag-tip ml10" v-if="!curSdk.sdk_version_number">
                ({{ SDKInfo }})
              </span>
            </h3>
                        
            <div>
              <sdk-detail :params="curSdk" :is-apigw="true"></sdk-detail>
            </div>
                        
            <h3 class="f16 mt20"> {{ $t('SDK使用样例') }} </h3>
            <div class="ag-markdown-view mt20" :key="renderHtmlIndex" v-html="sdkMarkdownHtml"></div>
            <zan class="mt30 mb50" v-if="GLOBAL_CONFIG.PLATFORM_FEATURE.ENABLE_FEEDBACK"></zan>
          </div>
        </bk-tab-panel>
      </bk-tab>
    </div>

    <div class="component-nav-box">
      <div style="position: fixed;">
        <side-nav :list="componentNavList" v-if="active === 'doc'"></side-nav>
        <side-nav :list="sdkNavList" v-else></side-nav>
      </div>
    </div>
        
  </div>
</template>

<script>
  import { catchErrorHandler } from '@/common/util'
  import MarkdownIt from 'markdown-it'
  import Clipboard from 'clipboard'
  import { slugify } from 'transliteration'
  import chat from '@/components/chat'
  import sdkDetail from '@/components/sdk-detail'
  import hljs from 'highlight.js'
  import zan from '@/components/zan'
  import 'highlight.js/styles/monokai-sublime.css'

  const md = new MarkdownIt({
    linkify: false,
    html: true,
    breaks: true,
    highlight (str, lang) {
      if (lang && hljs.getLanguage(lang)) {
        try {
          return hljs.highlight(lang, str, true).value
        } catch (__) {}
      }

      return ''
    }
  })

  export default {
    components: {
      chat,
      sdkDetail,
      zan
    },
    data () {
      return {
        curStage: '',
        curApigwId: '',
        curResourceId: '',
        curComponentName: '',
        renderHtmlIndex: 0,
        active: 'doc',
        curDocUpdated: '',
        curComponent: {
          id: '',
          name: '',
          label: '',
          content: '',
          innerHtml: '',
          markdownHtml: ''
        },
        curComponentList: [],
        sdkNavList: [],
        sdks: [],
        curSdk: {},
        sdkMarkdownHtml: '',
        curApigw: {
          name: '',
          label: '',
          maintainers: []
        },
                
        componentNavList: [],
        resourceListT: [1, 2, 3]
      }
    },
    computed: {
      curUser () {
        return this.$store.state.user
      },
      userList () {
        // 去重
        const set = new Set([this.curUser.username, ...this.curApigw.maintainers])
        return [...set]
      },
      chatName () {
        return `${this.$t('[蓝鲸网关API咨询] 网关')}${this.curApigw.name}`
      },
      chatContent () {
        return `${this.$t('网关API文档')}:${location.href}`
      },
      resourceList () {
        return this.$store.state.apigw.resourceList
      },
      SDKInfo () {
        return this.$t(`网关当前环境【{curStageText}】对应的资源版本未生成SDK，可联系网关负责人生成SDK`, { curStageText: this.curStage })
      }
    },
    watch: {
      '$route' () {
        this.init()
      },
      'resourceList' () {
        const match = this.resourceList.find(item => {
          return item.name === this.curResourceId
        })
        if (match) {
          this.curComponent = { ...this.curComponent, ...match }
        }
      }
    },
    created () {
      // ':stage/:resourceId/doc',
      this.init()
    },
    methods: {
      init () {
        const routeParams = this.$route.params
        this.curApigwId = routeParams.apigwId
        this.curStage = this.$route.query.stage
        this.curResourceId = routeParams.resourceId
                
        Promise.all([
          this.getApigwAPIDetail(),
          // this.getApigwResourceDetail(),
          this.getApigwResourceDoc(),
          this.getApigwSDK('python')
        ]).finally(() => {
          this.$store.commit('setMainContentLoading', false)
        })
      },

      async getApigwAPIDetail () {
        try {
          const res = await this.$store.dispatch('apigw/getApigwAPIDetail', {
            apigwId: this.curApigwId
          })
          this.curApigw = res.data
        } catch (e) {
          catchErrorHandler(e, this)
        }
      },

      async getApigwSDK (language) {
        try {
          const res = await this.$store.dispatch('apigw/getApigwSDK', {
            apigwId: this.curApigwId,
            language: language
          })
          this.sdks = res.data
          const match = this.sdks.find(item => item.stage_name === this.curStage)
          this.curSdk = match || {}
          this.getApigwResourceSDK()
        } catch (e) {
          catchErrorHandler(e, this)
        }
      },

      async getApigwResourceDetail () {
        try {
          const res = await this.$store.dispatch('apigw/getApigwResources', {
            apigwId: this.curApigwId,
            stage: this.curStage
          })

          const match = res.data.results.find(item => {
            return item.name === this.curResourceId
          })
          if (match) {
            this.curComponent = { ...this.curComponent, ...match }
          }
        } catch (e) {
          catchErrorHandler(e, this)
        }
      },

      async getApigwResourceDoc (id) {
        this.$store.commit('setMainContentLoading', true)
        try {
          const res = await this.$store.dispatch('apigw/getApigwResourceDoc', {
            apigwId: this.curApigwId,
            stage: this.curStage,
            resourceId: this.curResourceId
          })
          const content = res.data.content
          this.curComponent.content = content
          this.curComponent.markdownHtml = md.render(content)
          this.renderHtmlIndex++
          this.curDocUpdated = res.data.updated_time

          this.initMarkdownHtml('markdown')
        } catch (e) {
          catchErrorHandler(e, this)
        } finally {
          this.$store.commit('setMainContentLoading', false)
        }
      },

      async getApigwResourceSDK () {
        try {
          const res = await this.$store.dispatch('apigw/getApigwResourceSDK', {
            apigwId: this.curApigwId,
            stage: this.curStage,
            resourceId: this.curResourceId,
            sdk: this.curSdk.sdk_name
          })
          const content = res.data.content
          this.sdkMarkdownHtml = md.render(content)
          this.initMarkdownHtml('sdk-markdown')
        } catch (e) {
          catchErrorHandler(e, this)
        }
      },

      initMarkdownHtml (box) {
        this.$nextTick(() => {
          const markdownDom = document.getElementById(box)
          // 右侧导航
          const titles = markdownDom && markdownDom.querySelectorAll('h3')
          if (box === 'sdk-markdown') {
            this.sdkNavList = []
            titles && titles.forEach(item => {
              const name = String(item.firstChild.nodeValue).trim()
              const id = slugify(name)
              item.id = `${this.curComponentName}?${id}`
              this.sdkNavList.push({
                id: `${this.curComponentName}?${id}`,
                name: name
              })
            })
          } else {
            this.componentNavList = []
            titles && titles.forEach(item => {
              const name = String(item.innerText).trim()
              const id = slugify(name)
              item.id = `${this.curComponentName}?${id}`
              this.componentNavList.push({
                id: `${this.curComponentName}?${id}`,
                name: name
              })
            })
          }

          // 复制代码
          markdownDom && markdownDom.querySelectorAll('a').forEach(item => {
            item.target = '_blank'
          })
          markdownDom && markdownDom.querySelectorAll('pre').forEach(item => {
            const parentDiv = document.createElement('div')
            const btn = document.createElement('button')
            const codeBox = document.createElement('div')
            const code = item.querySelector('code').innerText
            parentDiv.className = 'pre-wrapper'
            btn.className = 'ag-copy-btn'
            codeBox.className = 'code-box'
            btn.innerHTML = '<span :title="$t(`复制`)"><i class="bk-icon icon-clipboard mr5"></i></span>'
            btn.setAttribute('data-clipboard-text', code)
            parentDiv.appendChild(btn)
            codeBox.appendChild(item.querySelector('code'))
            item.appendChild(codeBox)
            item.parentNode.replaceChild(parentDiv, item)
            parentDiv.appendChild(item)
          })
        })

        if (this.clipboardInstance && this.clipboardInstance.off) {
          this.clipboardInstance.off('success')
        }
        setTimeout(() => {
          this.clipboardInstance = new Clipboard('.ag-copy-btn')
          this.clipboardInstance.on('success', e => {
            this.$bkMessage({
              width: 100,
              limit: 1,
              theme: 'success',
              message: this.$t('复制成功')
            })
          })
        }, 2000)
      }
    }
  }
</script>

<style lang="postcss" scoped>
    @import './detail.css';
</style>
