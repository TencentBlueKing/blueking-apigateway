<template>
  <div class="app-content pt25 pl25 pr25 pb10">
    <template v-if="curView === 'import'">
      <bk-form :label-width="100">
        <bk-form-item :label="$t('文档类型')">
          <div class="bk-button-group">
            <bk-radio-group v-model="docType">
              <bk-button class="ag-type-button" :class="docType === 'archive' ? 'is-selected' : ''" v-bk-tooltips="archiveTip">
                <bk-radio value="archive" class="bk-button-item" :class="docType === 'archive' ? 'radio-text' : ''">
                  <div class="pl15">
                    <div class="ag-type-name"> {{ $t('压缩包') }} </div>
                    <div class="ag-type-spec"> {{ $t('支持 tgz, zip 压缩格式') }} </div>
                  </div>
                </bk-radio>
              </bk-button>
              <bk-button class="ag-type-button" :class="docType === 'swagger' ? 'is-selected' : ''" v-bk-tooltips="swaggerTip">
                <bk-radio value="swagger" class="bk-button-item" :class="docType === 'swagger' ? 'radio-text' : ''">
                  <div class="pl15">
                    <div class="ag-type-name">Swagger</div>
                    <div class="ag-type-spec"> {{ $t('支持 json, yaml 格式') }} </div>
                  </div>
                </bk-radio>
              </bk-button>
            </bk-radio-group>
          </div>
        </bk-form-item>
        <bk-form-item :label="$t('文档语言')" v-if="docType === 'swagger'">
          <bk-radio-group class="pt5" v-model="language">
            <bk-radio value="zh" class="pr20"> {{ $t('中文文档') }} </bk-radio>
            <bk-radio value="en"> {{ $t('英文文档') }} </bk-radio>
          </bk-radio-group>
        </bk-form-item>
        <bk-form-item :label="$t('上传文件')">
          <div class="import-top" v-if="docType === 'swagger'">
            <bk-button icon="plus" class="import-btn" :key="uploadButtonKey">
              {{ $t('导入 Swagger 文件') }}
              <input ref="fileInput" type="file" name="upload" class="file-input" accept=".yaml,.json,.yml" @change="handleFileInput">
            </bk-button>
            <!-- <span class="import-tip">（json /yaml 格式）</span> -->

            <a :href="GLOBAL_CONFIG.DOC.SWAGGER" target="_blank" class="ag-text-link f14 fr mt10">
              <i class="apigateway-icon icon-ag-info" style="margin-right: 1px;"></i>
              {{ $t('Swagger 说明文档') }}
            </a>
            <a href="javascript: void(0);" class="ag-text-link f14 fr mt10 mr15" @click="handleShowExample">
              {{ $t('模板示例') }}
            </a>
          </div>

          <div class="import-top" v-else>
            <bk-button icon="plus" class="import-btn" :key="uploadButtonKey">
              {{ $t('导入文档压缩包') }}
              <input ref="fileArchive" type="file" name="upload" class="file-input" accept=".tar.gz,.tgz,.zip" @change="handleFileArchive">
            </bk-button>
          </div>
        </bk-form-item>
      </bk-form>

      <div class="import-container mt15" v-if="docType === 'swagger'">
        <code-viewer
          ref="bodyCodeViewer"
          :placeholder="$t('请选择 Swagger 文件(json/yaml)')"
          :value="content"
          :width="'100%'"
          :height="yamlViewerHeight"
          :lang="'yaml'"
          :key="uploadButtonKey"
          @input="handleInput"
          @focus="isViewerFocus = true"
          @blur="isViewerFocus = false">
        </code-viewer>

        <div class="mt20">
          <bk-button
            class="mr10"
            theme="primary"
            type="button"
            :title="$t('下一步')"
            @click.stop.prevent="checkData" :loading="isDataLoading">
            {{ $t('下一步') }}
          </bk-button>
          <bk-button
            theme="default"
            type="button"
            :title="$t('取消')"
            :disabled="isDataLoading"
            @click="goBack">
            {{ $t('取消') }}
          </bk-button>
        </div>
      </div>
      <bk-sideslider
        :quick-close="true"
        :title="$t('模板示例')"
        :width="650"
        :is-show.sync="exampleConf.isShow"
        :before-close="handleBeforeClose">
        <div slot="content" class="p0">
          <code-viewer
            ref="exampleViewer"
            :value="exampleConf.content"
            :width="'100%'"
            :height="exampleConf.height"
            :lang="'yaml'"
            @input="handleChange">
          </code-viewer>
        </div>
      </bk-sideslider>
    </template>
    <template v-else>
      <p class="f14 ag-table-header">
        {{ $t('请确认以下文档变更：') }}
        <span v-html="addInfo"></span>
        <span v-html="coverInfo"></span>
        <span v-html="resourceInfo"></span>
        <bk-input
          class="fr"
          :clearable="true"
          v-model="pathUrl"
          :placeholder="docType !== 'swagger' ? $t('请输入文件名、请求路径，按Enter搜索') : $t('请输入请求路径，按Enter搜索')"
          :right-icon="'bk-icon icon-search'"
          style="width: 328px;"
          @enter="filterData">
        </bk-input>
        <bk-checkbox-group v-model="selectOperateType" class="checkbox-group fr ag-checkbox-header">
          <bk-checkbox value="create" @change="selectType" class="pr15"> {{ $t('勾选新增文档') }} </bk-checkbox>
          <bk-checkbox value="merge" @change="selectType"> {{ $t('勾选已存在文档') }} </bk-checkbox>
        </bk-checkbox-group>
      </p>
      <bk-table
        ref="groupTableRef"
        :data="resourceList"
        :size="'small'"
        :ext-cls="'resource-table-container'"
        :cell-style="{ 'overflow': 'visible', 'white-space': 'normal' }"
        v-bkloading="{ isLoading: isDataLoading }"
        @select="handlerChange"
        @select-all="handlerChangeAll"
        @filter-change="handleFilterChange">
        <div slot="empty">
          <table-empty
            :keyword="tableEmptyConf.keyword"
            @clear-filter="clearFilterKey"
          />
        </div>
        <bk-table-column type="selection" width="60" :selectable="setDefaultSelect"></bk-table-column>
        <bk-table-column
          v-if="docType !== 'swagger'"
          :label="$t('文件名称')"
          column-key="name"
          prop="name"
          :render-header="$renderHeader">
          <template slot-scope="props">
            <div v-bk-tooltips.top="props.row.filename">
              <span class="ag-auto-text">
                {{props.row.filename || '--'}}
              </span>
            </div>
          </template>
        </bk-table-column>
        <bk-table-column
          :label="$t('请求路径')"
          prop="path"
          sortable
          column-key="path"
          :render-header="$renderHeader">
          <template slot-scope="props">
            <div class="ag-flex">
              <div v-bk-tooltips.top="props.row.path">
                {{props.row.path || '--'}}
              </div>
              <div>
                <span class="ag-tag success ml5" v-if="props.row.has_updated"> {{ $t('有更新') }} </span>
              </div>
            </div>
          </template>
        </bk-table-column>
        <bk-table-column
          width="150"
          :label="$t('请求方法')"
          prop="method"
          :render-header="$renderHeader"
          :filters="methodFilters"
          :filter-multiple="false"
          column-key="method">
          <template slot-scope="props">
            <span class="ag-tag" :class="props.row.method.toLowerCase()">{{props.row.method || '--'}}</span>
          </template>
        </bk-table-column>
        <bk-table-column
          :label="$t('描述')"
          column-key="description"
          prop="description"
          :render-header="$renderHeader">
          <template slot-scope="props">
            <div v-bk-tooltips.top="props.row.description">
              <span class="ag-auto-text">
                {{props.row.description || '--'}}
              </span>
            </div>
          </template>
        </bk-table-column>
        <bk-table-column
          :label="$t('文档语言')"
          column-key="resourceDocLanguage"
          prop="resourceDocLanguage"
          :render-header="$renderHeader"
          :filters="languageFilters"
          :filter-multiple="false">
          <template slot-scope="props">
            <div>
              <span class="ag-auto-text">
                {{resourceDocLanguages[props.row.resource_doc_language] || '--'}}
              </span>
            </div>
          </template>
        </bk-table-column>
        <bk-table-column
          width="250"
          :label="$t('操作类型')"
          prop="type"
          column-key="type"
          :render-header="$renderHeader"
          :filters="docTypeFilters"
          :filter-multiple="false"
        >
          <template slot-scope="props">
            <div v-if="props.row.id">
              <div class="update-text" style="color: #EA3636" v-if="props.row.resource_doc_id">
                {{ $t('覆盖') }}
              </div>
              <div v-else style="color: #2DCB56">
                {{ $t('新建') }}
              </div>
            </div>
            <div v-else class="ag-no-docid"> {{ $t('资源不存在，无法导入') }} </div>
          </template>
        </bk-table-column>
      </bk-table>
      <div class="mt20">
        <bk-button
          class="mr10"
          type="button"
          :title="$t('上一步')"
          :disabled="isDataLoading"
          @click.stop.prevent="goPrev">
          {{ $t('上一步') }}
        </bk-button>
        <bk-button
          v-if="selectedResourceDocs.length"
          class="mr10"
          theme="primary"
          type="button"
          :title="$t('确定导入')"
          @click.stop.prevent="handleImportResource" :loading="isDataLoading">
          {{ $t('确定导入') }}
        </bk-button>
        <div
          v-else
          v-bk-tooltips="$t('请确认勾选资源文档')"
          class="tips-disabled-btn mr10"
        >
          {{ $t('确定导入') }}
        </div>
        <bk-button
          theme="default"
          type="button"
          :title="$t('取消')"
          :disabled="isDataLoading"
          @click="goBack">
          {{ $t('取消') }}
        </bk-button>
      </div>
    </template>
  </div>
