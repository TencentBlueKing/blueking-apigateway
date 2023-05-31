<template>
  <loader :is-loading="mainContentLoading" class="skd-wrapper" :loader="'table2-loader'" :height="400">
    <bk-tab :active.sync="active" :key="renderKey">
      <bk-tab-panel
        :name="'sdk'"
        :label="$t('SDK 列表')">
        <div class="bk-button-group">
          <bk-button class="is-selected">Python</bk-button>
          <!-- <bk-button disabled>GO</bk-button> -->
        </div>

        <bk-input
          v-if="type === 'apigateway'"
          class="fr"
          v-model="keyword"
          style="width: 500px;"
          :placeholder="$t('请输入网关名称或描述')"
          :right-icon="'bk-icon icon-search'"
          :clearable="true">
        </bk-input>

        <bk-table
          ref="sdkRef"
          style="margin-top: 15px;"
          :data="curPageData"
          :size="'small'"
          :key="renderKey"
          :outer-border="false"
          :pagination="pagination"
          @filter-change="handleFilterChange"
          @page-limit-change="handlePageLimitChange"
          @page-change="handlePageChange">
          <div slot="empty">
            <table-empty
              :keyword="tableEmptyConf.keyword"
              :abnormal="tableEmptyConf.isAbnormal"
              @reacquire="getSDKList"
              @clear-filter="clearFilterKey"
            />
          </div>

          <template v-if="type === 'apigateway'">
            <bk-table-column :label="$t('网关名称')" show-overflow-tooltip>
              <template slot-scope="props">
                {{props.row.api_name}}
              </template>
            </bk-table-column>

            <bk-table-column :label="$t('网关描述')" :show-overflow-tooltip="true" :render-header="columnRenderHeader">
              <template slot-scope="props">
                {{props.row.api_description || '--'}}
              </template>
            </bk-table-column>

            <!-- <bk-table-column
                            :label="$t('用户类型')"
                            width="150"
                            prop="user_auth_type"
                            column-key="user_auth_type"
                            v-if="userFilters.length"
                            :filters="userFilters"
                            :filter-multiple="true"
                            :render-header="columnRenderHeader"
                            show-overflow-tooltip>
                            <template slot-scope="props">
                                {{props.row.user_auth_type_display || '--'}}
                            </template>
                        </bk-table-column>

                        <bk-table-column
                            :label="$t('用户类型')"
                            width="150"
                            prop="user_auth_type"
                            column-key="user_auth_type"
                            :render-header="columnRenderHeader"
                            show-overflow-tooltip
                            v-else>
                            <template slot-scope="props">
                                {{props.row.user_auth_type_display || '--'}}
                            </template>
                        </bk-table-column> -->
          </template>

          <template v-else>
            <bk-table-column :label="$t('名称')" show-overflow-tooltip>
              <template slot-scope="props">
                {{props.row.board_label || '--'}}
              </template>
            </bk-table-column>

            <bk-table-column :label="$t('描述')" :show-overflow-tooltip="true">
              <template slot-scope="props">
                {{props.row.sdk_description || '--'}}
              </template>
            </bk-table-column>
          </template>

          <bk-table-column :label="$t('SDK包名称')" :show-overflow-tooltip="true" :render-header="columnRenderHeader">
            <template slot-scope="props">
              {{props.row.sdk_name || '--'}}
            </template>
          </bk-table-column>

          <bk-table-column :label="$t('SDK最新版本')" :render-header="renderHeader" show-overflow-tooltip>
            <template slot-scope="props">
              {{props.row.sdk_version_number || '--'}}
            </template>
          </bk-table-column>

          <bk-table-column :label="$t('操作')" width="200">
            <template slot-scope="props">
              <template v-if="props.row.sdk_download_url">
                <bk-button class="mr5" :text="true" @click="handleShow(props.row)"> {{ $t('查看') }} </bk-button>
                <a class="ag-link" :href="props.row.sdk_download_url"> {{ $t('下载') }} </a>
              </template>
              <template v-else>
                {{ $t('未生成-doc') }}
              </template>
            </template>
          </bk-table-column>
        </bk-table>
      </bk-tab-panel>
      <bk-tab-panel
        :name="'doc'"
        :label="$t('SDK 说明')">
        <div class="bk-button-group mb10">
          <bk-button class="is-selected">Python</bk-button>
          <!-- <bk-button disabled>GO</bk-button> -->
        </div>
        <div class="ag-markdown-view" id="markdown" :key="renderHtmlIndex" v-html="markdownHtml"></div>
        <zan class="mt30 mb50" v-if="GLOBAL_CONFIG.PLATFORM_FEATURE.ENABLE_FEEDBACK"></zan>
      </bk-tab-panel>
    </bk-tab>

    <bk-sideslider
      :width="750"
      :title="sdkConfig.title"
      :is-show.sync="sdkConfig.isShow"
      :quick-close="true">
      <div slot="content" class="p25">
        <div class="bk-button-group mb15">
          <bk-button class="is-selected">Python</bk-button>
          <!-- <bk-button disabled>GO</bk-button> -->
        </div>
        <sdk-detail :params="curSdk" :is-apigw="type === 'apigateway'"></sdk-detail>
      </div>
    </bk-sideslider>
  </loader>
</template>

