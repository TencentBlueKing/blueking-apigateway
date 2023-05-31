<template>
  <loader
    :is-loading="mainContentLoading"
    :delay="1000"
    class="apigw-wrapper"
    :background-color="'#FAFBFD'"
    :loader="'table-loader'"
    :height="600"
    :offset-left="0"
    :has-border="false">
    <div class="top-header top-wrapper">
      <bk-input
        v-model="keyword"
        style="width: 500px;"
        :placeholder="$t('请输入网关名称或描述')"
        :right-icon="'bk-icon icon-search'"
        :clearable="true">
      </bk-input>

      <bk-button @click="handleGoApigw" theme="primary" class="fr" v-if="GLOBAL_CONFIG.APIGW"> {{ $t('网关管理') }} </bk-button>
    </div>

    <bk-table style="margin-top: 15px;"
      ref="gatewayRef"
      :data="curPageData"
      :size="'small'"
      :key="renderKey"
      :pagination="pagination"
      @filter-change="handleFilterChange"
      @page-limit-change="handlePageLimitChange"
      @page-change="handlePageChange">
      <div slot="empty">
        <table-empty
          :keyword="tableEmptyConf.keyword"
          :abnormal="tableEmptyConf.isAbnormal"
          @reacquire="getApigwAPI"
          @clear-filter="clearFilterKey"
        />
      </div>
      <bk-table-column :label="$t('网关名称')" prop="name" :show-overflow-tooltip="true" :render-header="columnRenderHeader">
        <template slot-scope="props">
          <router-link style="color: #3A84FF;" :to="{ name: 'apigwAPIDetailIntro', params: { apigwId: props.row.name } }">{{props.row.name || '--'}}</router-link>
          <span class="ag-tag success ml5" v-if="props.row.name_prefix === '[官方]'"> {{ $t('官方') }} </span>
        </template>
      </bk-table-column>
      <bk-table-column :label="$t('网关描述')" prop="description" :show-overflow-tooltip="true" :render-header="columnRenderHeader">
        <template slot-scope="props">
          {{props.row.description || '--'}}
        </template>
      </bk-table-column>
      <!-- <bk-table-column
                :label="$t('用户类型')"
                prop="type"
                column-key="user_auth_type"
                :filters="userFilters"
                :filter-multiple="true"
                v-if="userFilters.length"
                :render-header="columnRenderHeader">
                <template slot-scope="props">
                    {{props.row.user_auth_type_display || '--'}}
                </template>
            </bk-table-column>
            <bk-table-column
                :label="$t('用户类型')"
                prop="type"
                column-key="user_auth_type"
                :render-header="columnRenderHeader"
                v-else>
                <template slot-scope="props">
                    {{props.row.user_auth_type_display || '--'}}
                </template>
            </bk-table-column> -->
      <bk-table-column :label="$t('网关负责人')" prop="maintainers" :show-overflow-tooltip="true" :render-header="columnRenderHeader">
        <template slot-scope="props">
          {{props.row.maintainers.join(', ') || '--'}}
        </template>
      </bk-table-column>
    </bk-table>
  </loader>
</template>

<script>
  import { catchErrorHandler, clearFilter, renderHeader } from '@/common/util'
  import loader from '@/components/loader'

  export default {
    components: {
      loader
    },
    data () {
      return {
        renderKey: 0,
        pagination: {
          current: 1,
          count: 0,
          limit: 20
        },
        filterList: [],
        keyword: '',
        originApigwList: [],
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

        this.originApigwList.forEach(item => {
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
        if (endIndex > this.apigwList.length) {
          endIndex = this.apigwList.length
        }
        this.updateTableEmptyConfig()
        return this.apigwList.slice(startIndex, endIndex)
      },
      apigwList () {
        return this.originApigwList.filter(item => {
          const matchKeyword = (item.name || '').indexOf(this.keyword) > -1 || (item.description || '').indexOf(this.keyword) > -1
          const matchFilter = this.filterList.length ? this.filterList.includes(item['user_auth_type']) : true
          return matchKeyword && matchFilter
        })
      }
    },
    watch: {
      apigwList () {
        this.resetPagination()
      }
    },
    mounted () {
      this.init()
    },
    methods: {
      init () {
        this.getApigwAPI()
      },
      async getApigwAPI (page) {
        const curPage = page || this.pagination.current
        const pageParams = {
          limit: this.pagination.limit,
          offset: this.pagination.limit * (curPage - 1),
          name: this.keyword
        }

        this.isDataLoading = true
        this.$store.commit('setMainContentLoading', true)
        try {
          const { data: { results, count } } = await this.$store.dispatch('apigw/getApigwAPI', { pageParams })
          // this.apigwList = results
          this.originApigwList = results
          this.pagination.count = count
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

      resetPagination () {
        this.pagination.count = this.apigwList.length
        this.pagination.current = 1
      },

      handlePageLimitChange (limit) {
        this.pagination.limit = limit
        this.pagination.current = 1
      },

      handlePageChange (newPage) {
        this.pagination.current = newPage
      },

      handleFilterChange (filters) {
        this.filterList = filters['user_auth_type']
      },

      handleGoApigw () {
        window.open(this.GLOBAL_CONFIG.APIGW)
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
        this.$refs.gatewayRef.clearFilter()
        if (this.$refs.gatewayRef && this.$refs.gatewayRef.$refs.tableHeader) {
          clearFilter(this.$refs.gatewayRef.$refs.tableHeader)
        }
      }
    }
  }
</script>

<style lang="postcss" scoped>
    @import './index.css';
</style>
