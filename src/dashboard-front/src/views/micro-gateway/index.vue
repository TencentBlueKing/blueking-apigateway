<template>
  <div class="app-content">
    <!-- <bk-alert type="info" title="当前网关的托管方式为专享实例，需要创建微网关实例，并将其与环境绑定" closable></bk-alert> -->
    <div class="ag-top-header">
      <bk-button theme="primary" @click="handleCreateMicro"> {{ $t('新建') }} </bk-button>
      <bk-input
        class="fr"
        :clearable="true"
        v-model="keyword"
        :placeholder="$t('请输入名称，按Enter搜索')"
        :right-icon="'bk-icon icon-search'"
        style="width: 240px;"
        @enter="handleSearch">
      </bk-input>
    </div>
    <bk-table style="margin-top: 15px;"
      :data="microList"
      :size="'small'"
      :pagination="pagination"
      v-bkloading="{ isLoading: isDataLoading }"
      :ext-cls="'ag-resources-table'"
      @row-mouse-enter="columnHoverEnter"
      @row-mouse-leave="columnHoverLeave"
      @page-limit-change="handlePageLimitChange"
      @page-change="handlePageChange">
      <div slot="empty">
        <table-empty
          :keyword="tableEmptyConf.keyword"
          :abnormal="tableEmptyConf.isAbnormal"
          @reacquire="getMicroApigwList"
          @clear-filter="clearFilterKey"
        />
      </div>
      <bk-table-column :label="$t('实例ID')" prop="id">
        <template slot-scope="props">
          <template>
            <div style="display: flex;">
              <span class="ag-auto-text">
                {{props.row.id}}
              </span>
              <!-- <span v-bk-tooltips.top="{ content: $t('复制') , disabled: changeCopyIconID !== props.row.id }" v-show="!switchIcon === true && changeCopyIconID === props.row.id" :zIndex="999999" class="top-middle">
                                <i class="apigateway-icon icon-ag-copy-info copy-btn" style="margin-left: 20px;" :class="{ 'copyCursor': isCursor }" @click="handleCopy(props.row.id)" @mouseover="isCursorFun"></i>
                            </span> -->
              <span :title="$t('复制')" v-show="changeCopyIconID === props.row.id" :z-index="999999" style="position: relative;z-index: 99;">
                <i class="apigateway-icon icon-ag-copy-info copy-btn" style="margin-left: 20px;" :class="{ 'copyCursor': isCursor }" @click="handleCopy(props.row.id)" @mouseover="isCursorFun"></i>
              </span>
            </div>
          </template>
        </template>
      </bk-table-column>
      <bk-table-column :label="$t('名称')" prop="name" :show-overflow-tooltip="true">
        <template slot-scope="props">
          <template v-if="props.row.name">
            <span class="ag-auto-text">
              {{props.row.name}}
            </span>
          </template>
          <template v-else>
            --
          </template>
        </template>
      </bk-table-column>
      <bk-table-column :label="$t('Release名称')" prop="release_name" :show-overflow-tooltip="true" :render-header="$renderHeader">
        <template slot-scope="props">
          <template v-if="props.row.release_name">
            <span class="ag-auto-text">
              {{props.row.release_name}}
            </span>
          </template>
          <template v-else>
            --
          </template>
        </template>
      </bk-table-column>
      <bk-table-column :label="$t('绑定环境')" prop="stage_name" :show-overflow-tooltip="true" :render-header="$renderHeader">
        <template slot-scope="props">
          <template v-if="props.row.stage_name">
            <span class="ag-auto-text">
              {{props.row.stage_name}}
            </span>
          </template>
          <template v-else>
            --
          </template>
        </template>
      </bk-table-column>
      <bk-table-column :label="$t('实例状态')" prop="status" :show-overflow-tooltip="true" sortable :render-header="$renderHeader">
        <template slot-scope="props">
          <template>
            <span v-bk-tooltips.top="{ content: props.row.comment, disabled: changeCopyIconID !== props.row.id }" class="top-middle">
              <bk-spin size="mini" v-if="props.row.status === 'releasing'"></bk-spin>
              <span v-else-if="props.row.status === 'failure'" class="ag-ouline-dot error mr10"></span>
              <span v-else-if="props.row.status === 'success'" class="ag-ouline-dot success mr10"></span>
              <span v-else class="ag-ouline-dot mr10"></span>
            </span>
            <span>{{getStatusText(props.row.status)}}</span>
          </template>
        </template>
      </bk-table-column>
      <bk-table-column width="180" :label="$t('微网关版本')" prop="chart_version"></bk-table-column>
      <bk-table-column width="300" :label="$t('更新时间')" prop="updated_time" sortable></bk-table-column>
      <bk-table-column :label="$t('操作')" width="150" class="ag-action" :show-overflow-tooltip="false">
        <template slot-scope="props">
          <bk-button
            class="mr10"
            text
            theme="primary"
            @click="handleEditMicro(props.row)">
            {{ $t('编辑') }}
          </bk-button>
          <bk-button
            class="mr10"
            text
            theme="primary"
            @click="handleDeleteMicro(props.row)">
            {{ $t('删除') }}
          </bk-button>
        </template>
      </bk-table-column>
    </bk-table>

    <bk-dialog v-model="deleteDialogConf.visiable"
      theme="primary"
      :width="525"
      :title="`${$t('确定要删除实例')}【${curStage.name}】？`"
      :mask-close="true"
      @cancel="deleteDialogConf.visiable = false"
      @confirm="removeMicro">
      <p class="tc p10"> {{ $t('实例删除后，将删除该实例相关配置，不可恢复，请确认删除') }} </p>
    </bk-dialog>
  </div>
