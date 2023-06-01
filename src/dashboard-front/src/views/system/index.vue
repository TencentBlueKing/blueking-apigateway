<template>
  <div class="app-content">
    <div class="ag-top-header">
      <bk-alert type="info" :title="$t('请将新系统的接口，直接接入 API 网关')"></bk-alert>
      <!-- 新建系統接口，直接接入 API 网关 -->
      <!-- <bk-button theme="primary" @click="handleCreateSys"> {{ $t('新建系统') }} </bk-button> -->
      <div class="mt10" style="overflow: hidden;">
        <bk-input
          class="fr"
          :clearable="true"
          v-model="keyword"
          :placeholder="$t('请输入系统名称、描述，按Enter搜索')"
          :right-icon="'bk-icon icon-search'"
          style="width: 370px;"
          @enter="handleSearch">
        </bk-input>
      </div>
    </div>
    <bk-table
      ref="systemRef"
      style="margin-top: 15px;"
      :data="systemList"
      size="small"
      :pagination="pagination"
      ext-cls="ag-stage-table"
      v-bkloading="{ isLoading, opacity: 1 }"
      @page-limit-change="handlePageLimitChange"
      @page-change="handlePageChange"
      @filter-change="handleFilterChange">
      <div slot="empty">
        <table-empty
          :keyword="tableEmptyConf.keyword"
          :abnormal="tableEmptyConf.isAbnormal"
          @reacquire="getSystemList(true)"
          @clear-filter="clearFilterKey"
        />
      </div>
      <bk-table-column :label="$t('名称')">
        <template slot-scope="{ row }">
          {{ row.name }}
          <template v-if="row.is_official">
            <span class="official"> {{ $t('官方') }} </span>
          </template>
        </template>
      </bk-table-column>
      <bk-table-column :label="$t('描述')" prop="description" :show-overflow-tooltip="true">
        <template slot-scope="props">
          <template v-if="props.row.description">
            <span>{{props.row.description}}</span>
          </template>
          <template v-else>
            --
          </template>
        </template>
      </bk-table-column>
      <bk-table-column :label="$t('系统负责人')" :show-overflow-tooltip="true" :render-header="$renderHeader">
        <template slot-scope="props">
          <template v-if="props.row.maintainers.length > 0">
            <span>{{props.row.maintainers.join('；')}}</span>
          </template>
          <template v-else>
            --
          </template>
        </template>
      </bk-table-column>
      <bk-table-column
        :label="$t('文档分类')"
        column-key="doc_category"
        prop="doc_category_id"
        :render-header="$renderHeader"
        :filters="classifyFilters"
        :filter-method="classifyFilterMethod"
        :filter-multiple="true">
        <template slot-scope="props">
          {{props.row.doc_category_name}}
        </template>
      </bk-table-column>
      <bk-table-column :label="$t('操作')" width="150">
        <template slot-scope="{ row }">
          <bk-button
            class="mr10"
            text
            theme="primary"
            @click="handleEditSys(row)">
            {{ $t('编辑') }}
          </bk-button>
          <bk-button
            text
            theme="primary"
            :disabled="row.is_official"
            @click="handleDeleteSys(row)">
            <template v-if="row.is_official">
              <span v-bk-tooltips="$t('官方系统，不可删除')"> {{ $t('删除') }} </span>
            </template>
            <template v-else>
              {{ $t('删除') }}
            </template>
          </bk-button>
        </template>
      </bk-table-column>
    </bk-table>

    <bk-dialog
      width="540"
      v-model="deleteDialogConf.visiable"
      :title="deleteDialogTitle"
      :theme="'primary'"
      header-position="center"
      :mask-close="false"
      @after-leave="handleAfterLeave">
      <div>
        <div class="ft13" style="margin: 8px 0;" v-html="systemDelTips"></div>
        <bk-input v-model="formRemoveConfirmCode" />
        <div class="mt10 ft13">
          {{ $t('注意：删除系统，将删除该系统下所有组件API') }}， <strong> {{ $t('不可恢复') }} </strong>
        </div>
      </div>
      <template slot="footer">
        <bk-button
          theme="primary"
          :loading="deleteDialogConf.loading"
          :disabled="formRemoveConfirmCode !== curSystem.name"
          @click="handleDeleteSystem">
          {{ $t('确定') }}
        </bk-button>
        <bk-button theme="default" @click="deleteDialogConf.visiable = false"> {{ $t('取消') }} </bk-button>
      </template>
    </bk-dialog>

    <bk-sideslider
      :is-show.sync="isSliderShow"
      :width="750"
      :title="sliderTitle"
      @hidden="handleHidden"
      :quick-close="true"
      :before-close="handleBeforeClose">
      <div slot="content" style="padding: 20px;" v-bkloading="{ isLoading: detailLoading, opacity: 1 }">
        <bk-form :label-width="160" :rules="rules" ref="form" :model="formData" v-show="!detailLoading">
          <bk-form-item :label="$t('名称')" :required="true" property="name">
            <bk-input v-model="formData.name" :placeholder="$t('由英文字母、下划线(_)或数字组成，并且以字母开头，长度小于64个字符')" :disabled="isDisabled"></bk-input>
            <p class="tips" slot="tip"><i class="apigateway-icon icon-ag-info"></i> {{ $t('系统唯一标识') }} </p>
          </bk-form-item>
          <bk-form-item :label="$t('描述')" :required="true" property="description">
            <bk-input :disabled="isDisabled" :maxlength="128" v-model="formData.description" :placeholder="$t('不超过128个字符')"></bk-input>
          </bk-form-item>
          <bk-form-item :label="$t('文档分类')" :required="true" property="doc_category_id">
            <template v-if="isDisabled">
              <bk-input v-model="curSystem.doc_category_name" disabled></bk-input>
            </template>
            <bk-select
              v-else
              :loading="categoryLoading"
              searchable
              :clearable="false"
              v-model="formData.doc_category_id">
              <bk-option v-for="option in categoryList"
                :key="option.id"
                :id="option.id"
                :name="option.name">
              </bk-option>
              <div slot="extension" style="cursor: pointer;" @click="handleCreateCategory">
                <i class="bk-icon icon-plus-circle"></i>
                <span style="margin-left: 4px;"> {{ $t('新建文档分类') }} </span>
              </div>
            </bk-select>
          </bk-form-item>
          <bk-form-item :label="$t('系统负责人')">
            <user v-model="formData.maintainers" ref="userRef"></user>
          </bk-form-item>
          <bk-form-item :label="$t('超时时长')">
            <bk-input type="number" :max="600" :min="1" :precision="0" v-model="formData.timeout">
              <section class="timeout-append" slot="append">
                <div>{{$t('秒')}}</div>
              </section>
            </bk-input>
            <p class="tips" slot="tip"><i class="apigateway-icon icon-ag-info"></i> {{ $t('未设置时，使用默认值30秒，最大600秒') }} </p>
          </bk-form-item>
          <bk-form-item :label="$t('备注')">
            <bk-input type="textarea" :disabled="isDisabled" v-model="formData.comment" :placeholder="$t('请输入备注')"></bk-input>
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
      v-model="docuCategoryDialog.visible"
      :title="$t('新建文档分类')"
      :header-position="docuCategoryDialog.headerPosition"
      :width="docuCategoryDialog.width"
      :mask-close="false"
      @after-leave="docuCategoryDialog.categoryName = ''">
      <div class="category-label" style="margin-bottom: 5px;"> {{ $t('分类名称') }} </div>
      <bk-input v-model="docuCategoryDialog.categoryName" @input.native.stop style="margin-bottom: 15px;"></bk-input>
      <div slot="footer">
        <bk-button
          :disabled="docuCategoryDialog.categoryName === ''"
          theme="primary"
          :loading="docuCategoryDialog.loading"
          @click="handleConfirm"> {{ $t('确定') }} </bk-button>
        <bk-button style="margin-left: 6px;" @click="docuCategoryDialog.visible = false"> {{ $t('取消') }} </bk-button>
      </div>
    </bk-dialog>
  </div>
