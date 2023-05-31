<template>
  <div class="app-content apigw-access-manager-wrapper">
    <div class="wrapper">
      <bk-input
        class="fr"
        :clearable="true"
        v-model="pathUrl"
        :placeholder="$t('请输入组件名称、请求路径，按Enter搜索')"
        :right-icon="'bk-icon icon-search'"
        style="width: 328px; margin-bottom: 10px"
        @enter="filterData">
      </bk-input>
      <ag-loader
        :offset-top="0"
        :offset-left="0"
        loader="stage-loader"
        :is-loading="false">
        <bk-table
          ref="componentTableRef"
          style="margin-top: 16px;"
          :data="componentList"
          size="small"
          :pagination="pagination"
          v-bkloading="{ isLoading, opacity: 1 }"
          @page-change="handlePageChange"
          @page-limit-change="handlePageLimitChange"
          @filter-change="handleFilterChange">
          <div slot="empty">
            <table-empty
              :keyword="tableEmptyConf.keyword"
              :abnormal="tableEmptyConf.isAbnormal"
              @reacquire="getComponents(true)"
              @clear-filter="clearFilterKey"
            />
          </div>
          <bk-table-column :label="$t('系统名称')" prop="system_name" :render-header="$renderHeader">
            <template slot-scope="{ row }">
              {{row.system_name || '--'}}
            </template>
          </bk-table-column>
          <bk-table-column :label="$t('组件名称')" prop="component_name" :render-header="$renderHeader">
            <template slot-scope="{ row }">
              {{row.component_name || '--'}}
            </template>
          </bk-table-column>
          <bk-table-column :label="$t('组件请求方法')"
            :filters="methodFilters"
            :filter-multiple="false"
            :render-header="$renderHeader"
            column-key="component_method"
            prop="component_method">
            <template slot-scope="{ row }">
              {{row.component_method || '--'}}
            </template>
          </bk-table-column>
          <bk-table-column :label="$t('组件请求路径')" prop="component_path" :render-header="$renderHeader">
            <template slot-scope="{ row }">
              {{row.component_path || '--'}}
            </template>
          </bk-table-column>
          <bk-table-column :label="$t('资源ID')" prop="resource_id" :render-header="$renderHeader">
            <template slot-scope="{ row }">
              {{row.resource_id || '--'}}
            </template>
          </bk-table-column>
          <bk-table-column :label="$t('组件ID')" prop="component_id" :render-header="$renderHeader">
            <template slot-scope="{ row }">
              {{row.component_id || '--'}}
            </template>
          </bk-table-column>
          <bk-table-column :label="$t('权限级别')" width="150"
            :filters="levelFilters"
            :filter-multiple="false"
            :render-header="$renderHeader"
            column-key="component_permission_level"
            prop="component_permission_level">
            <template slot-scope="{ row }">
              {{levelEnum[row.component_permission_level] || '--'}}
            </template>
          </bk-table-column>
        </bk-table>
      </ag-loader>
    </div>
  </div>
</template>
<script>
  import { catchErrorHandler, clearFilter, isTableFilter } from '@/common/util'

  export default {
    name: '',
    components: {
    },
    data () {
      return {
        componentList: [],
        pagination: {
          current: 1,
          count: 0,
          limit: 10
        },
        requestQueue: ['component'],
        allData: [],
        displayData: [],
        isLoading: false,
        pathUrl: '',
        levelEnum: { 'unlimited': this.$t('无限制'), 'normal': this.$t('普通') },
        displayDataLocal: [],
        levelFilters: [{ value: 'unlimited', text: this.$t('无限制') }, { value: 'normal', text: this.$t('普通') }],
        tableEmptyConf: {
          keyword: '',
          isAbnormal: false
        },
        filterList: {}
      }
    },
    computed: {
      id () {
        return this.$route.query.id
      },
      methodFilters () {
        return this.$store.state.options.methodList.map(item => {
          return {
            value: item.id,
            text: item.id

          }
        })
      }
    },
    watch: {
      requestQueue (value) {
        if (value.length < 1) {
          this.$store.commit('setMainContentLoading', false)
        }
      },
      pathUrl (value) {
        if (!value) {
          this.displayData = this.displayDataLocal
          this.pagination.count = this.displayData.length
          this.componentList = this.getDataByPage()
        }
      }
    },
    created () {
      this.init()
      this.isFilter = false
    },
    methods: {
      init () {
        this.getComponents()
      },

      async getComponents (isLoading = false) {
        this.isLoading = isLoading
        try {
          const res = await this.$store.dispatch('component/getSyncVersion', {
            id: this.id
          })
          this.allData = Object.freeze(res.data)
          this.displayData = res.data
          this.displayDataLocal = res.data
          this.pagination.count = this.displayData.length
          this.componentList = this.getDataByPage()
          this.tableEmptyConf.isAbnormal = false
        } catch (e) {
          this.tableEmptyConf.isAbnormal = true
          catchErrorHandler(e, this)
        } finally {
          if (this.requestQueue.length > 0) {
            this.requestQueue.shift()
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
        this.componentList.splice(0, this.componentList.length, ...data)
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
      filterData () {
        this.displayData = this.displayDataLocal.filter(e => (e.component_path && e.component_path.includes(this.pathUrl)) || (e.component_name && e.component_name.includes(this.pathUrl)))
        this.componentList = this.getDataByPage()
        this.pagination.count = this.displayData.length
      },
      handleFilterChange (filters) {
        this.filterList = filters
        if (filters.component_method && filters.component_method.length) {
          this.displayData = this.displayDataLocal.filter(item => filters.component_method.includes(item.component_method))
          this.componentList = this.getDataByPage()
          this.pagination.count = this.displayData.length
        } else if (filters.component_permission_level && filters.component_permission_level.length) {
          this.displayData = this.displayDataLocal.filter(item => filters.component_permission_level[0] === item.component_permission_level)
          this.componentList = this.getDataByPage()
          this.pagination.count = this.displayData.length
        } else {
          this.getComponents()
        }
      },
      clearFilterKey () {
        this.pathUrl = ''
        this.$refs.componentTableRef.clearFilter()
        if (this.$refs.componentTableRef && this.$refs.componentTableRef.$refs.tableHeader) {
          clearFilter(this.$refs.componentTableRef.$refs.tableHeader)
        }
      },
      updateTableEmptyConfig () {
        const isFilter = isTableFilter(this.filterList)
        if (this.pathUrl || isFilter) {
          this.tableEmptyConf.keyword = 'placeholder'
          return
        }
        this.tableEmptyConf.keyword = ''
      }
    }
  }
</script>
<style lang="postcss" scoped>
    .apigw-access-manager-wrapper {
        display: flex;
        justify-content: flex-start;
        .wrapper {
            padding: 0 10px;
            width: 100%
        }
        .search-wrapper {
            display: flex;
            justify-content: space-between;
        }
        .bk-table {
            .api-name,
            .docu-link {
                max-width: 200px;
                display: inline-block;
                word-break: break-all;
                overflow: hidden;
                white-space: nowrap;
                text-overflow: ellipsis;
                vertical-align: bottom;
            }
            .copy-icon {
                font-size: 14px;
                cursor: pointer;
                &:hover {
                    color: #3a84ff;
                }
            }
        }
    }
    .apigw-access-manager-slider-cls {
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
        .timeout-append {
            width: 36px;
            font-size: 12px;
            text-align: center;
        }
    }

    .ag-flex {
        display: flex;
    }
    .ag-auto-text {
        vertical-align: middle;
    }
    .ag-tag.success {
        width: 44px;
    }
</style>
