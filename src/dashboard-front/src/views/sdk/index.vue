<template>
  <div class="app-content">
    <div class="basic-info">
      <div class="basic-hd">
        <div class="title fl">{{ $t('SDK信息') }}</div>
        <bk-button class="fr" theme="primary" @click="handleBuildSDK"> {{ $t('生成SDK') }} </bk-button>

        <bk-form class="fr mr15" form-type="inline">
          <bk-form-item label="">
            <bk-search-select
              style="min-width: 500px;"
              v-model="searchFilters"
              :data="searchData"
              :placeholder="$t('输入SDK版本号、资源版本进行搜索')"
              :show-popover-tag-change="true"
              :show-condition="false"
              clearable
              @change="formatFilterData"
              @clear="clearSearchFilters"></bk-search-select>
          </bk-form-item>
          <!-- <bk-form-item :label="$t('SDK版本号')">
            <bk-input
              :clearable="true"
              v-model="sdkVersionKeyword"
              :placeholder="$t('请输入SDK版本号，按Enter搜索')"
              :right-icon="'bk-icon icon-search'"
              style="width: 250px;"
              @enter="handleSearch"
              @clear="handleSearch">
            </bk-input>
          </bk-form-item>
          <bk-form-item :label="$t('资源版本')">
            <bk-select
              searchable
              clearable
              style="width: 300px;"
              ext-popover-cls="resource-version-dropdown-content"
              v-model="searchParams.version">
              <bk-option v-for="option in versionList"
                :key="option.id"
                :id="option.id"
                :name="`${option.resource_version_display || '--'}`">
              </bk-option>
            </bk-select>
          </bk-form-item> -->
        </bk-form>
      </div>
      <div class="basic-bd">
        <bk-table
          :size="'small'"
          v-bkloading="{ isLoading: isDataLoading }"
          :data="sdkList"
          :pagination="pagination"
          @page-change="handlePageChange"
          @page-limit-change="handlePageLimitChange">
          <div slot="empty">
            <table-empty
              :keyword="tableEmptyConf.keyword"
              :abnormal="tableEmptyConf.isAbnormal"
              @reacquire="getSDKList"
              @clear-filter="clearFilterKey"
            />
          </div>
          <bk-table-column :label="$t('SDK版本号')" width="150" prop="version_number" :show-overflow-tooltip="true" :render-header="$renderHeader">
          </bk-table-column>
          <!-- <bk-table-column label="文件名" prop="filename" :show-overflow-tooltip="true">
                    </bk-table-column> -->
          <bk-table-column :label="$t('SDK名称')" prop="name" :show-overflow-tooltip="true" :render-header="$renderHeader">
          </bk-table-column>
          <bk-table-column :label="$t('SDK语言')" prop="language" :show-overflow-tooltip="true" :render-header="$renderHeader">
          </bk-table-column>
          <bk-table-column :label="$t('资源版本')" :show-overflow-tooltip="true" :render-header="$renderHeader">
            <template slot-scope="{ row }">
              {{row.resource_version_id ? `${row.resource_version_display || '--'}` : '--'}}
            </template>
          </bk-table-column>
          <bk-table-column
            :label="$t('包含非公开资源')"
            width="150"
            align="left"
            prop="include_private_resources"
            :formatter="(row, column, value) => value ? $t('是') : $t('否')">
          </bk-table-column>
          <bk-table-column
            :label="$t('是否公开')"
            width="150"
            align="left"
            prop="is_public"
            :formatter="(row, column, value) => value ? $t('是') : $t('否')">
          </bk-table-column>
          <bk-table-column :label="$t('创建时间')" prop="created_time" :render-header="$renderHeader">
          </bk-table-column>
          <bk-table-column
            fixed="right"
            :label="$t('操作')">
            <template slot-scope="{ row }">
              <bk-link theme="primary" class="action-link mr10"
                v-bk-tooltips="{ content: $t('未公开不可复制') , disabled: row.download_url }"
                :disabled="!row.download_url"
                @click="handleCopyUrl(row.download_url)">
                {{ $t('复制地址') }}
              </bk-link>
              <bk-link theme="primary" class="action-link"
                v-bk-tooltips="{ content: $t('未公开不可下载') , disabled: row.download_url }"
                :disabled="!row.download_url"
                :href="row.download_url" download>
                {{ $t('下载') }}
              </bk-link>
            </template>
          </bk-table-column>
        </bk-table>
      </div>
    </div>
    <!-- <div class="sdk-usage">
            <div class="title">SDK使用说明</div>
            <div class="subtitle">SDK有两种使用方式：shortcuts、RequestAPIClient。下面以调用网关 {{currentApigwName}} 下的资源 post_create_task 为例说明如何使用：</div>
            <dl class="sample-code">
                <div class="code-item">
                    <dt class="sample-title">shortcuts -- get_client_by_request</dt>
                    <dd class="code-content">
                        <code-viewer
                            ref="codeViewer"
                            :value="getCodeContent(sampleCodeContent['get_client_by_request'])"
                            :width="'100%'"
                            :height="195"
                            :lang="'python'"
                            :read-only="true"
                            @init="codeViewerInit">
                        </code-viewer>
                    </dd>
                </div>
                <div class="code-item">
                    <dt class="sample-title">shortcuts -- get_client_by_user</dt>
                    <dd class="code-content">
                        <code-viewer
                            :value="getCodeContent(sampleCodeContent['get_client_by_user'])"
                            :width="'100%'"
                            :height="216"
                            :lang="'python'"
                            :read-only="true"
                            @init="codeViewerInit">
                        </code-viewer>
                    </dd>
                </div>
                <div class="code-item">
                    <dt class="sample-title">RequestAPIClient</dt>
                    <dd class="code-content">
                        <code-viewer
                            :value="getCodeContent(sampleCodeContent['RequestAPIClient'])"
                            :width="'100%'"
                            :height="386"
                            :lang="'python'"
                            :read-only="true"
                            @init="codeViewerInit">
                        </code-viewer>
                    </dd>
                </div>
            </dl>
        </div> -->

    <bk-dialog
      v-model="buildDialog.visible"
      theme="primary"
      :width="660"
      :mask-close="false"
      :header-position="'left'"
      :title="buildDialog.title"
      @cancel="handleBuildCancel">
      <bk-form
        class="mt10 mb10 mr20"
        :label-width="150"
        ref="versionForm"
        :model="buildData">
        <bk-form-item :label="$t('资源版本')" required :error-display-type="'normal'">
          <bk-select
            searchable
            ext-popover-cls="resource-version-dropdown-content"
            :clearable="false"
            :disabled="initAction === 'create'"
            v-model="buildData.resource_version_id">
            <bk-option v-for="option in versionList"
              :key="option.id"
              :id="option.id"
              :name="`${option.resource_version_display || '--'}`">
            </bk-option>
          </bk-select>
          <p class="ag-tip mt5" v-show="resourceVersionEmpty">
            <i class="apigateway-icon icon-ag-info"></i> {{ $t('请先生成资源版本，再生成SDK') }}
          </p>
        </bk-form-item>
        <bk-form-item :label="$t('生成的语言')">
          <bk-select :clearable="false" v-model="buildData.language">
            <bk-option v-for="option in SDKLanguageList"
              :key="option.value"
              :id="option.value"
              :name="option.name">
            </bk-option>
          </bk-select>
        </bk-form-item>
        <bk-form-item :label="$t('SDK 版本号')"
          :rules="rules.version"
          :property="'version'"
          :icon-offset="-20">
          <bk-input
            v-model="buildData.version"
            :placeholder="$t('由数字、小写字母、中折线(-)、点号(.)组成，长度小于32个字符')"
          >
          </bk-input>
          <p class="ag-tip mt5">
            <i class="apigateway-icon icon-ag-info"></i> {{ $t('为空则由网关自动生成版本号，自定义版本号推荐遵从') }}
            &nbsp;{{ $t('Semver 规范') }}
          </p>
        </bk-form-item>
        <bk-form-item
          :label="$t('包含非公开资源')"
          :desc="$t('若选择，则网关所有资源写入到SDK；否则，仅公开的资源写入到SDK')"
          desc-type="icon">
          <bk-checkbox class="build-option-checkbox" v-model="buildData.include_private_resources"></bk-checkbox>
        </bk-form-item>
        <bk-form-item
          :label="$t('是否公开')"
          :desc="$t('发布到源')"
          desc-type="icon"
          v-if="GLOBAL_CONFIG.PLATFORM_FEATURE.ALLOW_UPLOAD_SDK_TO_REPOSITORY">
          <bk-checkbox class="build-option-checkbox" v-model="buildData.is_public"></bk-checkbox>
        </bk-form-item>
      </bk-form>
      <div slot="footer">
        <bk-button
          theme="primary"
          class="mr10"
          :disabled="buildConfirmButtonDisabled"
          :loading="buildDialog.loading"
          @click="SDKConfirm"> {{ $t('确定') }} </bk-button>
        <bk-button @click="handleBuildCancel" :disabled="buildDialog.loading"> {{ $t('取消') }} </bk-button>
      </div>
    </bk-dialog>
  </div>