</template>

<script>
  import { catchErrorHandler, clearFilter } from '@/common/util'
  import User from '@/components/user'
  import sidebarMixin from '@/mixins/sidebar-mixin'

  const getDefaultData = () => {
    return {
      name: '',
      description: '',
      comment: '',
      maintainers: [],
      timeout: '',
      doc_category_id: ''
    }
  }

  export default {
    name: '',
    components: {
      User
    },
    mixins: [sidebarMixin],
    data () {
      return {
        keyword: '',
        systemList: [],
        pagination: {
          current: 1,
          count: 0,
          limit: 10
        },
        stageDialogConf: {
          isLoading: false,
          visiable: false,
          title: this.$t('新建标签')
        },
        curSystem: {},
        deleteDialogConf: {
          visiable: false,
          loading: false
        },
        isSliderShow: false,
        formData: getDefaultData(),
        categoryList: [],
        submitLoading: false,
        categoryLoading: false,
        allData: [],
        displayData: [],
        classifyFilters: [],
        isLoading: false,
        formRemoveConfirmCode: '',
        docuCategoryDialog: {
          visible: false,
          width: 480,
          headerPosition: 'left',
          categoryName: ''
        },
        detailLoading: false,
        tableEmptyConf: {
          keyword: '',
          isAbnormal: false
        },
        filterDocCategory: []
      }
    },
    computed: {
      isEdit () {
        return Object.keys(this.curSystem).length > 0
      },
      isDisabled () {
        return this.curSystem.is_official
      },
      sliderTitle () {
        return this.isEdit ? this.$t('编辑系统') : this.$t('新建系统')
      },
      systemDelTips () {
        return this.$t(`请完整输入 <code class="system-del-tips">{name}</code> 来确认删除系统！`, { name: this.curSystem.name })
      },
      deleteDialogTitle () {
        return this.$t(`确认删除系统【{name}】？`, { name: this.curSystem.name })
      }
    },
    watch: {
      keyword (newVal, oldVal) {
        if (oldVal && !newVal && this.isFilter) {
          this.isFilter = false
          this.pagination.current = 1
          this.pagination.limit = 10
          this.displayData = this.allData
          this.pagination.count = this.displayData.length
          this.systemList = this.getDataByPage()
        }
      }
    },
    created () {
      this.init()
      this.isFilter = false
      this.rules = {
        name: [
          {
            required: true,
            message: this.$t('必填项'),
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
        doc_category_id: [
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
      },

      handleCreateCategory () {
        this.docuCategoryDialog.visible = true
      },

      async handleConfirm () {
        this.docuCategoryDialog.loading = true
        try {
          const res = await this.$store.dispatch('category/addCategory', {
            name: this.docuCategoryDialog.categoryName
          })
          this.categoryList.push({
            id: res.data.id,
            name: this.docuCategoryDialog.categoryName
          })
          this.formData.doc_category_id = res.data.id
          this.docuCategoryDialog.visible = false
        } catch (e) {
          catchErrorHandler(e, this)
        } finally {
          this.docuCategoryDialog.loading = false
        }
      },

      handleHidden () {
        this.curSystem = {}
        this.categoryList = []
        this.formData = Object.assign({}, getDefaultData())
      },

      handleAfterLeave () {
        this.curSystem = {}
        this.formRemoveConfirmCode = ''
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
          try {
            const methods = this.isEdit ? 'updateSystem' : 'addSystem'
            const params = this.isEdit ? {
              systemId: this.curSystem.id,
              data: tempData
            } : tempData
            await this.$store.dispatch(`system/${methods}`, params)
            this.isSliderShow = false
            this.getSystemList(true)
          } catch (e) {
            catchErrorHandler(e, this)
          } finally {
            this.submitLoading = false
          }
        }, async validator => {
          console.error(validator)
        })
      },

      classifyFilterMethod (value, row, column) {
        const property = column.property
        return row[property] === value
      },

      handleFilterChange (filters) {
        this.filterDocCategory = filters.doc_category || []
        this.updateTableEmptyConfig()
      },

      async getCategories () {
        this.categoryLoading = true
        try {
          const res = await this.$store.dispatch('category/getCategories')
          this.categoryList = res.data
        } catch (e) {
          catchErrorHandler(e, this)
        } finally {
          this.categoryLoading = false
        }
      },

      async getSystemList (isLoading = false) {
        this.isLoading = isLoading
        try {
          const res = await this.$store.dispatch('system/getSystems')
          this.allData = Object.freeze(res.data)
          this.displayData = res.data
          this.allData.forEach(item => {
            if (!this.classifyFilters.map(subItem => subItem.value).includes(item.doc_category_id)) {
              this.classifyFilters.push({
                text: item.doc_category_name,
                value: item.doc_category_id
              })
            }
          })
          this.pagination.count = this.displayData.length
          this.systemList = this.getDataByPage()
          this.tableEmptyConf.isAbnormal = false
        } catch (e) {
          this.tableEmptyConf.isAbnormal = true
          catchErrorHandler(e, this)
        } finally {
          if (!isLoading) {
            this.$store.commit('setMainContentLoading', false)
          }
          this.isLoading = false
        }
      },

      handlePageLimitChange (limit) {
        this.pagination.limit = limit
        this.pagination.current = 1
        this.handlePageChange(this.pagination.current)
      },

      handlePageChange (page) {
        this.pagination.current = page
        const data = this.getDataByPage(page)
        this.systemList.splice(0, this.systemList.length, ...data)
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

      async handleCreateSys () {
        this.curSystem = {}
        this.formData.timeout = 30
        this.isSliderShow = true
        await this.getCategories()
        this.initSidebarFormData(this.formData)
      },

      async handleDeleteSystem () {
        this.deleteDialogConf.loading = true
        try {
          await this.$store.dispatch('system/deleteSystem', { systemId: this.curSystem.id })
          this.deleteDialogConf.visiable = false
          this.$bkMessage({
            limit: 1,
            theme: 'success',
            message: this.$t('删除成功！')
          })
          this.getSystemList(true)
        } catch (e) {
          catchErrorHandler(e, this)
        } finally {
          this.deleteDialogConf.loading = false
        }
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
          return item.name.match(reg) || item.description.match(reg)
        })
        this.pagination.count = this.displayData.length
        this.systemList = this.getDataByPage()
      },

      async handleEditSys (data) {
        this.curSystem = data
        this.isSliderShow = true
        this.getCategories()
        this.detailLoading = true
        try {
          const res = await this.$store.dispatch('system/getSystemDetail', { systemId: this.curSystem.id })
          const { name, description, maintainers, comment, timeout } = res.data
          this.formData.name = name
          this.formData.description = description
          this.formData.maintainers = [...maintainers]
          this.formData.doc_category_id = data.doc_category_id
          this.formData.comment = comment
          this.formData.timeout = timeout || ''
          this.$nextTick(() => {
            this.initSidebarFormData(this.formData)
          })
        } catch (e) {
          catchErrorHandler(e, this)
        } finally {
          this.detailLoading = false
        }
      },

      handleDeleteSys (data) {
        this.curSystem = data
        this.deleteDialogConf.visiable = true
      },

      clearFilterKey () {
        this.keyword = ''
        this.filterDocCategory = []
        this.$refs.systemRef.clearFilter()
        if (this.$refs.systemRef && this.$refs.systemRef.$refs.tableHeader) {
          clearFilter(this.$refs.systemRef.$refs.tableHeader)
        }
      },

      updateTableEmptyConfig () {
        if (this.keyword || this.filterDocCategory.length) {
          this.tableEmptyConf.keyword = 'placeholder'
          return
        }
        this.tableEmptyConf.keyword = ''
      },

      async handleBeforeClose () {
        this.$refs.userRef && this.$refs.userRef.handleBlur()
        return this.$isSidebarClosed(JSON.stringify(this.formData))
      }
    }
  }
</script>
<style lang="postcss" scoped>
    span.official {
        margin-left: 2px;
        padding: 2px;
        background:#dcffe2;
        font-size: 12px;
        color: #2dcb56;
    }

    .timeout-append {
        width: 54px;
        font-size: 12px;
        text-align: center;
        line-height: 30px;
    }

    code {
        padding: 0;
        padding-top: 0.2em;
        padding-bottom: 0.2em;
        margin: 0;
        color: #c7254e;
        font-size: 85%;
        background-color: rgba(0, 0, 0, 0.04);
        border-radius: 3px;
    }

    .ft13 {
        font-size: 13px;
    }

    .category-label {
        position: relative;
        margin-bottom: 5px;
        &::after {
            content: '*';
            margin-left: 2px;
            color: #ea3636;
        }
    }

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
</style>
<style>
    .system-del-tips {
        padding: 0;
        padding-top: 0.2em;
        padding-bottom: 0.2em;
        margin: 0;
        color: #c7254e;
        font-size: 85%;
        background-color: rgba(0, 0, 0, 0.04);
        border-radius: 3px;
    }
</style>
