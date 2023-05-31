<template>
  <div class="app-content">
    <div class="ag-top-header">
      <p :class="['version-title', localLanguage === 'en' ? 'title-mr' : '']">：{{curVersion.version}} ({{curVersion.title}})</p>
      <bk-input
        class="mr10"
        :clearable="true"
        v-model="keyword"
        :placeholder="$t('请输入请求路径，按Enter搜索')"
        :right-icon="'bk-icon icon-search'"
        style="width: 350px;"
        @enter="handleSearch">
      </bk-input>
      <div class="header-meta">
        <span> {{ $t('生成时间：') }} </span>{{curVersion.created_time}}
        <span class="ml40"> {{ $t('创建者：') }} </span>{{curVersion.created_by}}
      </div>
    </div>
    <bk-table
      :data="curPageData"
      :pagination="pagination"
      size="small"
      @page-limit-change="handlePageLimitChange"
      @page-change="handlePageChange"
      @row-click="handleRowClick">
      <div slot="empty">
        <table-empty
          :keyword="tableEmptyConf.keyword"
          :abnormal="tableEmptyConf.isAbnormal"
          @reacquire="getVersionDetail"
          @clear-filter="clearFilterKey"
        />
      </div>
      <bk-table-column :label="$t('请求路径')" prop="path" :render-header="$renderHeader">
        <template slot-scope="props">
          <a href="javascript: void(0);" class="ag-text-link ag-auto-text" v-bk-tooltips.right="props.row.path" @click.stop.prevent="handleShowResourceDetail(props.row)">{{props.row.path}}</a>
        </template>
      </bk-table-column>
      <bk-table-column :label="$t('请求方法')" prop="method" :render-header="$renderHeader"></bk-table-column>
      <bk-table-column :label="$t('名称')" prop="name">
        <template slot-scope="props">
          {{props.row.name || '--'}}
        </template>
      </bk-table-column>
      <bk-table-column :label="$t('描述')">
        <template slot-scope="props">
          <span class="ag-auto-text" v-bk-tooltips.right="props.row.description">{{props.row.description || '--'}}</span>
        </template>
      </bk-table-column>
    </bk-table>

    <bk-sideslider
      :is-show.sync="detailSidesliderConf.isShow"
      :title="detailSidesliderConf.title"
      :quick-close="true"
      :width="720">
      <div slot="content" class="pt10 pl30 pr30 pb30" v-bkloading="{ isLoading: isDetailLoading, opacity: 1 }" style="min-height: 250px;">
        <resource-detail :cur-resource="curResource" v-if="!isDetailLoading"></resource-detail>
      </div>
    </bk-sideslider>
  </div>
</template>

<script>
  import { catchErrorHandler, sortByKey } from '@/common/util'
  import ResourceDetail from '@/components/resource-detail'

  export default {
    components: {
      ResourceDetail
    },
    data () {
      return {
        isPageLoading: true,
        isDetailLoading: false,
        pagination: {
          current: 1,
          count: 0,
          limit: 10
        },
        allResourceList: [],
        resourceList: [],
        curPageData: [],
        curVersion: {
          name: '',
          title: ''
        },
        detailSidesliderConf: {
          isShow: false
        },
        keyword: '',
        curResource: {
          name: '',
          disabled_stages: [],
          config: {},
          proxy: {
            type: '',
            config: {
              transform_headers: {
                add: []
              }
            }
          },
          useDefaultTimeout: true,
          useDefaultHeader: true,
          useDefaultHost: true,
          contexts: {
            resource_auth: {
              config: {}
            }
          }
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
      localLanguage () {
        return this.$store.state.localLanguage
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
        this.getVersionDetail()
      },

      goBack () {
        this.$router.push({
          name: 'apigwVersion',
          params: {
            id: this.apigwId
          }
        })
      },

      handleSearch () {
        this.pagination.current = 1
        if (this.keyword) {
          this.resourceList = this.allResourceList.filter(item => {
            return item.path.indexOf(this.keyword) !== -1
          })
        } else {
          this.resourceList = [...this.allResourceList]
        }
        this.initPageConf()
        this.getCurPageData()
      },

      async getVersionDetail () {
        try {
          this.isPageLoading = true
          const apigwId = this.apigwId
          const versionId = this.$route.params.versionId
          const res = await this.$store.dispatch('version/getApigwVersionDetail', { apigwId, versionId })
          const sortList = sortByKey(res.data.data, 'path')
          this.curVersion = res.data
          this.allResourceList = [...sortList]
          this.resourceList = [...sortList]
          this.initPageConf()
          this.getCurPageData()
          this.tableEmptyConf.isAbnormal = false
        } catch (e) {
          this.tableEmptyConf.isAbnormal = true
          catchErrorHandler(e, this)
        } finally {
          this.isPageLoading = false
          this.$store.commit('setMainContentLoading', false)
        }
      },

      initPageConf () {
        this.pagination.count = this.resourceList.length
        this.pagination.current = 1
      },

      getCurPageData () {
        const offset = this.pagination.limit * (this.pagination.current - 1)
        this.curPageData = [...this.resourceList].splice(offset, this.pagination.limit)
        this.updateTableEmptyConfig()
      },

      handlePageLimitChange (limit) {
        this.pagination.limit = limit
        this.pagination.current = 1
        this.getCurPageData()
      },

      handlePageChange (page) {
        this.pagination.current = page
        this.getCurPageData()
      },

      handleRowClick (row) {
        this.handleShowResourceDetail(row)
      },

      handleShowResourceDetail (params) {
        this.isDetailLoading = true
        this.detailSidesliderConf.isShow = true
        this.detailSidesliderConf.title = this.$t('资源详情')
        this.curResource = params
        setTimeout(() => {
          this.isDetailLoading = false
        }, 1000)
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

    .version-title {
        position: absolute;
        left: 53px;
        top: -61px;
        color: #313238;
    }

    .title-mr {
        margin-left: 24px;
    }

    .header-meta {
        font-size: 14px;
        color: #313238;
        position: absolute;
        right: 0;
        top: -61px;

        span {
            color: #979BA5;
        }
    }

    .ag-tab-button {
        cursor: default;
        &:hover {
            border-color: #c4c6cc;
            color: #63656e;
        }
        &.is-selected {
            border-color: #3a84ff !important;
            color: #3a84ff !important;
        }
    }

    .button-diff {
        .ag-tab-button {
            &.is-selected {
                border-color: red !important;
                color: red !important;
            }
        }
    }
</style>