</template>

<script>
  import { catchErrorHandler } from '@/common/util'

  export default {
    data () {
      return {
        keyword: '',
        isPageLoading: true,
        isDataLoading: false,
        microList: [],
        pagination: {
          current: 1,
          count: 0,
          limit: 10
        },
        curStage: {
          name: ''
        },
        deleteDialogConf: {
          visiable: false
        },
        changeCopyIconID: '',
        switchIcon: false,
        isCursor: false,
        tableEmptyConf: {
          keyword: '',
          isAbnormal: false
        }
      }
    },
    computed: {
      apigwId () {
        return this.$route.params.id
      }
    },
    watch: {
      keyword (newVal, oldVal) {
        if (oldVal && !newVal) {
          this.handleSearch()
        }
      }
    },
    created () {
      this.init()
    },
    methods: {
      init () {
        this.getMicroApigwList()
      },

      async getMicroApigwList (page) {
        const apigwId = this.apigwId
        const curPage = page || this.pagination.current
        const pageParams = {
          limit: this.pagination.limit,
          offset: this.pagination.limit * (curPage - 1),
          name: this.keyword
        }

        this.isDataLoading = true
        try {
          const res = await this.$store.dispatch('microGateway/getMicroApigwList', { apigwId, pageParams })
          res.data.results.forEach(item => {
            item.release_time = item.release_time || '--'
            item.resource_version_name = item.resource_version_name || '--'
          })
          this.microList = res.data.results
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
        this.getMicroApigwList(this.pagination.current)
      },

      handlePageChange (newPage) {
        this.pagination.current = newPage
        this.getMicroApigwList(newPage)
      },

      handleCreateMicro () {
        this.$router.push({
          name: 'createMicroGateway'
        })
      },

      async removeMicro () {
        try {
          const apigwId = this.apigwId
          const id = this.curStage.id
          await this.$store.dispatch('microGateway/deleteMicrogateway', { apigwId, id })
          // 当前页只有一条数据
          if (this.microList.length === 1 && this.pagination.current > 1) {
            this.pagination.current--
          }
          this.$bkMessage({
            theme: 'success',
            message: this.$t('删除成功！')
          })
          this.getMicroApigwList()
        } catch (e) {
          catchErrorHandler(e, this)
          this.$bkMessage({
            theme: 'error',
            message: this.$t('删除失败！')
          })
        }
      },

      handleSearch (event) {
        this.getMicroApigwList()
      },

      handleEditMicro (data) {
        this.$router.push({
          name: 'createMicroGateway',
          query: {
            MicroId: data.id
          }
        })
      },

      handleDeleteMicro (data) {
        // if (!data.deletable) {
        //     return false
        // }

        this.curStage = data
        this.deleteDialogConf.visiable = true
      },

      columnHoverEnter (index, row, event) {
        this.switchIcon = false
        this.changeCopyIconID = event.id
      },
            
      columnHoverLeave () {
        this.switchIcon = true
        this.changeCopyIconID = ''
      },

      handleCopy (text) {
        this.$copyText(text).then((e) => {
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

      getStatusText (key) {
        const status = { installed: this.$t('已安装'), abnormal: this.$t('安装异常'), pending: this.$t('待安装'), installing: this.$t('安装中') }
        return status[key]
      },

      isCursorFun () {
        this.isCursor = true
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

    .icon-ag-copy-info {
        line-height: 19px;
        color: #3A84FF;
    }

    .error {
        border: 2px solid #ec4444;
        background: #ffe6e6;
    }

    .success {
        background: #e5f6ea;
    }

    .bk-alert-info {
        margin-bottom: 16px;
    }
    .copyCursor {
        cursor : pointer;
    }
</style>
