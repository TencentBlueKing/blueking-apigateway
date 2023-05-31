<template>
  <div class="component-doc">
    <div class="component-content">
      <div class="component-metedata mb10">
        <strong class="name mr5" v-bk-tooltips.top="curComponent.name">{{curComponent.name}}</strong>
        <span class="label" v-bk-tooltips.top-start="{ content: curComponent.description, allowHTML: false }">{{curComponent.description || $t('暂无描述')}}</span>
      </div>

      <div style="position: relative;">
        <bk-breadcrumb separator-class="bk-icon icon-angle-right" class="mb20">
          <bk-breadcrumb-item :to="{ name: 'componentAPI' }">{{ $t('组件API文档') }}</bk-breadcrumb-item>
          <bk-breadcrumb-item>{{curSystem.description || '--'}}</bk-breadcrumb-item>
          <bk-breadcrumb-item>{{curComponent.name || '--'}}</bk-breadcrumb-item>
        </bk-breadcrumb>
        <chat
          class="ag-chat"
          v-if="GLOBAL_CONFIG.PLATFORM_FEATURE.ALLOW_CREATE_APPCHAT"
          :default-user-list="userList"
          :owner="curUser.username"
          :name="chatName"
          :content="chatContent">
        </chat>
      </div>
      <bk-tab :active.sync="active" class="bk-special-tab" @tab-change="handleTabChange">
        <bk-tab-panel
          :name="'doc'"
          :label="$t('文档')">
          <div class="ag-kv-box mb30">
            <div class="kv-row">
              <div class="k">{{ $t('更新时间') }}:</div>
              <div class="v">{{curDocUpdated || '--'}}</div>
            </div>
            <div class="kv-row">
              <div class="k">{{ $t('应用认证') }}<i class="ml5 bk-icon icon-question-circle" v-bk-tooltips="$t('应用访问该组件API时，是否需提供应用认证信息')"></i>：</div>
              <div class="v">{{curComponent.app_verified_required ? $t('是') : $t('否')}}</div>
            </div>
            <div class="kv-row">
              <div class="k">{{ $t('用户认证') }}<i class="ml5 bk-icon icon-question-circle" v-bk-tooltips="$t('应用访问该组件API时，是否需要提供用户认证信息')"></i>：</div>
              <div class="v">{{curComponent.user_verified_required ? $t('是') : $t('否')}}</div>
            </div>
            <div class="kv-row">
              <div class="k">{{ $t('是否需申请权限') }}<i class="ml5 bk-icon icon-question-circle" v-bk-tooltips="$t('应用访问该组件API前，是否需要在开发者中心申请该组件API权限')"></i>：</div>
              <div class="v">{{curComponent.component_permission_required ? $t('是') : $t('否')}}</div>
            </div>
          </div>
          <div class="ag-markdown-view" id="markdown" :key="renderHtmlIndex" v-html="curComponent.markdownHtml"></div>
          <zan class="mt30 mb50" v-if="GLOBAL_CONFIG.PLATFORM_FEATURE.ENABLE_FEEDBACK"></zan>
        </bk-tab-panel>
        <bk-tab-panel
          :name="'sdk '"
          :label="$t('SDK及示例')"
          v-if="GLOBAL_CONFIG.PLATFORM_FEATURE.ENABLE_SDK">
          <div id="sdk-markdown">
            <div class="bk-button-group mb5">
              <bk-button class="is-selected">Python</bk-button>
              <!-- <bk-button disabled>GO</bk-button> -->
            </div>
            <h3 class="f16">
              {{ $t('SDK信息-doc') }}
            </h3>
            <router-link style="margin-top: -30px;" :to="{ name: 'esbSDK', query: { tab: 'doc' } }" class="ag-link fn f12 fr">{{ $t('Python SDK使用说明') }}</router-link>

            <div>
              <sdk-detail :params="curSdk"></sdk-detail>
            </div>
            <h3 class="f16 mt30">{{ $t('SDK使用样例') }}</h3>
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
  import Chat from '@/components/chat'
  import sdkDetail from '@/components/sdk-detail'
  import hljs from 'highlight.js'
  import 'highlight.js/styles/monokai-sublime.css'
  import zan from '@/components/zan'

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
      Chat,
      sdkDetail,
      zan
    },
    data () {
      return {
        curDocUpdated: '',
        curSdk: {},
        active: 'doc',
        curVersion: '',
        curSystemName: '',
        curComponentName: '',
        renderHtmlIndex: 0,
        curSideNavId: '',
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
        curSystem: {
          name: '',
          description: ''
        },

        componentNavList: [],
        sdkMarkdownHtml: ''
      }
    },
    computed: {
      curUser () {
        return this.$store.state.user
      },
      userList () {
        // 去重
        const list = (this.curSystem.maintainers || []).filter(item => item !== 'BK助手')
        const set = new Set(list)
        return [...set]
      },
      chatName () {
        return `${this.$t('[蓝鲸组件API咨询] 系统')} ${this.curSystem.description || this.curSystem.name}`
      },
      chatContent () {
        return `${this.$t('组件API文档：')}${location.href}`
      }
    },
    created () {
      const routeParams = this.$route.params
      this.curVersion = routeParams.version
      this.curSystemName = routeParams.id
      this.curComponentName = routeParams.componentId
      this.init()
    },
    methods: {
      init () {
        this.getSystemDetail()
        this.getSystemComponents()
        this.getSystemComponentDoc()
        this.getSDKDoc()
        this.getSDKDetail()
      },

      async getSystemDetail () {
        try {
          const res = await this.$store.dispatch('esb/getSystemDetail', {
            version: this.curVersion,
            systemName: this.curSystemName
          })
          this.curSystem = res.data
        } catch (e) {
          catchErrorHandler(e, this)
        }
      },

      async getSystemComponents () {
        try {
          const res = await this.$store.dispatch('esb/getSystemComponents', {
            version: this.curVersion,
            systemName: this.curSystemName
          })
          this.curComponentList = res.data
          const match = this.curComponentList.find(item => item.name === this.curComponentName)
          if (match) {
            this.curComponent = { ...this.curComponent, ...match }
          }
        } catch (e) {
          catchErrorHandler(e, this)
        }
      },

      handleShowDoc (component) {
        this.curComponent = component
        this.curComponentName = this.curComponent.name
        this.getSystemComponentDoc()
      },

      async getSystemComponentDoc (id) {
        this.$store.commit('setMainContentLoading', true)
        try {
          const res = await this.$store.dispatch('esb/getSystemComponentDoc', {
            version: this.curVersion,
            systemName: this.curSystemName,
            componentId: this.curComponentName
          })
          const data = res.data ? res.data : { content: '', type: 'markdown' }
          const content = data.content
          this.curComponent.content = content
          this.curComponent.markdownHtml = data.type === 'markdown' ? md.render(content) : content
          this.curDocUpdated = res.data.updated_time
          this.renderHtmlIndex++
          this.initMarkdownHtml('markdown')
        } catch (e) {
          catchErrorHandler(e, this)
        } finally {
          this.$store.commit('setMainContentLoading', false)
        }
      },

      handleAnchor (id) {
        const OFFSET = 60
        const element = document.getElementById(id)
        this.curSideNavId = id

        if (element) {
          const rect = element.getBoundingClientRect()
          const container = document.querySelector('.container-content')
          const top = container.scrollTop + rect.top - OFFSET

          container.scrollTo({
            top: top,
            behavior: 'smooth'
          })
        }
      },

      async getSDKDoc (language) {
        try {
          const res = await this.$store.dispatch('esb/getSDKDoc', {
            version: this.curVersion,
            systemName: this.curSystemName,
            componentId: this.curComponentName,
            language: 'python'
          })
          const content = res.data ? res.data.content : ''
          this.sdkMarkdownHtml = md.render(content)
        } catch (e) {
          catchErrorHandler(e, this)
        }
      },

      async getSDKDetail () {
        try {
          const res = await this.$store.dispatch('esb/getSDKDetail', {
            version: this.curVersion,
            language: 'python'
          })
          this.curSdk = res.data
          this.initMarkdownHtml()
        } catch (e) {
          catchErrorHandler(e, this)
        }
      },

      handleTabChange () {
        if (this.active === 'doc') {
          this.initMarkdownHtml('markdown')
        } else {
          this.initMarkdownHtml('sdk-markdown')
        }
      },

      initMarkdownHtml (box) {
        if (!box) {
          return false
        }
        this.$nextTick(() => {
          const markdownDom = document.getElementById(box)
          if (markdownDom.className.indexOf('has-init') > -1) {
            return false
          }
          markdownDom.className = `${markdownDom.className} has-init`
          // 右侧导航
          const titles = markdownDom.querySelectorAll('h3')

          if (box === 'sdk-markdown') {
            this.sdkNavList = []
            titles.forEach(item => {
              const name = String(item.innerText).trim()
              const id = slugify(name)
              item.id = `${this.curComponentName}?${id}`
              this.sdkNavList.push({
                id: `${this.curComponentName}?${id}`,
                name: name
              })
            })
          } else {
            this.componentNavList = []
            titles.forEach(item => {
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
          markdownDom.querySelectorAll('a').forEach(item => {
            // item.target = '_blank'
          })
          markdownDom.querySelectorAll('pre').forEach(item => {
            const btn = document.createElement('button')
            let code = ''
            if (item.className.indexOf('code') > -1) {
              code = item.innerText
            } else {
              code = item.querySelector('code').innerText
            }

            btn.className = 'ag-copy-btn'
            btn.innerHTML = '<span title="复制"><i class="bk-icon icon-clipboard mr5"></i></span>'
            btn.setAttribute('data-clipboard-text', code)
            item.appendChild(btn)
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
      },

      initHtml (content, type = 'markdown') {
        this.$nextTick(() => {
          const markdownDom = document.getElementById('markdown')
          // 右侧导航
          const titles = markdownDom.querySelectorAll('h3')
          this.componentNavList = []
          titles.forEach(item => {
            const name = String(item.innerText).trim()
            const newName = slugify(name)
            const id = `${this.curComponentName}_${newName}`
            this.componentNavList.push({
              id: id,
              name: name
            })
            item.id = id
          })

          // 复制代码
          markdownDom.querySelectorAll('a').forEach(item => {
            // item.target = '_blank'
          })

          markdownDom.querySelectorAll('pre').forEach(item => {
            const btn = document.createElement('button')
            let code = ''
            if (item.className.indexOf('code') > -1) {
              code = item.innerText
            } else {
              code = item.querySelector('code').innerText
            }

            btn.className = 'ag-copy-btn'
            btn.innerHTML = '<span title="复制"><i class="bk-icon icon-clipboard mr5"></i></span>'
            btn.setAttribute('data-clipboard-text', code)
            item.appendChild(btn)
          })

          // table
          const tables = document.querySelectorAll('table')
          tables.forEach(table => {
            table.className = 'bk-table'
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