</template>

<script>
  import { catchErrorHandler, clearFilter, isTableFilter } from '@/common/util'
  import example from './example.js'
  import axios from 'axios'
  import cookie from 'cookie'
  import sidebarMixin from '@/mixins/sidebar-mixin'
  export default {
    mixins: [sidebarMixin],
    data () {
      return {
        isMerge: true,
        content: example.content,
        curView: 'import',
        isDataLoading: false,
        yamlViewerHeight: 300,
        isViewerFocus: false,
        uploadButtonKey: 0,
        pagination: {
          current: 1,
          count: 0,
          limit: 10
        },
        exampleConf: {
          isShow: false,
          height: 400,
          content: example.content
        },
        resourceList: [],
        curPageData: [],
        originResourceList: [],
        filterSelectedList: [],
        resource: {
          content: example.content,
          allow_overwrite: true
        },
        typeFilters: [
          {
            value: 'create',
            text: this.$t('新建')
          },
          {
            value: 'merge',
            text: this.$t('覆盖')
          }
        ],
        docType: 'archive',
        language: 'zh',
        selectedResourceDocs: [],
        selectedResourceDocsCopy: [],
        pathUrl: '',
        selectOperateType: ['create', 'merge'],
        resourceDocLanguages: { 'zh': this.$t('中文'), 'en': this.$t('英文') },
        docTypeFilters: [
          {
            value: this.$t('新建'),
            text: this.$t('新建')
          },
          {
            value: this.$t('覆盖'),
            text: this.$t('覆盖')
          },
          {
            value: this.$t('资源不存在'),
            text: this.$t('资源不存在')
          }
        ],
        typeFiltersEmums: { 'create': '新建', 'merge': '覆盖' },
        archiveTip: {
          theme: 'dark',
          allowHtml: true,
          content: this.$t('提示信息'),
          html: `${this.$t('请先将 markdown 格式的资源文档归档为压缩包，然后导入该文档压缩包，如何归档资源文档，请参考')}，<a target="_blank" href=${this.GLOBAL_CONFIG.DOC.IMPORT_RESOURCE_DOCS} style="color: #3a84ff">${this.$t('更多详情')}</a>`,
          placements: ['top']
        },
        swaggerTip: {
          theme: 'dark',
          allowHtml: true,
          content: this.$t('提示信息'),
          html: `${this.$t('Swagger 协议中描述了接口说明，利用其中内容生成资源文档')}，<a target="_blank" href=${this.GLOBAL_CONFIG.DOC.IMPORT_RESOURCE_DOCS} style="color: #3a84ff">${this.$t('更多详情')}</a>`,
          placements: ['top']
        },
        tableEmptyConf: {
          keyword: ''
        },
        filterList: {},
        swaggerActiveIndex: 1
      }
    },

    computed: {
      languageFilters () {
        return Object.keys(this.resourceDocLanguages).reduce((p, e) => {
          p.push({
            value: e,
            text: this.resourceDocLanguages[e]
          })
          return p
        }, [])
      },
      methodFilters () {
        return this.$store.state.options.methodList.map(item => {
          return {
            value: item.id,
            text: item.id

          }
        })
      },
      apigwId () {
        return this.$route.params.id
      },
      resourceId () {
        return this.$route.params.resourceId || undefined
      },
      createNum () {
        const results = this.selectedResourceDocs.filter(item => item.id && !item.resource_doc_id)
        return results.length
      },
      updateNum () {
        const results = this.selectedResourceDocs.filter(item => item.id && item.resource_doc_id)
        return results.length
      },
      noExistNum () {
        const results = this.resourceList.filter(item => !item.id)
        return results.length
      },
      addInfo () {
        return this.$t(`新建 <strong style="color: #2DCB56;"> {createNum} </strong> 条，`, { createNum: this.createNum })
      },
      coverInfo () {
        return this.$t(`覆盖 <strong style="color: #3a84ff;"> {updateNum} </strong> 条，`, { updateNum: this.updateNum })
      },
      resourceInfo () {
        return this.$t(`资源不存在 <strong style="color: #EA3536;"> {noExistNum} </strong> 条`, { noExistNum: this.noExistNum })
      }
    },

    watch: {
      selectOperateType (value, oldVal) {
        console.log('value', value)
        console.log('this.selectTypeValue', this.selectTypeValue)
        this.selectedResourceDocs = []
        if (!value.length) {
          if (!this.selectedResourceDocsCopy.length) {
            this.originResourceList.forEach(item => {
              this.$refs.groupTableRef && this.$refs.groupTableRef.toggleRowSelection(item, false)
            })
          } else {
            if (oldVal.join('') === 'merge') {
              this.originResourceList.filter(e => e.typeText === '覆盖').forEach(item => {
                this.$refs.groupTableRef && this.$refs.groupTableRef.toggleRowSelection(item, false)
              })
            } else {
              this.originResourceList.filter(e => e.typeText === '新建').forEach(item => {
                this.$refs.groupTableRef && this.$refs.groupTableRef.toggleRowSelection(item, false)
              })
            }
          }
        }

        if (value.join('') === 'merge') {
          console.log('this.selectTypeValue', this.selectTypeValue)
          if (this.selectTypeValue === 'merge') {
            this.originResourceList.filter(e => e.typeText === '覆盖').forEach(item => {
              this.$refs.groupTableRef && this.$refs.groupTableRef.toggleRowSelection(item, true)
              this.selectedResourceDocs.push({
                language: this.docType === 'swagger' ? this.language : item.resource_doc_language,
                resource_name: item.name,
                name: item.name,
                id: item.id,
                resource_doc_id: item.resource_doc_id,
                filename: item.filename || ''
              })
            })
          }
          if (!this.selectTypeValue) {
            this.originResourceList.filter(e => e.typeText === '新建').forEach(item => {
              this.$refs.groupTableRef && this.$refs.groupTableRef.toggleRowSelection(item, false)
            })
            const data = this.originResourceList.filter(e => !!e.id && !!e.resource_doc_id)
            console.log('data1111', data)
            this.handChangeData(data)
          }
        }

        if (value.join('') === 'create') {
          if (this.selectTypeValue === 'create') {
            this.originResourceList.filter(e => e.typeText === '新建').forEach(item => {
              this.$refs.groupTableRef && this.$refs.groupTableRef.toggleRowSelection(item, true)
              this.selectedResourceDocs.push({
                language: this.docType === 'swagger' ? this.language : item.resource_doc_language,
                resource_name: item.name,
                name: item.name,
                id: item.id,
                resource_doc_id: item.resource_doc_id,
                filename: item.filename || ''
              })
            })
          }
          if (!this.selectTypeValue) {
            this.originResourceList.filter(e => e.typeText === '覆盖').forEach(item => {
              this.$refs.groupTableRef && this.$refs.groupTableRef.toggleRowSelection(item, false)
            })
            const data = this.originResourceList.filter(e => !!e.id && !e.resource_doc_id)
            this.handChangeData(data)
          }
        }

        if (value.length === 2) {
          let data = this.originResourceList
          console.log('this.selectTypeValue', this.selectTypeValue)
          if (this.selectTypeValue === 'merge') {
            data = this.originResourceList.filter(e => !!e.id && !!e.resource_doc_id)
          } else if (this.selectTypeValue === 'create') {
            data = this.originResourceList.filter(e => !!e.id && !e.resource_doc_id)
          }

          const dataSelect = this.deDuplication([...data, ...this.selectedResourceDocsCopy], this.docType === 'swagger' ? 'name' : 'filename')

          data.forEach(item => {
            if (item.id) {
              this.$refs.groupTableRef && this.$refs.groupTableRef.toggleRowSelection(item, true)
            }
          })

          dataSelect.forEach(item => {
            if (item.id) {
              this.selectedResourceDocs.push({
                language: this.docType === 'swagger' ? this.language : item.resource_doc_language || item.language,
                resource_name: item.name,
                name: item.name,
                id: item.id,
                resource_doc_id: item.resource_doc_id,
                filename: item.filename || ''
              })
            }
          })

          this.selectedResourceDocsCopy = [...this.selectedResourceDocs]
        }
        console.log('this.selectedResourceDocs', this.selectedResourceDocs)
      },
      pathUrl (value) {
        if (!value) {
          this.originResourceList = [...this.curPageData]
          this.resourceList = this.originResourceList
          this.selectedResourceDocs = []
          this.$nextTick(() => {
            this.$nextTick(() => {
              this.handChangeData(this.originResourceList)
            })
          })
        }
      }
    },

    mounted () {
      const winHeight = window.innerHeight
      const offsetTop = 450
      this.exampleConf.height = winHeight - 52
      if ((winHeight - offsetTop) > this.yamlViewerHeight) {
        this.yamlViewerHeight = winHeight - offsetTop
      }
      this.$store.commit('setMainContentLoading', false)

      this.axiosInstance = axios.create({
        withCredentials: true,
        headers: { 'X-REQUESTED-WITH': 'XMLHttpRequest' }
      })
    },

    methods: {

      goBack () {
        const self = this
        if (this.resource.content) {
          this.$bkInfo({
            title: this.$t('确定要放弃资源文档导入？'),
            confirmFn () {
              self.goResourceIndex()
            }
          })
        } else {
          self.goResourceIndex()
        }
      },

      goPrev () {
        this.curView = 'import'
      },

      goResourceIndex () {
        this.$router.push({
          name: 'apigwResource',
          params: {
            id: this.apigwId
          }
        })
      },
      handleInput (content) {
        this.resource.content = content
      },

      handleFileInput () {
        const fileInput = this.$refs.fileInput
        const self = this
        if (fileInput.files && fileInput.files.length) {
          const file = fileInput.files[0]
          const reg = '.*\\.(json|yaml|yml)'
          if (!file.name.match(reg)) {
            this.$bkMessage({
              theme: 'error',
              message: this.$t('仅支持 json, yaml 格式')
            })
            return
          }
          if (window.FileReader) {
            const reader = new FileReader()
            reader.onloadend = function (event) {
              if (event.target.readyState === FileReader.DONE) {
                console.log(event.target)
                self.content = event.target.result
                self.resource.content = event.target.result
                setTimeout(() => {
                  self.$refs.bodyCodeViewer.$ace.scrollToLine(1, true, true)
                  // self.$refs.bodyCodeViewer.$ace.scrollToLine(1, true, true)
                }, 0)
                self.uploadButtonKey++
              }
            }
            reader.readAsText(file)
          }
        }
      },

      handleFileArchive () {
        const apigwId = this.apigwId
        const fileArchive = this.$refs.fileArchive
        if (fileArchive.files && fileArchive.files.length) {
          this.file = fileArchive.files[0]
          const formData = new FormData()
          formData.append('file', this.file)
          const CSRFToken = cookie.parse(document.cookie)[DASHBOARD_CSRF_COOKIE_NAME || `${window.PROJECT_CONFIG.BKPAAS_APP_ID}_csrftoken`]
          this.axiosInstance.post(`${DASHBOARD_URL}/apis/${apigwId}/support/resources/docs/archive/parse/`, formData, {
            headers: {
              'Content-Type': 'multipart/form-data',
              'X-CSRFToken': CSRFToken
            }
          }).then(res => {
            this.curView = 'resources'
            res.data.data.forEach(item => {
              item.description = item.description || '--'
              item.path = item.path || '--'
              if (item.id) {
                if (item.resource_doc_id) {
                  item.typeText = '覆盖'
                } else {
                  item.typeText = '新建'
                }
              }
            })
            this.curPageData = res.data.data
            this.resourceList = res.data.data
            this.originResourceList = res.data.data
            this.handlSelectData()
            this.updateTableEmptyConfig()
          }).catch(err => {
            const { status, data } = err.response
            if (status === 500) {
              this.$bkMessage({
                theme: 'error',
                message: this.$t('系统出现异常')
              })
            } else {
              this.$bkMessage({
                theme: 'error',
                message: data.message
              })
            }
          }).finally(() => {
            this.uploadButtonKey++
          })
        }
      },

      async handleImportResource () {
        if (this.isDataLoading) {
          return false
        }

        if (!this.selectedResourceDocs.length) {
          this.$bkMessage({
            theme: 'error',
            message: this.$t('请确认勾选资源文档')
          })
          return false
        }

        this.isDataLoading = true
        try {
          const apigwId = this.apigwId
          let params = this.resource
          if (this.docType === 'swagger') {
            params = {
              selected_resource_docs: this.selectedResourceDocs,
              swagger: this.resource.content
            }
            await this.$store.dispatch('resource/importSwagger', { apigwId, params })
          } else {
            const selectedResourceDocs = this.selectedResourceDocs.reduce((p, v) => {
              p.push({
                language: v.language,
                resource_name: v.resource_name
              })
              return p
            }, [])
            const formData = new FormData()
            formData.append('file', this.file)
            formData.append('selected_resource_docs', JSON.stringify(selectedResourceDocs))
            const CSRFToken = cookie.parse(document.cookie)[DASHBOARD_CSRF_COOKIE_NAME || `${window.PROJECT_CONFIG.BKPAAS_APP_ID}_csrftoken`]
            await this.axiosInstance.post(`${DASHBOARD_URL}/apis/${apigwId}/support/resources/docs/import/by-archive/`, formData, {
              headers: {
                'Content-Type': 'multipart/form-data',
                'X-CSRFToken': CSRFToken
              }
            })
          }
          this.goResourceIndex()
          this.$bkMessage({
            theme: 'success',
            message: this.$t('资源导入成功')
          })
        } catch (e) {
          catchErrorHandler(e, this)
        } finally {
          setTimeout(() => {
            this.isDataLoading = false
          }, 500)
        }
      },

      async checkData () {
        if (this.isDataLoading) {
          return false
        }

        if (!this.resource.content) {
          this.$bkMessage({
            theme: 'error',
            message: this.$t('请输入Swagger内容')
          })
          return false
        }

        this.isDataLoading = true
        try {
          const apigwId = this.apigwId
          const params = this.resource
          params.resource_doc_language = this.language
          const res = await this.$store.dispatch('resource/checkResourceImport', { apigwId, params })

          res.data.forEach(item => {
            if (item.id) {
              if (item.resource_doc_id) {
                item.typeText = '覆盖'
              } else {
                item.typeText = '新建'
              }
            }
          })

          this.curView = 'resources'
          this.content = this.resource.content
          this.resourceList = res.data
          this.curPageData = res.data
          this.originResourceList = res.data
          this.handlSelectData()
        } catch (e) {
          this.$bkInfo({
            type: 'error',
            title: this.$t('资源导入配置错误'),
            subTitle: e.message,
            showFooter: false
          })
        } finally {
          setTimeout(() => {
            this.isDataLoading = false
          }, 500)
        }
      },

      handlSelectData () {
        this.selectedResourceDocs = []
        this.$nextTick(() => {
          this.originResourceList.forEach(item => {
            this.selectOperateType.forEach(e => {
              if (this.typeFiltersEmums[e] === item.typeText) {
                this.$refs.groupTableRef && this.$refs.groupTableRef.toggleRowSelection(item, true)
                this.selectedResourceDocs.push({
                  language: this.docType === 'swagger' ? this.language : item.resource_doc_language,
                  resource_name: item.name,
                  name: item.name,
                  id: item.id,
                  resource_doc_id: item.resource_doc_id,
                  filename: item.filename || ''
                })
              }
            })
          })
          this.selectedResourceDocsCopy = [...this.selectedResourceDocs]
        })
      },

      handChangeData (data) {
        if (!!data && data.length) {
          data.forEach(item => {
            this.selectedResourceDocsCopy.forEach(e => {
              if (e.resource_name === item.name) {
                if (this.docType === 'swagger' || e.filename === item.filename) {
                  this.$refs.groupTableRef && this.$refs.groupTableRef.toggleRowSelection(item, true)
                  this.selectedResourceDocs.push({
                    language: this.docType === 'swagger' ? this.language : item.resource_doc_language,
                    resource_name: item.name,
                    name: item.name,
                    id: item.id,
                    resource_doc_id: item.resource_doc_id,
                    filename: item.filename || ''
                  })
                }
              }
            })
          })
          this.updateTableEmptyConfig()
        }
      },

      handleShowExample () {
        this.exampleConf.isShow = true
        setTimeout(() => {
          this.$refs.exampleViewer.$ace.scrollToLine(1, true, true)
          this.$refs.exampleViewer.$ace.scrollToLine(1, true, true)
          this.initSidebarFormData(this.swaggerActiveIndex)
        }, 0)
      },

      handleFilterChange (filters) {
        this.filterList = filters
        if (filters.method && filters.method.length) {
          this.originResourceList = this.curPageData.filter(item => filters.method.includes(item.method))
          this.resourceList = this.originResourceList
        } else if (filters.resourceDocLanguage && filters.resourceDocLanguage.length) {
          this.originResourceList = this.curPageData.filter(item => filters.resourceDocLanguage.includes(item.resource_doc_language))
          this.resourceList = this.originResourceList
        } else if (filters.type && filters.type.length) {
          if (filters.type.join('') === '资源不存在') {
            this.originResourceList = this.curPageData.filter(item => !item.id)
          } else {
            this.originResourceList = this.curPageData.filter(item => filters.type.includes(item.typeText))
          }
          this.resourceList = this.originResourceList
        } else {
          this.originResourceList = [...this.curPageData]
          this.resourceList = this.originResourceList
        }
        this.$nextTick(() => {
          this.selectedResourceDocs = []
          this.handChangeData(this.curPageData)
        })
      },

      handlerChange (payload) {
        this.selectedResourceDocs = [...payload].reduce((prev, item) => {
          prev.push({
            language: this.docType === 'swagger' ? this.language : item.resource_doc_language,
            resource_name: item.name,
            name: item.name,
            id: item.id,
            resource_doc_id: item.resource_doc_id,
            filename: item.filename || ''
          })
          return prev
        }, [])
        this.selectedResourceDocsCopy = [...this.selectedResourceDocs]
      },

      handlViewerFocus () {
        console.log(this.$refs.bodyCodeViewer.$ace)
        this.$refs.bodyCodeViewer.$ace.focus()
      },

      setDefaultSelect (payload) {
        return !!payload.id
      },
      handlerChangeAll (payload) {
        if (!payload.length) {
          this.selectOperateType = []
          this.selectedResourceDocs = []
        } else {
          this.selectOperateType = ['create', 'merge']
        }
      },
      selectType (value) {
        this.selectTypeValue = value
      },
      deDuplication (data, k) {
        const map = new Map()
        for (const item of data) {
          if (item[k] && !map.has(item[k])) {
            map.set(item[k], item)
          }
        }
        return [...map.values()]
      },
      filterData () {
        if (this.docType === 'swagger') {
          this.originResourceList = this.curPageData.filter(e => e.path.includes(this.pathUrl))
        } else {
          this.originResourceList = this.curPageData.filter(e => e.path.includes(this.pathUrl) || e.filename.includes(this.pathUrl))
        }
        this.resourceList = [...this.originResourceList]
        this.$nextTick(() => {
          this.selectedResourceDocs = []
          this.handChangeData(this.curPageData)
        })
      },
      clearFilterKey () {
        this.pathUrl = ''
        this.$refs.groupTableRef.clearFilter()
        if (this.$refs.groupTableRef && this.$refs.groupTableRef.$refs.tableHeader) {
          clearFilter(this.$refs.groupTableRef.$refs.tableHeader)
        }
      },
      updateTableEmptyConfig () {
        const isFilter = isTableFilter(this.filterList)
        if (this.pathUrl || isFilter) {
          this.tableEmptyConf.keyword = 'placeholder'
          return
        }
        this.tableEmptyConf.keyword = ''
      },
      // 输入为激活状态
      handleChange () {
        this.swaggerActiveIndex++
      },
      async handleBeforeClose () {
        return this.$isSidebarClosed(JSON.stringify(this.swaggerActiveIndex))
      }
    }
  }
