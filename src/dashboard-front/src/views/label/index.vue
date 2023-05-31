<template>
  <div class="app-content">
    <div class="ag-top-header">
      <bk-button theme="primary" @click="handleShowDialog"> {{ $t('新建标签') }} </bk-button>
      <bk-input
        class="fr"
        :clearable="true"
        v-model="keyword"
        :placeholder="$t('请输入标签名，按Enter搜索')"
        :right-icon="'bk-icon icon-search'"
        style="width: 300px;"
        @enter="handleSearch">
      </bk-input>
    </div>
    <bk-table style="margin-top: 15px;"
      :data="labelList"
      :size="'small'"
      :pagination="pagination"
      v-bkloading="{ isLoading: isDataLoading }"
      @page-limit-change="handlePageLimitChange"
      @page-change="handlePageChange"
      @sort-change="handleSortChange">
      <div slot="empty">
        <table-empty
          :keyword="tableEmptyConf.keyword"
          :abnormal="tableEmptyConf.isAbnormal"
          @reacquire="getApigwLabels"
          @clear-filter="clearFilterKey"
        />
      </div>
      <bk-table-column :label="$t('名称')" prop="name" sortable column-key="name"></bk-table-column>
      <bk-table-column :label="$t('更新时间')" prop="updated_time" sortable column-key="updated_time" :render-header="$renderHeader"></bk-table-column>
      <bk-table-column :label="$t('操作')" width="200">
        <template slot-scope="props">
          <bk-button class="mr10" theme="primary" text @click="handleRename(props.row)"> {{ $t('重命名') }} </bk-button>
          <bk-button theme="primary" text @click="handleRemove(props.row)"> {{ $t('删除') }} </bk-button>
        </template>
      </bk-table-column>
    </bk-table>

    <bk-dialog
      v-model="labelDialogConf.visiable"
      theme="primary"
      :width="480"
      :mask-close="false"
      :header-position="'left'"
      :title="labelDialogConf.title"
      :loading="labelDialogConf.isLoading"
      @confirm="handleSubmitLabel"
      @cancel="handleCancel">
      <bk-form
        :label-width="200"
        form-type="vertical"
        :model="curLabel"
        :rules="rules"
        ref="labelForm">
        <bk-form-item :label="$t('标签名称')" :required="true" :property="'name'">
          <bk-input v-model="curLabel.name"></bk-input>
        </bk-form-item>
      </bk-form>
    </bk-dialog>
  </div>
</template>

