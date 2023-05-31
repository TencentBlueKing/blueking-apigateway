<template>
  <div class="app-content">
    <div class="ag-top-header">
      <!-- 新建文档分类操作 -->
      <!-- <bk-button theme="primary" @click="handleCreate"> {{ $t('新建文档分类') }} </bk-button> -->
      <bk-input
        class="fr"
        :clearable="true"
        v-model="keyword"
        :placeholder="$t('请输入文档分类名称，按Enter搜索')"
        :right-icon="'bk-icon icon-search'"
        style="width: 240px;"
        @enter="handleSearch">
      </bk-input>
    </div>
    <bk-table
      style="margin-top: 15px;"
      :data="docCategoryList"
      size="small"
      :pagination="pagination"
      ext-cls="ag-stage-table"
      v-bkloading="{ isLoading, opacity: 1 }"
      @page-limit-change="handlePageLimitChange"
      @page-change="handlePageChange">
      <div slot="empty">
        <table-empty
          :keyword="tableEmptyConf.keyword"
          :abnormal="tableEmptyConf.isAbnormal"
          @reacquire="getDocCategoryList(true)"
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
      <bk-table-column :label="$t('优先级')" prop="priority" :show-overflow-tooltip="true">
        <template slot-scope="props">
          <template v-if="props.row.priority">
            <span>{{props.row.priority}}</span>
          </template>
          <template v-else>
            --
          </template>
        </template>
      </bk-table-column>
      <bk-table-column :label="$t('关联系统数量')" :show-overflow-tooltip="true" :render-header="$renderHeader">
        <template slot-scope="props">
          {{props.row.system_count}}
        </template>
      </bk-table-column>
      <bk-table-column
        :label="$t('更新时间')"
        :render-header="$renderHeader"
        prop="updated_time">
        <template slot-scope="props">
          {{props.row.updated_time}}
        </template>
      </bk-table-column>
      <bk-table-column :label="$t('操作')" width="150">
        <template slot-scope="{ row }">
          <bk-button
            class="mr10"
            text
            theme="primary"
            @click="handleEdit(row)">
            {{ $t('编辑') }}
          </bk-button>
          <bk-button
            class="mr10"
            text
            theme="primary"
            :disabled="row.is_official || row.system_count !== 0"
            @click="handleDelete(row)">
            <template v-if="row.is_official">
              <span v-bk-tooltips="$t('官方文档分类，不可删除')"> {{ $t('删除') }} </span>
            </template>
            <template v-else-if="row.system_count !== 0">
              <span v-bk-tooltips="$t('存在关联系统，不可删除')"> {{ $t('删除') }} </span>
            </template>
            <template v-else>
              {{ $t('删除') }}
            </template>
          </bk-button>
        </template>
      </bk-table-column>
    </bk-table>

    <bk-dialog
      width="400"
      v-model="deleteDialogConf.visiable"
      header-position="left"
      :title="`${$t('确认删除')}`"
      :theme="'primary'"
      :loading="deleteDialogConf.loading"
      :mask-close="true"
      @confirm="handleDeleteDocCategory">
      <p class="tc"> {{ $t('确定要删除文档分类') }}【 {{curDocCategory.name}} 】? </p>
    </bk-dialog>

    <bk-dialog
      v-model="docCategoryDialog.visiable"
      :title="docCategoryDialog.title"
      :header-position="docCategoryDialog.headerPosition"
      :loading="docCategoryDialog.loading"
      :width="docCategoryDialog.width"
      :mask-close="false"
      @after-leave="docCategoryDialog.categoryName = ''"
      @confirm="handleConfirm"
      @cancel="closeDocCategoryDialog">
      <bk-form :label-width="90" :model="docCategoryDialog" :rules="rules" ref="validateForm" form-type="vertical">
        <bk-form-item :label="$t('名称')" :required="true" :property="'name'">
          <bk-input v-model="docCategoryDialog.name" :placeholder="$t('请输入分类名称')" :disabled="curDocCategory.is_official"></bk-input>
        </bk-form-item>
        <bk-form-item :label="$t('优先级')" :required="true" :property="'priority'">
          <bk-input v-model="docCategoryDialog.priority" :placeholder="$t('请输入优先级，范围1 - 9999')" type="number" :max="9999" :min="1" :show-controls="true"></bk-input>
          <p class="ag-tip mt10">
            <i class="apigateway-icon icon-ag-info"></i> {{ $t('文档展示时，将按照优先级从大到小排序') }}
          </p>
        </bk-form-item>
      </bk-form>
    </bk-dialog>
  </div>
</template>

