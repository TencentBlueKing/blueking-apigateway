<template>
  <div class="app-content pt25 pl25 pr25 pb10 resource-doc-wrapper">
    <template v-if="curView === 'import'">
      <div class="import-top">
        <bk-button icon="plus" class="import-btn" :key="uploadButtonKey">
          {{ $t('导入 Swagger 文件') }}
          <input ref="fileInput" type="file" name="upload" class="file-input" @change="handleFileInput">
        </bk-button>
        <span class="import-tip"> {{ $t('（json /yaml 格式）') }} </span>

        <!-- <span class="merge-text">是否覆盖</span>
                <i class="apigateway-icon icon-ag-info" v-bk-tooltips="'若覆盖，则已存在资源的配置将被更新；否则，已存在的资源将被跳过'"></i>
                <bk-checkbox
                    :true-value="true"
                    :false-value="false"
                    v-model="resource.allow_overwrite">
                </bk-checkbox> -->
        <bk-form :label-width="200" form-type="inline">
          <bk-form-item>
            <bk-checkbox class="pr15 ml20 mr30" v-model="showDoc" v-bk-tooltips="docsTip"> {{ $t('生成资源文档') }} </bk-checkbox>
          </bk-form-item>
          <bk-form-item :label="$t('文档语言')" v-if="showDoc" :required="true">
            <bk-radio-group v-model="language" class="ag-radio-header">
              <bk-radio :value="'zh'" class="pl15 pt5">
                <div> {{ $t('中文文档') }} </div>
              </bk-radio>
              <bk-radio :value="'en'" class="pl15 pt5">
                <div> {{ $t('英文文档') }} </div>
              </bk-radio>
            </bk-radio-group>
          </bk-form-item>
        </bk-form>

        <a :href="GLOBAL_CONFIG.DOC.SWAGGER" target="_blank" class="ag-text-link f14 fr mt10">
          <i class="apigateway-icon icon-ag-info" style="margin-right: 1px;"></i>
          {{ $t('Swagger 说明文档') }}
        </a>
        <a href="javascript: void(0);" class="ag-text-link f14 fr mt10 mr15" @click="handleShowExample">
          {{ $t('模板示例') }}
        </a>
      </div>

      <div class="import-container mt15">
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
        {{ $t('请确认以下资源变更，资源配置：') }}
        <span v-html="addInfo"></span>
        <span v-html="coverInfo"></span>
        <span v-if="showDoc">
          ，{{ $t('资源文档：') }}
          <span v-html="addResourceDoc"></span>
          <span v-html="coverResourceDoc"></span>
        </span>
        <bk-input
          class="fr"
          :clearable="true"
          :placeholder="$t('请输入请求路径，按Enter搜索')"
          :right-icon="'bk-icon icon-search'"
          style="width: 328px;"
          v-model="path"
          @enter="filterData">
        </bk-input>
        <bk-checkbox-group v-model="selectOperateType" class="checkbox-group fr ag-checkbox-header">
          <bk-checkbox value="create" @change="selectType" class="pr15"> {{ $t('勾选新增资源') }} </bk-checkbox>
          <bk-checkbox value="merge" @change="selectType"> {{ $t('勾选已存在资源') }} </bk-checkbox>
        </bk-checkbox-group>
      </p>
      <div class="resource-table-wrapper" v-bkloading="{ isLoading: isDataLoading }">
        <bk-table
          ref="groupTableRef"
          :data="resourceList"
          :size="'small'"
          :ext-cls="'resource-table-container'"
          :cell-style="{ 'overflow': 'visible', 'white-space': 'normal' }"
          v-bkloading="{ isLoading: isDataLoading }"
          @select-all="handlerChangeAll"
          @select="handlerChange"
          @filter-change="handleFilterChange">
          <div slot="empty">
            <table-empty
              :keyword="tableEmptyConf.keyword"
              @clear-filter="clearFilterKey"
            />
          </div>
          <bk-table-column type="selection" width="60"></bk-table-column>
          <bk-table-column
            :label="$t('请求路径')"
            prop="path"
            :render-header="$renderHeader"
            sortable
            column-key="path">
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
              <span class="ag-tag" :class="props.row.method.toLowerCase()">{{props.row.method}}</span>
            </template>
          </bk-table-column>
          <bk-table-column
            :label="$t('描述')"
            column-key="name"
            prop="name">
            <template slot-scope="props">
              <div v-bk-tooltips.top="props.row.description">
                <span class="ag-auto-text">
                  {{props.row.description || '--'}}
                </span>
              </div>
            </template>
          </bk-table-column>
          <bk-table-column
            v-if="showDoc"
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
            :label="$t('资源操作类型')"
            prop="id"
            column-key="type"
            :render-header="$renderHeader"
            :filters="typeFilters"
            :filter-multiple="false"
          >
            <template slot-scope="props">
              <div class="update-text" v-if="props.row.id">
                {{ $t('覆盖') }}
              </div>
              <div v-else style="color: #2DCB56">
                {{ $t('新建') }}
              </div>
            </template>
          </bk-table-column>
          <bk-table-column
            v-if="showDoc"
            width="250"
            :label="$t('文档操作类型')"
            prop="docType"
            column-key="docType"
            :render-header="$renderHeader"
            :filters="typeFilters"
            :filter-multiple="false"
          >
            <template slot-scope="props">
              <div class="update-text" v-if="props.row.resource_doc_id">
                {{ $t('覆盖') }}
              </div>
              <div v-else style="color: #2DCB56">
                {{ $t('新建') }}
              </div>
            </template>
          </bk-table-column>
        </bk-table>
      </div>
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
          v-bk-tooltips="$t('请确认勾选资源')"
          class="tips-disabled-btn mr10"
        >
          {{ $t('确定导入') }}
        </div>
        <bk-button
          theme="default"
          type="button"
          title="取消"
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
        showDoc: false,
        language: 'zh',
        selectOperateType: ['create', 'merge'],
        resourceDocLanguages: { 'zh': this.$t('中文'), 'en': this.$t('英文') },
        selectedResourceDocs: [],
        selectedResource: [],
        selectedResourceDocsCopy: [],
        selectedResourceCopy: [],
        selectedResourceDocsCopyT: [],
        selectedResourceCopyT: [],
        path: '',
        typeFiltersEmums: { 'create': this.$t('新建'), 'merge': this.$t('覆盖') },
        selectTypeValue: true,
        docsTip: {
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
        const results = this.deDuplication(this.selectedResource.filter(item => !item.id), 'name')
        return results.length
      },
      updateNum () {
        const results = this.deDuplication(this.selectedResource.filter(item => item.id), 'name')
        return results.length
      },
      createDocNum () {
        const results = this.deDuplication(this.selectedResourceDocs.filter(item => !item.resource_doc_id), 'resource_name')
        return results.length
      },
      updateDocNum () {
        const results = this.deDuplication(this.selectedResourceDocs.filter(item => item.resource_doc_id), 'resource_name')
        return results.length
      },
      addInfo () {
        return this.$t(`新建 <strong style="color: #2DCB56;"> {createNum} </strong> 条，`, { createNum: this.createNum })
      },
      coverInfo () {
        return this.$t(`覆盖 <strong style="color: #EA3536;"> {updateNum} </strong> 条`, { updateNum: this.updateNum })
      },
      addResourceDoc () {
        return this.$t(`新建 <strong style="color: #2DCB56;"> {createDocNum} </strong> 条，`, { createDocNum: this.createDocNum })
      },
      coverResourceDoc () {
        return this.$t(`覆盖 <strong style="color: #EA3536;"> {updateDocNum} </strong> 条`, { updateDocNum: this.updateDocNum })
      },
      typeFilters () {
        return [
          {
            value: this.$t('新建'),
            text: this.$t('新建')
          },
          {
            value: this.$t('覆盖'),
            text: this.$t('覆盖')
          }
        ]
      }
    },

    watch: {
      selectOperateType (value, oldVal) {
        if (!value.length) {
          this.selectedResourceDocs = []
          this.selectedResource = []
          if (!this.selectedResourceDocsCopy.length && !this.selectedResourceCopy.length) {
            this.originResourceList.forEach(item => {
              this.$refs.groupTableRef && this.$refs.groupTableRef.toggleRowSelection(item, false)
            })
          } else {
            if (oldVal.join('') === 'merge') {
              this.originResourceList.filter(e => e.typeText === '覆盖').forEach(item => {
                this.$refs.groupTableRef && this.$refs.groupTableRef.toggleRowSelection(item, false)
                this.filterCopyData(item.name)
              })
            } else {
              this.originResourceList.filter(e => e.typeText === '新建').forEach(item => {
                this.$refs.groupTableRef && this.$refs.groupTableRef.toggleRowSelection(item, false)
                this.filterCopyData(item.name)
              })
            }
          }
        }

        if (value.join('') === 'merge') {
          if (this.selectTypeValue === 'merge') {
            this.originResourceList.filter(e => e.typeText === '覆盖').forEach(item => {
              this.$refs.groupTableRef && this.$refs.groupTableRef.toggleRowSelection(item, true)
              this.selectedResourceDocs.push({
                language: this.language,
                resource_name: item.name,
                resource_doc_id: item.resource_doc_id
              })

              this.selectedResource.push({
                name: item.name,
                id: item.id,
                typeText: item.typeText,
                resource_doc_id: item.resource_doc_id
              })
            })
          }
          if (!this.selectTypeValue) {
            const data = this.originResourceList.filter(e => !!e.id)
            this.selectedResourceDocs = []
            this.selectedResource = []
            this.originResourceList.filter(e => e.typeText === '新建').forEach(item => {
              this.$refs.groupTableRef && this.$refs.groupTableRef.toggleRowSelection(item, false)
              this.filterCopyData(item.name)
            })

            // this.originResourceList.filter(e => e.typeText === '覆盖').forEach(item => {
            //     this.selectedResourceDocs.push({
            //         language: this.language,
            //         resource_name: item.name,
            //         resource_doc_id: item.resource_doc_id
            //     })

            //     this.selectedResource.push({
            //         name: item.name,
            //         id: item.id,
            //         typeText: item.typeText
            //     })
            // })
            this.handChangeData(data)
          }
        }

        if (value.join('') === 'create') {
          if (this.selectTypeValue === 'create') {
            this.originResourceList.filter(e => e.typeText === '新建').forEach(item => {
              this.$refs.groupTableRef && this.$refs.groupTableRef.toggleRowSelection(item, true)
              this.selectedResourceDocs.push({
                language: this.language,
                resource_name: item.name,
                resource_doc_id: item.resource_doc_id
              })

              this.selectedResource.push({
                name: item.name,
                id: item.id,
                typeText: item.typeText,
                resource_doc_id: item.resource_doc_id
              })
            })
          }
          if (!this.selectTypeValue) {
            const data = this.originResourceList.filter(e => !e.id)
            this.selectedResourceDocs = []
            this.selectedResource = []
            this.originResourceList.filter(e => e.typeText === '覆盖').forEach(item => {
              this.$refs.groupTableRef && this.$refs.groupTableRef.toggleRowSelection(item, false)
              this.filterCopyData(item.name)
            })
            this.handChangeData(data)
          }
        }

        if (value.length === 2) {
          this.selectedResourceDocs = []
          this.selectedResource = []
          let data = this.originResourceList
          let dataSelect = this.originResourceList
          if (this.selectTypeValue === 'merge') {
            data = this.originResourceList.filter(e => !!e.id)
            dataSelect = this.deDuplication([...this.originResourceList.filter(e => !!e.id), ...this.selectedResourceCopyT], 'name')
          } else if (this.selectTypeValue === 'create') {
            data = this.originResourceList.filter(e => !e.id)
            dataSelect = this.deDuplication([...this.originResourceList.filter(e => !e.id), ...this.selectedResourceCopyT], 'name')
          }
          data.forEach(item => {
            // const data = this.curPageData.find(e => e.name === item.name)
            this.$refs.groupTableRef && this.$refs.groupTableRef.toggleRowSelection(item, true)
          })
          dataSelect.forEach(item => {
            this.selectedResourceDocs.push({
              language: this.language,
              resource_name: item.name,
              resource_doc_id: item.resource_doc_id
            })
            
            this.selectedResource.push({
              name: item.name,
              id: item.id,
              typeText: item.typeText,
              resource_doc_id: item.resource_doc_id
            })
          })

          this.selectedResourceDocsCopyT = this.deDuplication([...this.selectedResourceDocs, ...this.selectedResourceDocsCopy], 'resource_name')
          this.selectedResourceCopyT = this.deDuplication([...this.selectedResource, ...this.selectedResourceCopy], 'name')
        }

        this.selectedResourceDocs = this.deDuplication([...this.selectedResourceDocs, ...this.selectedResourceDocsCopy], 'resource_name')
        this.selectedResource = this.deDuplication([...this.selectedResource, ...this.selectedResourceCopy], 'name')
      },
      path (value) {
        if (!value) {
          this.originResourceList = [...this.curPageData]
          this.resourceList = this.originResourceList
          this.selectedResourceDocs = []
          this.selectedResource = []
          this.$nextTick(() => {
            this.handChangeData(this.originResourceList)
          })
        }
      }
    },

    mounted () {
      const winHeight = window.innerHeight
      const offsetTop = 300
      this.exampleConf.height = winHeight - 52
      if ((winHeight - offsetTop) > this.yamlViewerHeight) {
        this.yamlViewerHeight = winHeight - offsetTop
      }
      this.$store.commit('setMainContentLoading', false)
    },

    methods: {

      goBack () {
        const self = this
        if (this.resource.content) {
          this.$bkInfo({
            title: this.$t('确定要放弃资源导入？'),
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

      async handleImportResource () {
        if (this.isDataLoading) {
          return false
        }

        if (!this.selectedResourceDocs.length) {
          this.$bkMessage({
            theme: 'error',
            message: this.$t('请确认勾选资源')
          })
          return false
        }

        this.isDataLoading = true
        try {
          const apigwId = this.apigwId
          let params = this.resource
          params.selected_resources = this.selectedResource
          const res = await this.$store.dispatch('resource/importResource', { apigwId, params })
          // 需要导入文档
          if (res.code === 0 && this.showDoc) {
            params = {
              selected_resource_docs: this.selectedResourceDocs,
              swagger: this.resource.content
            }
            await this.$store.dispatch('resource/importSwagger', { apigwId, params })
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
          if (this.showDoc) {
            params.resource_doc_language = this.language
          }
          const res = await this.$store.dispatch('resource/checkResourceImport', { apigwId, params })
          res.data.forEach(item => {
            if (item.id) {
              item.typeText = this.$t('覆盖')
            } else {
              item.typeText = this.$t('新建')
            }
          })

          this.curView = 'resources'
          this.content = this.resource.content
          this.resourceList = res.data
          this.originResourceList = res.data
          this.curPageData = res.data
          this.updateTableEmptyConfig()
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
        this.selectedResource = []
        this.$nextTick(() => {
          this.originResourceList.forEach(item => {
            this.selectOperateType.forEach(e => {
              if (this.typeFiltersEmums[e] === item.typeText) {
                this.$refs.groupTableRef && this.$refs.groupTableRef.toggleRowSelection(item, true)
                this.selectedResourceDocs.push({
                  language: this.language,
                  resource_name: item.name,
                  resource_doc_id: item.resource_doc_id
                })
    
                this.selectedResource.push({
                  name: item.name,
                  id: item.id,
                  typeText: item.typeText,
                  resource_doc_id: item.resource_doc_id
                })
              }
            })
          })
          this.selectedResourceDocsCopy = [...this.selectedResourceDocs]
          this.selectedResourceCopy = [...this.selectedResource]
          this.selectedResourceDocsCopyT = [...this.selectedResourceDocs]
          this.selectedResourceCopyT = [...this.selectedResource]
        })
      },

      handChangeData (data) {
        if (!!data && data.length) {
          data.forEach(item => {
            this.selectedResourceCopyT.forEach(e => {
              if (e.name === item.name) {
                this.$refs.groupTableRef && this.$refs.groupTableRef.toggleRowSelection(item, true)
                this.selectedResourceDocs.push({
                  language: this.language,
                  resource_name: item.name,
                  resource_doc_id: item.resource_doc_id
                })
        
                this.selectedResource.push({
                  name: item.name,
                  id: item.id,
                  typeText: item.typeText,
                  resource_doc_id: item.resource_doc_id
                })
              }
            })
          })
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
          this.originResourceList = this.curPageData.filter(item => filters.type.includes(item.typeText))
          this.resourceList = this.originResourceList
        } else if (filters.docType && filters.docType.length) {
          if (filters.docType.join('') === '新建') {
            this.originResourceList = this.curPageData.filter(item => !item.resource_doc_id)
          } else {
            this.originResourceList = this.curPageData.filter(item => !!item.resource_doc_id)
          }
          this.resourceList = this.originResourceList
        } else {
          this.originResourceList = [...this.curPageData]
          this.resourceList = this.originResourceList
        }
        this.updateTableEmptyConfig()
        // this.handlSelectData()
        this.$nextTick(() => {
          this.selectedResourceCopyT = this.deDuplication([...this.selectedResource, ...this.selectedResourceCopy], 'name')
          this.selectedResourceDocs = []
          this.selectedResource = []
          this.handChangeData(this.curPageData)
        })
      },

      handlViewerFocus () {
        this.$refs.bodyCodeViewer.$ace.focus()
      },
            
      handlerChange (payload, row) {
        payload = this.deDuplication(payload, 'name')
        this.selectedResourceDocs = [...payload].reduce((prev, item) => {
          prev.push({
            language: this.language,
            resource_name: item.name,
            resource_doc_id: item.resource_doc_id
          })
          return prev
        }, [])

        this.selectedResource = [...payload].reduce((prev, item) => {
          prev.push({
            name: item.name,
            id: item.id,
            typeText: item.typeText,
            resource_doc_id: item.resource_doc_id
          })
          return prev
        }, [])

        this.selectedResourceDocsCopy = [...this.selectedResourceDocs]
        this.selectedResourceCopy = [...this.selectedResource]
        this.selectedResourceDocsCopyT = [...this.selectedResourceDocs]
        this.selectedResourceCopyT = [...this.selectedResource]
      },
      handlerChangeAll (payload, row) {
        if (!payload.length) {
          this.selectOperateType = []
          this.selectedResourceDocsCopy = []
          this.selectedResourceCopy = []
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
          if (!map.has(item[k])) {
            map.set(item[k], item)
          }
        }
        return [...map.values()]
      },
      filterCopyData (name) {
        this.selectedResourceDocsCopy = this.selectedResourceDocsCopy.filter(e => e.resource_name !== name)
        this.selectedResourceCopy = this.selectedResourceCopy.filter(e => e.name !== name)
      },
      filterData () {
        this.selectedResourceCopyT = this.deDuplication([...this.selectedResource, ...this.selectedResourceCopy], 'name')
        this.selectedResourceDocs = []
        this.selectedResource = []
        this.originResourceList = this.curPageData.filter(e => e.path.includes(this.path))
        this.resourceList = this.originResourceList
        this.$nextTick(() => {
          this.handChangeData(this.curPageData)
        })
      },
      clearFilterKey () {
        this.path = ''
        this.$refs.groupTableRef.clearFilter()
        if (this.$refs.groupTableRef && this.$refs.groupTableRef.$refs.tableHeader) {
          clearFilter(this.$refs.groupTableRef.$refs.tableHeader)
        }
      },
      updateTableEmptyConfig () {
        const isFilter = isTableFilter(this.filterList)
        if (this.path || isFilter) {
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
    .app-content{
        min-width: 1350px;
    }
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
        color: #EA3536;
    }
    .import-container {
        position: relative;
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
    .ag-radio-header{
        width: auto;
        margin: 0 32px 0 0;
        display: flex;
        align-items: center;
    }

    .ag-checkbox-header{
        width: auto;
        margin: 0 32px 0 0;
        line-height: 32px;
    }

    .ag-table-header{
        height: 32px;
        line-height: 32px;
        color: #63656E;
    }

    .resource-table-container{
        overflow-y: scroll;
        max-height: 70vh;
        margin-top: 15px;
        position: relative;
    }
    .resource-doc-wrapper {
        .bk-table::before,
        .bk-table::after {
            width: 0;
            height: 0;
            z-index: 0;
        }
        .resource-table-wrapper::before {
            position: absolute;
            left: 0px;
            bottom: 0;
            width: 100%;
            height: 1px;
            content: "";
            background-color: #dfe0e5;
            z-index: 1;
        }
        .resource-table-wrapper::after {
            position: absolute;
            top: 0;
            right: 0;
            width: 1px;
            height: 100%;
            content: "";
            background-color: #dfe0e5;
            z-index: 9;
        }
    }
</style>