<script>
  import { catchErrorHandler, clearFilter, renderHeader } from '@/common/util'
  import MarkdownIt from 'markdown-it'
  import Clipboard from 'clipboard'
  import loader from '@/components/loader'
  import sdkDetail from '@/components/sdk-detail'
  import zan from '@/components/zan'

  export default {
    components: {
      loader,
      sdkDetail,
      zan
    },
    data () {
      return {
        type: '',
        pagination: {
          current: 1,
          count: 0,
          limit: 20
        },
        filterList: [],
        keyword: '',
        originSdkList: [],
        language: 'python',
        active: 'sdk',
        renderHtmlIndex: 0,
        renderKey: 0,
        sdkConfig: {
          title: '',
          isShow: false
        },
        sdkDoc: '',
        markdownHtml: '',
        curSdk: {
          sdk_name: '',
          sdk_version_number: '',
          sdk_download_url: '',
          sdk_install_command: ''
        },
        tableEmptyConf: {
          isAbnormal: false,
          keyword: ''
        },
        columnRenderHeader: renderHeader
      }
    },

    computed: {
      mainContentLoading () {
        return this.$store.state.mainContentLoading
      },

      userFilters () {
        const list = []
        const map = {}
        this.originSdkList.forEach(item => {
          if (!map[item.user_auth_type]) {
            list.push({
              text: item.user_auth_type_display,
              value: item.user_auth_type
            })
          }
          map[item.user_auth_type] = true
        })
        this.renderKey++
        return list
      },

      curPageData () {
        const page = this.pagination.current
        let startIndex = (page - 1) * this.pagination.limit
        let endIndex = page * this.pagination.limit
        if (startIndex < 0) {
          startIndex = 0
        }
        if (endIndex > this.sdkList.length) {
          endIndex = this.sdkList.length
        }
        this.updateTableEmptyConfig()
        return this.sdkList.slice(startIndex, endIndex)
      },

      sdkList () {
        return this.originSdkList.filter(item => {
          if (this.type === 'apigateway') {
            const name = item.api_name
            const description = item.api_description
            const matchKeyword = (name || '').indexOf(this.keyword) > -1 || (description || '').indexOf(this.keyword) > -1
            const matchFilter = this.filterList.length ? this.filterList.includes(item['user_auth_type']) : true
            return matchKeyword && matchFilter
          }
          return true
        })
      }
    },

    watch: {
      '$route' () {
        this.init()
      },

      sdkList () {
        this.resetPagination()
      }
    },

    created () {
      this.init()
    },

    methods: {
      init () {
        this.active = this.$route.query.tab ? this.$route.query.tab : 'sdk'
        this.type = this.$route.meta.type
        this.$store.commit('setMainContentLoading', true)
        this.renderKey++
        this.getSDKList()
        this.getSDKDoc()
      },

      handleShow (data) {
        this.curSdk = data
        this.sdkConfig.title = this.type === 'apigateway' ? `${this.$t('网关API SDK')}: ${data.api_name}` : `${this.$t('组件API SDK')}: ${data.board_label}`
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

      async getSDKList () {
        try {
          const res = await this.$store.dispatch('sdkDoc/getSDKList', { type: this.type, language: this.language })
          const results = res.data
          this.originSdkList = results
          this.pagination.count = results.length
          this.tableEmptyConf.isAbnormal = false
        } catch (e) {
          this.tableEmptyConf.isAbnormal = true
          catchErrorHandler(e, this)
        } finally {
          setTimeout(() => {
            this.$store.commit('setMainContentLoading', false)
          }, 1000)
        }
      },

      async getSDKDoc () {
        try {
          const res = await this.$store.dispatch('sdkDoc/getSDKDoc', { type: this.type, language: this.language })
          this.sdkDoc = res.data.content
          this.initMarkdownHtml(this.sdkDoc)
        } catch (e) {
          catchErrorHandler(e, this)
        }
      },

      handleFilterChange (filters) {
        this.filterList = filters['user_auth_type']
      },

      initMarkdownHtml (content) {
        const md = new MarkdownIt({
          linkify: false
        })
        this.markdownHtml = md.render(content)

        this.renderHtmlIndex++
                
        this.$nextTick(() => {
          const markdownDom = document.getElementById('markdown')

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
          this.clipboardInstance = new Clipboard('.ag-copy-btn')
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
      },

      resetPagination () {
        this.pagination.count = this.sdkList.length
        this.pagination.current = 1
      },

      handlePageLimitChange (limit) {
        this.pagination.limit = limit
        this.pagination.current = 1
      },

      handlePageChange (newPage) {
        this.pagination.current = newPage
      },

      renderHeader (h, data) {
        if (this.type === 'apigateway') {
          const directive = {
            name: 'bkTooltips',
            content: this.$t('网关最新SDK，对应已生成SDK的最新资源版本'),
            placement: 'right'
          }
          return <span style="cursor: pointer;" class="custom-header-cell" v-bk-tooltips={ directive }>
                        { data.column.label }
                        <i class="bk-icon icon-question-circle-shape ml5"></i>
                    </span>
        } else {
          return <span>
                        { data.column.label }
                    </span>
        }
      },

      updateTableEmptyConfig () {
        if (this.keyword || this.filterList.length) {
          this.tableEmptyConf.keyword = 'placeholder'
          return
        }
        this.tableEmptyConf.keyword = ''
      },

      clearFilterKey () {
        this.keyword = ''
        this.$refs.sdkRef.clearFilter()
        if (this.$refs.sdkRef && this.$refs.sdkRef.$refs.tableHeader) {
          clearFilter(this.$refs.sdkRef.$refs.tableHeader)
        }
      }
    }
  }
</script>

<style lang="postcss" scoped>
    @import './index.css';
</style>
