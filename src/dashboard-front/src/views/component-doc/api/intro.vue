<template>
  <div class="intro-doc">
    <div class="component-content">
      <div class="component-metedata mb10">
        <strong class="name">{{ $t('简介') }}</strong>
      </div>

      <div style="position: relative;">
        <bk-breadcrumb separator-class="bk-icon icon-angle-right" class="mb20">
          <bk-breadcrumb-item :to="{ name: 'componentAPI' }">{{ $t('组件API文档') }}</bk-breadcrumb-item>
          <bk-breadcrumb-item>{{curSystem.description || '--'}}</bk-breadcrumb-item>
          <bk-breadcrumb-item>{{ $t('简介') }}</bk-breadcrumb-item>
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

      <bk-divider></bk-divider>

      <div class="ag-markdown-view" id="markdown">
        <h3>{{ $t('系统描述') }}</h3>
        <p class="mb30">{{curSystem.comment || $t('暂无简介')}}</p>

        <h3>{{ $t('系统负责人-doc') }}</h3>
        <p class="mb30">{{curSystem.maintainers && curSystem.maintainers.join(', ') || '--'}}</p>

        <template v-if="GLOBAL_CONFIG.PLATFORM_FEATURE.ENABLE_SDK">
          <h3>{{ $t('组件API SDK') }}</h3>
          <div class="bk-button-group">
            <bk-button class="is-selected">Python</bk-button>
          </div>

          <div>
            <sdk-detail :params="curSdk"></sdk-detail>
          </div>
        </template>

        <zan class="mt30 mb50" v-if="GLOBAL_CONFIG.PLATFORM_FEATURE.ENABLE_FEEDBACK"></zan>
      </div>
    </div>

    <div class="component-nav-box" v-if="componentNavList.length">
      <div style="position: fixed;">
        <side-nav :list="componentNavList"></side-nav>
      </div>
    </div>
  </div>
</template>

<script>
  import { catchErrorHandler } from '@/common/util'
  import Clipboard from 'clipboard'
  import { slugify } from 'transliteration'
  import Chat from '@/components/chat'
  import sdkDetail from '@/components/sdk-detail'
  import zan from '@/components/zan'

  export default {
    components: {
      Chat,
      sdkDetail,
      zan
    },
    data () {
      return {
        curVersion: '',
        curCatefory: '',
        curSystemName: '',
        curComponentName: '',
        renderHtmlIndex: 0,
        curSdk: {},
        curComponent: {
          id: '',
          name: '',
          label: '',
          content: '',
          innerHtml: '',
          markdownHtml: ''
        },
        curComponentList: [],
        curSystem: {
          name: '',
          description: ''
        },
                
        componentNavList: []
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
      this.curCatefory = routeParams.category
      this.curSystemName = routeParams.id
      this.init()
    },
    methods: {
      init () {
        this.getSystemDetail()
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

      initMarkdownHtml (content) {
        this.$nextTick(() => {
          const markdownDom = document.getElementById('markdown')
          // 右侧导航
          const titles = markdownDom.querySelectorAll('h3')
          this.componentNavList = []
          titles.forEach(item => {
            const name = String(item.innerText).trim()
            const newName = slugify(name)
            const id = `${this.curComponentName}?${newName}`
            this.componentNavList.push({
              id: id,
              name: name
            })
            item.id = id
          })

          // 复制代码
          markdownDom.querySelectorAll('a').forEach(item => {
            item.target = '_blank'
          })
          markdownDom.querySelectorAll('pre').forEach(item => {
            const btn = document.createElement('button')
            const codeBox = document.createElement('div')
            const code = item.querySelector('code').innerText
            btn.className = 'ag-copy-btn'
            codeBox.className = 'code-box'
            btn.innerHTML = '<span title="复制"><i class="bk-icon icon-clipboard mr5"></i></span>'
            btn.setAttribute('data-clipboard-text', code)
            item.appendChild(btn)
            codeBox.appendChild(item.querySelector('code'))
            item.appendChild(codeBox)
          })
        })

        if (this.clipboardInstance && this.clipboardInstance.off) {
          this.clipboardInstance.off('success')
        }
        setTimeout(() => {
          this.clipboardInstance = new Clipboard('.doc-copy')
          this.clipboardInstance.on('success', e => {
            this.$bkMessage({
              width: 100,
              limit: 1,
              theme: 'success',
              message: this.$t('复制成功')
            })
          })
        }, 1000)
      },

      handleDownload () {
        if (this.curSdk.sdk_download_url) {
          window.open(this.curSdk.sdk_download_url)
        }
      }
    }
  }
</script>

<style lang="postcss" scoped>
    @import './detail.css';
</style>