<script>
  import { catchErrorHandler } from '@/common/util'

  export default {
    data () {
      return {
        keyword: '',
        orderBy: '',
        isPageLoading: true,
        isDataLoading: false,
        labelList: [
        ],
        pagination: {
          current: 1,
          count: 0,
          limit: 10
        },
        labelDialogConf: {
          isLoading: false,
          visiable: false,
          title: this.$t('新建标签')
        },
        curLabel: {
          name: ''
        },
        rules: {
          name: [
            {
              required: true,
              message: this.$t('必填项'),
              trigger: 'blur'
            },
            {
              max: 32,
              message: this.$t('不能多于32个字符'),
              trigger: 'change'
            }
          ]
        },
        tableEmptyConf: {
          keyword: '',
          isAbnormal: false
        }
      }
    },
    computed: {
      apigwId () {
        return this.$route.params.id
      },
      removeTitle () {
        return (data) => this.$t(`确定删除 【{DataName}】标签`, { DataName: data.name })
      }
    },
    watch: {
      keyword (newVal, oldVal) {
        if (oldVal && !newVal) {
          this.handleSearch()
        }
      },
      orderBy () {
        this.handleSearch()
      }
    },
    created () {
      this.init()
    },
    methods: {
      init () {
        this.getApigwLabels()
      },

      async getApigwLabels (page) {
        const apigwId = this.apigwId
        const curPage = page || this.pagination.current
        const pageParams = {
          limit: this.pagination.limit,
          offset: this.pagination.limit * (curPage - 1),
          name: this.keyword,
          order_by: this.orderBy
        }

        this.isDataLoading = true
        try {
          const res = await this.$store.dispatch('label/getApigwLabels', { apigwId, pageParams })
          res.data.results.forEach(item => {
            item.updated_time = item.updated_time || '--'
          })
          this.labelList = res.data.results
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

      handlePageLimitChange (limit) {
        this.pagination.limit = limit
        this.pagination.current = 1
        this.getApigwLabels(this.pagination.current)
      },

      handlePageChange (newPage) {
        this.pagination.current = newPage
        this.getApigwLabels(newPage)
      },

      handleShowDialog () {
        this.curLabel.name = ''
        this.curLabel.id = undefined
        this.labelDialogConf.title = this.$t('新建标签')
        this.labelDialogConf.visiable = true
      },

      handleSubmitLabel () {
        if (this.labelDialogConf.isLoading) {
          return false
        }
        this.labelDialogConf.isLoading = true
        this.$refs.labelForm.validate().then(() => {
          if (this.curLabel.id !== undefined) {
            this.updateLabel()
          } else {
            this.addLabel()
          }
        }).catch(() => {
          this.$nextTick(() => {
            this.labelDialogConf.isLoading = false
          })
        })
      },

      handleCancel () {
        this.clearLabelForm()
      },

      clearLabelForm () {
        this.curLabel.name = ''
        delete this.curLabel.id
        this.$refs.labelForm.formItems.forEach(item => {
          item.validator = {
            state: '',
            content: ''
          }
        })
      },

      async addLabel () {
        try {
          const data = { name: this.curLabel.name }
          const apigwId = this.apigwId
          await this.$store.dispatch('label/addApigwLabel', { apigwId, data })
          this.labelDialogConf.visiable = false
          this.clearLabelForm()

          this.pagination.current = 1
          this.getApigwLabels()
          this.$bkMessage({
            theme: 'success',
            message: this.$t('新建成功！')
          })
        } catch (e) {
          catchErrorHandler(e, this)
        } finally {
          this.labelDialogConf.isLoading = false
        }
      },

      async updateLabel () {
        try {
          const data = { name: this.curLabel.name }
          const apigwId = this.apigwId
          const labelId = this.curLabel.id
          await this.$store.dispatch('label/updateApigwLabel', { apigwId, labelId, data })
          this.labelDialogConf.visiable = false
          this.clearLabelForm()

          this.pagination.current = 1
          this.getApigwLabels()

          this.$bkMessage({
            theme: 'success',
            message: this.$t('更新成功！')
          })
        } catch (e) {
          catchErrorHandler(e, this)
        } finally {
          this.labelDialogConf.isLoading = false
        }
      },

      async removeLabel () {
        try {
          const apigwId = this.apigwId
          const labelId = this.curLabel.id
          await this.$store.dispatch('label/deleteApigwLabel', { apigwId, labelId })
          // 当前页只有一条数据
          if (this.labelList.length === 1 && this.pagination.current > 1) {
            this.pagination.current--
          }
          this.getApigwLabels()

          this.$bkMessage({
            theme: 'success',
            message: this.$t('删除成功！')
          })
        } catch (e) {
          catchErrorHandler(e, this)
        }
      },

      handleSearch (event) {
        this.pagination.current = 1
        this.pagination.count = 0
        this.getApigwLabels()
      },

      handleRename (data) {
        this.curLabel = JSON.parse(JSON.stringify(data))
        this.labelDialogConf.title = this.$t('重命名标签')
        this.labelDialogConf.visiable = true
      },

      handleRemove (data) {
        const self = this

        this.curLabel = data
        this.$bkInfo({
          width: 600,
          title: this.removeTitle(data),
          subTitle: this.$t('删除标签，将直接删除该标签与其它数据的关联关系，影响按该标签展示文档等功能，请确认是否删除？'),
          confirmFn () {
            self.removeLabel()
          }
        })
      },

      handleSortChange (params) {
        if (params.prop === 'name') {
          if (params.order === 'descending') {
            this.orderBy = '-name'
          } else if (params.order === 'ascending') {
            this.orderBy = 'name'
          } else {
            this.orderBy = ''
          }
        }

        if (params.prop === 'updated_time') {
          if (params.order === 'descending') {
            this.orderBy = '-updated_time'
          } else if (params.order === 'ascending') {
            this.orderBy = 'updated_time'
          } else {
            this.orderBy = ''
          }
        }
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
    @import '@/css/variable.css';

    .ag-dl {
        padding: 15px 40px 5px 30px;
    }
    
    .ag-user-type {
        width: 560px;
        height: 80px;
        background: #FAFBFD;
        border-radius: 2px;
        border: 1px solid #DCDEE5;
        padding: 17px 20px 0 20px;
        position: relative;
        overflow: hidden;

        .apigateway-icon {
            font-size: 80px;
            position: absolute;
            color: #ECF2FC;
            top: 15px;
            right: 20px;
            z-index: 0;
        }

        strong {
            font-size: 14px;
            margin-bottom: 10px;
            line-height: 1;
            display: block;
        }

        p {
            font-size: 12px;
            color: #63656E;
        }
    }
</style>
