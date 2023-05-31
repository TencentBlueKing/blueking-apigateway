<template>
  <div class="intro-doc">
    <div class="component-content">
      <div class="component-metedata mb10">
        <strong class="name"> {{ $t('简介') }} </strong>
      </div>

      <div style="position: relative;">
        <bk-breadcrumb separator-class="bk-icon icon-angle-right" class="0">
          <bk-breadcrumb-item :to="{ name: 'apigwDoc' }"> {{ $t('网关API文档') }} </bk-breadcrumb-item>
          <bk-breadcrumb-item>{{curApigw.name || '--'}}</bk-breadcrumb-item>
          <bk-breadcrumb-item> {{ $t('简介') }} </bk-breadcrumb-item>
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
            
      <bk-divider></bk-divider>

      <div class="ag-markdown-view" id="markdown">
        <h3> {{ $t('网关描述') }} </h3>
        <p class="mb30">{{curApigw.description}}</p>

        <h3> {{ $t('网关负责人') }} </h3>
        <p class="mb30">{{curApigw.maintainers.join(', ')}}</p>

        <h3> {{ $t('网关访问地址') }} </h3>
        <p class="mb30">{{curApigw.api_url}}</p>

        <template v-if="GLOBAL_CONFIG.PLATFORM_FEATURE.ENABLE_SDK">
          <h3> {{ $t('网关 SDK') }} </h3>
          <div class="bk-button-group">
            <bk-button class="is-selected">Python</bk-button>
            <!-- <bk-button disabled>GO</bk-button> -->
          </div>
        </template>
      </div>

      <template v-if="GLOBAL_CONFIG.PLATFORM_FEATURE.ENABLE_SDK">
        <bk-table style="margin-top: 15px;"
          :data="sdks"
          :size="'small'">
          <div slot="empty">
            <table-empty
              :abnormal="isAbnormal"
              @reacquire="getApigwSDK('python')"
            />
          </div>

          <bk-table-column :label="$t('网关环境')" prop="name" show-overflow-tooltip :render-header="columnRenderHeader">
            <template slot-scope="props">
              {{props.row.stage_name}}
            </template>
          </bk-table-column>

          <bk-table-column :label="$t('网关API资源版本')" prop="name" width="250" show-overflow-tooltip :render-header="columnRenderHeader">
            <template slot-scope="props">
              {{props.row.resource_version_display || '--'}}
            </template>
          </bk-table-column>

          <bk-table-column :label="$t('SDK 版本号')" prop="name" show-overflow-tooltip :render-header="renderHeader">
            <template slot-scope="props">
              {{props.row.sdk_version_number || '--'}}
            </template>
          </bk-table-column>

          <bk-table-column :label="$t('SDK下载')" :render-header="columnRenderHeader">
            <template slot-scope="props">
              <template v-if="props.row.sdk_download_url">
                <bk-button class="mr5" :text="true" @click="handleShow(props.row)"> {{ $t('查看') }} </bk-button>
                <bk-button :text="true" @click="handleDownload(props.row)"> {{ $t('下载') }} </bk-button>
              </template>
              <template v-else>
                {{ $t('未生成-doc') }}
              </template>
            </template>
          </bk-table-column>
        </bk-table>

        <p class="ag-tip mt5">
          <i class="bk-icon icon-info"></i>
          {{ $t('若资源版本对应的SDK未生成，可联系网关负责人生成SDK') }}
        </p>
      </template>

      <zan class="mt30 mb50" v-if="GLOBAL_CONFIG.PLATFORM_FEATURE.ENABLE_FEEDBACK"></zan>

      <bk-sideslider
        :width="720"
        :title="sdkConfig.title"
        :is-show.sync="sdkConfig.isShow"
        :quick-close="true">
        <div slot="content" class="p25">
          <sdk-detail :params="curSdk"></sdk-detail>
        </div>
      </bk-sideslider>
    </div>

    <div class="component-nav-box" v-if="componentNavList.length">
      <div style="position: fixed;">
        <side-nav :list="componentNavList"></side-nav>
      </div>
    </div>
  </div>
</template>

<script>
  import { catchErrorHandler, renderHeader } from '@/common/util'
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
        sdks: [],
        sdkConfig: {
          title: '',
          isShow: false
        },
        curSdk: {},
        componentNavList: [],
        curApigw: {
          'id': 2,
          'name': '',
          'description': '',
          'maintainers': [
          ],
          'name_prefix': '',
          'api_url': ''
        },
        isAbnormal: false,
        columnRenderHeader: renderHeader
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
      }
    },
    watch: {
      '$route' () {
        this.init()
      }
    },
    created () {
      this.init()
    },
    methods: {
      async init () {
        const container = document.querySelector('.container-content')
        container.scrollTo({
          top: 0,
          behavior: 'smooth'
        })
                
        const routeParams = this.$route.params
        this.curApigwId = routeParams.apigwId
        this.getApigwAPIDetail()
        this.getApigwSDK('python')
      },

      async getApigwAPIDetail () {
        this.$store.commit('setMainContentLoading', true)
        try {
          const res = await this.$store.dispatch('apigw/getApigwAPIDetail', {
            apigwId: this.curApigwId
          })
          this.curApigw = res.data
          this.initMarkdownHtml()
        } catch (e) {
          catchErrorHandler(e, this)
        } finally {
          this.$store.commit('setMainContentLoading', false)
        }
      },

      async getApigwSDK (language) {
        try {
          const res = await this.$store.dispatch('apigw/getApigwSDK', {
            apigwId: this.curApigwId,
            language: language
          })
          this.sdks = res.data
          this.isAbnormal = false
        } catch (e) {
          this.isAbnormal = true
          catchErrorHandler(e, this)
        }
      },

      renderHeader (h, data) {
        const directive = {
          name: 'bkTooltips',
          content: this.$t('网关API资源版本对应的SDK'),
          placement: 'right'
        }
        return <span style="cursor: pointer;" class="custom-header-cell" v-bk-tooltips={ directive }>
                    { data.column.label }
                    <i class="bk-icon icon-question-circle-shape ml5"></i>
                </span>
      },

      handleShow (data) {
        this.curSdk = data
        this.sdkConfig.title = `${this.$t('网关API SDK')}：${this.curApigwId}`
        this.sdkConfig.isShow = true

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

      handleDownload (sdk) {
        window.open(sdk.sdk_download_url)
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
            btn.innerHTML = '<span :title="$t(`复制`)"><i class="bk-icon icon-clipboard mr5"></i></span>'
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
      }
    }
  }
</script>

<style lang="postcss" scoped>
    @import './detail.css';
</style>