<script>
  import { catchErrorHandler } from '@/common/util'

  export default {
    name: '',
    data () {
      return {
        keyword: '',
        docCategoryList: [],
        pagination: {
          current: 1,
          count: 0,
          limit: 10
        },
        curDocCategory: {},
        deleteDialogConf: {
          visiable: false,
          loading: false
        },
        allData: [],
        displayData: [],
        classifyFilters: [],
        isLoading: false,
        formRemoveConfirmCode: '',
        docCategoryDialog: {
          visiable: false,
          width: 480,
          headerPosition: 'left',
          id: 0,
          name: '',
          priority: 1000,
          title: '',
          loading: false
        },
        detailLoading: false,
        tableEmptyConf: {
          keyword: '',
          isAbnormal: false
        },
        rules: {
          name: [
            {
              required: true,
              message: this.$t('必填项'),
              trigger: 'blur'
            }
          ],
          priority: [
            {
              required: true,
              message: this.$t('必填项'),
              trigger: 'blur'
            }
          ]
        }
      }
    },
    computed: {
      isEdit () {
        return Object.keys(this.curDocCategory).length > 0
      },
      isDisabled () {
        return this.curDocCategory.is_official
      },
      sliderTitle () {
        return this.isEdit ? this.$t('编辑文档分类') : this.$t('新建文档分类')
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
          this.docCategoryList = this.getDataByPage()
        }
      }
    },
    created () {
      this.init()
    },
    methods: {
      init () {
        this.getDocCategoryList()
      },

      async handleConfirm () {
        this.docCategoryDialog.loading = true

        this.$refs.validateForm.validate().then(() => {
          if (this.docCategoryDialog.id) {
            this.updateDocCategory()
          } else {
            this.createDocCategory()
          }
        }).catch(() => {
          this.$nextTick(() => {
            this.docCategoryDialog.loading = false
          })
        })
      },

      async createDocCategory () {
        try {
          await this.$store.dispatch('docCategory/addDocCategory', {
            name: this.docCategoryDialog.name,
            priority: this.docCategoryDialog.priority
          })
          this.getDocCategoryList(true)
          this.$bkMessage({
            limit: 1,
            theme: 'success',
            message: this.$t('新建成功！')
          })
          this.docCategoryDialog.visiable = false
        } catch (e) {
          catchErrorHandler(e, this)
        } finally {
          this.docCategoryDialog.loading = false
        }
      },

      async updateDocCategory () {
        try {
          await this.$store.dispatch('docCategory/updateDocCategory', {
            docCategoryId: this.docCategoryDialog.id,
            data: {
              name: this.docCategoryDialog.name,
              priority: this.docCategoryDialog.priority
            }
          })
          this.getDocCategoryList(true)
          this.$bkMessage({
            limit: 1,
            theme: 'success',
            message: this.$t('更新成功！')
          })
          this.docCategoryDialog.visiable = false
        } catch (e) {
          catchErrorHandler(e, this)
        } finally {
          this.docCategoryDialog.loading = false
        }
      },

      async getDocCategoryList (isLoading = false) {
        this.isLoading = isLoading
        try {
          const res = await this.$store.dispatch('docCategory/getDocCategorys')
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
          this.docCategoryList = this.getDataByPage()
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
        this.docCategoryList.splice(0, this.docCategoryList.length, ...data)
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

      handleCreate () {
        this.docCategoryDialog.title = this.$t('新建文档分类')
        this.curDocCategory = ''
        this.docCategoryDialog.id = 0
        this.docCategoryDialog.name = ''
        this.docCategoryDialog.priority = 1000
        this.docCategoryDialog.visiable = true
      },

      handleEdit (data) {
        this.curDocCategory = data
        this.docCategoryDialog.title = this.$t('编辑文档分类')
        this.docCategoryDialog.id = data.id
        this.docCategoryDialog.name = data.name
        this.docCategoryDialog.priority = data.priority
        this.docCategoryDialog.visiable = true
      },

      async handleDeleteDocCategory () {
        this.deleteDialogConf.loading = true
        try {
          await this.$store.dispatch('docCategory/deleteDocCategory', { docCategoryId: this.curDocCategory.id })
          this.deleteDialogConf.visiable = false
          this.$bkMessage({
            limit: 1,
            theme: 'success',
            message: this.$t('删除成功！')
          })
          this.getDocCategoryList(true)
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
          return item.name.match(reg)
        })
        this.pagination.count = this.displayData.length
        this.docCategoryList = this.getDataByPage()
      },

      handleDelete (data) {
        this.curDocCategory = data
        this.deleteDialogConf.visiable = true
      },

      closeDocCategoryDialog () {
        this.docCategoryDialog.visiable = false
        this.$refs.validateForm.clearError()
      },

      clearFilterKey () {
        this.keyword = ''
      },

      updateTableEmptyConfig () {
        this.tableEmptyConf.keyword = this.keyword
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
        width: 36px;
        font-size: 12px;
        text-align: center;
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