</template>

<script>
  import { mapGetters, mapState } from 'vuex'
  import { catchErrorHandler } from '@/common/util'
  import sampleCodeContent from './code-content'

  export default {
    data () {
      return {
        isPageLoading: true,
        isDataLoading: false,
        sdkVersionKeyword: '',
        initResourceVersion: '',
        initAction: '',
        sampleCodeContent,
        buildDialog: {
          visible: false,
          loading: false,
          title: this.$t('生成SDK')
        },
        buildData: {
          resource_version_id: undefined,
          language: 'python',
          include_private_resources: false,
          is_public: false,
          version: ''
        },
        sdkList: [],
        versionList: [],
        searchParams: {
          sdk: '',
          version: ''
        },
        rules: {
          version: [
            {
              max: 32,
              message: this.$t('不能多于32个字符'),
              trigger: 'blur'
            },
            {
              validator (value) {
                if (value === '') {
                  return true
                } else {
                  const reg = /^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:-((?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?(?:\+([0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?$/
                  return reg.test(value)
                }
              },
              message: this.$t('由数字、字母、中折线（-）、点号（.）组成，长度小于32个字符，符合 Semver 规范'),
              trigger: 'blur'
            }
          ]
        },
        pagination: {
          current: 1,
          count: 0,
          limit: 10,
          'limit-list': [5, 10, 15, 20]
        },
        tableEmptyConf: {
          keyword: '',
          isAbnormal: false
        },
        sdkAllList: [],
        searchFilters: []
      }
    },
    computed: {
      ...mapGetters('options', ['SDKLanguageList']),
      ...mapState('apis', ['apigwList']),
      apigwId () {
        return this.$route.params.id
      },
      currentApigwName () {
        const current = this.apigwList.find(item => item.id === Number(this.apigwId)) || {}
        return current.name || ''
      },
      resourceVersionEmpty () {
        return !this.versionList.length
      },
      buildConfirmButtonDisabled () {
        return this.resourceVersionEmpty || !this.buildData.resource_version_id
      },
      searchData () {
        return [
          {
            name: this.$t('资源版本'),
            id: 'version',
            children: this.versionList.map(v => {
              return { name: v.resource_version_display, id: v.id }
            })
          },
          {
            name: this.$t('SDK版本号'),
            id: 'sdk',
            children: this.sdkAllList.map(v => {
              return { name: v.version_number, id: v.version_number }
            })
          }
        ]
      }
    },
    mounted () {
      const query = this.$route.query
      if (query.version && query.action === 'create') {
        this.buildData.resource_version_id = query.version
        this.buildDialog.visible = true
        this.initResourceVersion = query.version
        this.initAction = query.action
      } else if (query.version && query.action === 'search') {
        this.searchParams.version = query.version
      }
      this.getSDKList()
      this.getApigwVersions()

      this.$watch('searchParams', () => {
        this.pagination.current = 1
        this.getSDKList()
      }, { deep: true })
    },
    methods: {
      async getSDKList () {
        const apigwId = this.apigwId
        const params = {
          offset: (this.pagination.current - 1) * this.pagination.limit,
          limit: this.pagination.limit
        }
        if (this.searchParams.version) {
          params.resource_version_id = this.searchParams.version
        }
        if (this.searchParams.sdk) {
          params.version_number = this.searchParams.sdk
        }
        this.isDataLoading = true
        try {
          const res = await this.$store.dispatch('sdk/getApigwSDKs', { apigwId, params })
          this.sdkList = res.data.results
          if (!this.searchParams.version && !this.searchParams.sdk) {
            this.sdkAllList = res.data.results
          }
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
      async getApigwVersions () {
        const apigwId = this.apigwId
        const pageParams = {
          no_page: true
        }

        try {
          const res = await this.$store.dispatch('version/getApigwVersions', { apigwId, pageParams })
          this.versionList = res.data.results
        } catch (e) {
          catchErrorHandler(e, this)
        }
      },
      codeViewerInit (editor) {
        editor.setOptions({
          readOnly: true,
          highlightActiveLine: false,
          highlightGutterLine: false,
          showLineNumbers: false,
          showGutter: false
        })
        editor.renderer.$cursorLayer.element.style.opacity = 0
        editor.resize()
      },
      getCodeContent (content) {
        const currentApigwName = this.currentApigwName.toLocaleLowerCase().replace(/-/g, '_')
        return content.replace(/#apigw_name#/g, currentApigwName)
      },
      async SDKConfirm () {
        try {
          await this.$refs.versionForm.validate()
          this.handleBuildConfirm()
        } catch (e) {
          catchErrorHandler(e)
        }
      },
      async handleBuildConfirm () {
        const apigwId = this.apigwId
        const data = this.buildData
        this.buildDialog.loading = true
        try {
          const res = await this.$store.dispatch('sdk/buildApigwSDK', { apigwId, data })

          // 未公开
          if (data.is_public === false) {
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
                message: this.$t('生成成功！')
              })

              // 刷新列表
              if (this.initAction === 'create') {
                this.initAction = ''
                this.searchParams.version = this.buildData.resource_version_id
              }
              this.buildDialogClose()

              this.getSDKList()
            } else if (res.headers.get('Content-Type') === 'application/json') {
              const { message } = await res.json()
              this.$bkMessage({
                theme: 'error',
                message
              })
            } else {
              throw new Error(res.statusText)
            }
          } else {
            if (res.data) {
              this.sdkList = [res.data]
            }

            this.$bkMessage({
              theme: 'success',
              message: this.$t('生成成功！')
            })

            this.buildDialogClose()

            // 刷新列表
            this.getSDKList()
          }
        } catch (e) {
          catchErrorHandler(e, this)
        } finally {
          this.buildDialog.loading = false
        }
      },
      buildDialogClose () {
        this.initAction = ''
        this.buildDialog.visible = false

        this.buildData.resource_version_id = undefined
        this.buildData.include_private_resources = false
        this.buildData.is_public = false
        this.buildData.version = ''
      },
      handleBuildCancel () {
        this.buildDialogClose()
      },
      handleBuildSDK () {
        this.buildDialog.visible = true
      },
      handleCopyUrl (url) {
        this.$copyText(url).then((e) => {
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
      handlePageLimitChange (limit) {
        this.pagination.limit = limit
        this.pagination.current = 1
        this.getSDKList()
      },
      handlePageChange (newPage) {
        this.pagination.current = newPage
        this.getSDKList()
      },
      handleSearch () {
        this.searchParams.sdk = this.sdkVersionKeyword
      },
      clearFilterKey () {
        this.sdkVersionKeyword = ''
        this.searchParams.version = ''
        this.handleSearch()
      },

      updateTableEmptyConfig () {
        if (this.sdkVersionKeyword || this.searchParams.version) {
          this.tableEmptyConf.keyword = 'placeholder'
          return
        }
        this.tableEmptyConf.keyword = ''
      },
      formatFilterData () {
        const map = {}
        this.searchFilters.forEach(filter => {
          map[filter.id] = filter
        })
        for (const key in this.searchParams) {
          if (map[key]) {
            this.searchParams[key] = map[key].values[0].id
          } else {
            this.searchParams[key] = ''
          }
        }
      },
      // 清空筛选条件
      clearSearchFilters () {
        this.searchFilters = []
        for (const key in this.searchParams) {
          this.searchParams[key] = ''
        }
      }
    }
  }
</script>

<style lang="postcss" scoped>
    @import '@/css/variable.css';

    .basic-info {
        .basic-hd {
            height: 32px;
            margin-bottom: 10px;

            .title {
                position: relative;
                line-height: 32px;
                color: #313238;
                padding-left: 8px;
                font-size: 16px;

                &::before {
                    position: absolute;
                    left: 0;
                    top: 50%;
                    content: '';
                    width: 3px;
                    height: 16px;
                    background: #3A84FF;
                    transform: translateY(-8px);
                }
            }
        }

        .basic-bd {
            .action-link {
                /deep/.bk-link-text {
                    font-size: 12px;
                }
            }
        }
    }

    .sdk-usage {
        margin-top: 24px;

        .title {
            color: #63656E;
            font-size: 16px;
            font-weight: 700;
        }

        .subtitle {
            color: #63656E;
            font-size: 14px;
            margin-top: 8px;
        }

        .sample-code {
            .code-item {
                margin: 20px 0;
            }
            .sample-title {
                position: relative;
                color: #313238;
                padding-left: 12px;
                font-size: 14px;
                font-weight: 700;
                margin-bottom: 10px;

                &::before {
                    position: absolute;
                    left: 0;
                    top: 50%;
                    width: 4px;
                    height: 4px;
                    border-radius: 50%;
                    transform: translateY(-2px);
                    content: '';
                    background: #313238;
                }
            }
        }

        .ace-monokai {
            border-radius: 2px;
        }
    }

    .build-option-checkbox {
        line-height: 32px;
    }
</style>

<style lang="postcss">
    @import '@/css/mixins/ellipsis.css';
    .resource-version-dropdown-content {
        .bk-option-name {
            width: 100%;
            @mixin ellipsis;
        }
    }
</style>