</script>

<style scoped lang="postcss">
    .merge-text {
        color: #313238;
        font-size: 14px;
        vertical-align: middle;
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
        font-size: 12px;
        color: #979ba5;
    }
    .overwrite-text {
        color: #EA3536;
    }
    .update-text {
        color: #FE9C00;
    }
    .ag-no-docid{
        color: #c4c6cc;
    }
    .import-container {
        position: relative;
        margin-left: 100px;
        .ap-nodata {
            width: 100%;
            position: absolute;
            left: 0;
            top: 43%;
            z-index: 1000;
            transform: translate(0, -50%);
            color: #c3cdd7;
        }
    }
    .bk-button-item{
        width: 100%;
    }
    .radio-text {
        color: #3a84ff;
    }
    .ag-type-button {
        height: 56px;
        width: 270px;
        text-align: left;
    }
    .ag-type-name{
        font-size: 12px;
        font-weight: bold;
    }
    .ag-type-spec {
        font-size: 12px;
    }
    .ag-table-header{
        height: 32px;
        line-height: 32px;
        color: #63656E;
    }
    .ag-checkbox-header{
        width: auto;
        margin-right: 32px;
        line-height: 32px;
    }
    .resource-table-container{
        overflow-y: scroll;
        max-height: 70vh;
        margin-top: 15px;
        position: relative;
    }
</style>
