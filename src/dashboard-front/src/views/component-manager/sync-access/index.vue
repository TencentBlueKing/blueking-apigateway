<template>
  <div class="app-content apigw-access-manager-wrapper">
    <div class="wrapper">
      <div class="f14 ag-table-header">
        <p>
          {{ $t('请确认以下组件对应网关资源的变更：') }}
          <span v-html="addInfo"></span>
          <span v-html="updateInfo"></span>
          <span v-html="deleteInfo"></span>
        </p>
        <bk-input
          :clearable="true"
          v-model="pathUrl"
          :placeholder="$t('请输入组件名称、请求路径，按Enter搜索')"
          :right-icon="'bk-icon icon-search'"
          style="width: 328px;"
          @enter="filterData">
        </bk-input>
      </div>
      <ag-loader
        :offset-top="0"
        :offset-left="0"
        loader="stage-loader"
        :is-loading="false">
        <bk-table
          ref="componentRef"
          style="margin-top: 16px;"
          :data="componentList"
          size="small"
          :pagination="pagination"
          v-bkloading="{ isLoading, opacity: 1 }"
          @select="handlerChange"
          @select-all="handlerAllChange"
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
            :filter-multiple="true"
            :render-header="$renderHeader"
            column-key="component_method"
            prop="component_method">
            <template slot-scope="{ row }">
              {{row.component_method || '--'}}
            </template>
          </bk-table-column>
          <bk-table-column :label="$t('组件请求路径')" prop="component_path" :min-width="200" :render-header="$renderHeader">
            <template slot-scope="{ row }">
              {{row.component_path || '--'}}
            </template>
          </bk-table-column>
          <bk-table-column :label="$t('资源')" prop="resource_id" :show-overflow-tooltip="false">
            <template slot-scope="{ row }">
              <span
                v-if="row.resource_name"
                :class="['text-resource', { 'resource-disabled': !row.resource_id }]"
                v-bk-tooltips.top="{ content: row.resource_id ? row.resource_name : $t('资源不存在') }"
                @click.stop="handleEditResource(row, row.resource_id)">{{ row.resource_name }}</span>
              <template v-else>
                --
              </template>
            </template>
          </bk-table-column>
          <bk-table-column :label="$t('组件ID')" prop="component_id" :render-header="$renderHeader">
            <template slot-scope="{ row }">
              {{row.component_id || '--'}}
            </template>
          </bk-table-column>
          <bk-table-column :label="$t('操作类型')" width="150"
            :filters="statusFilters"
            :filter-multiple="true"
            :render-header="$renderHeader"
            column-key="status"
            prop="status">
            <template slot-scope="{ row }">
              <span style="color: #2DCB56;" v-if="!row.resource_id"> {{ $t('新建') }} </span>
              <span style="color: #ffb400;" v-if="row.resource_id && row.component_path"> {{ $t('更新') }} </span>
              <span style="color: #EA3536;" v-if="row.resource_id && !row.component_path"> {{ $t('删除') }} </span>
            </template>
          </bk-table-column>
        </bk-table>

        <div class="mt20">
          <bk-popconfirm ref="resourcePopconfirm" trigger="click" ext-cls="import-resource-popconfirm-wrapper" v-if="componentList.length">
            <div slot="content">
              <div class="content-text"> {{ $t('将组件配置同步到网关 bk-esb，创建网关的资源版本并发布到网关所有环境') }} </div>
              <div class="btn-wrapper">
                <bk-button size="small" theme="primary" class="btn" :disabled="confirmIsLoading" @click="confirm"> {{ $t('确认') }} </bk-button>
                <bk-button size="small" class="btn" @click="$refs.resourcePopconfirm.cancel()"> {{ $t('取消') }} </bk-button>
              </div>
            </div>
            <bk-button
              class="mr10"
              theme="primary"
              type="button"
              :title="$t('下一步')"
              :loading="confirmIsLoading">
              {{ $t('确认同步') }}
            </bk-button>
          </bk-popconfirm>
          <bk-button
            v-else
            class="mr10"
            theme="primary"
            type="button"
            :disabled="true">
            {{ $t('确认同步') }}
          </bk-button>
          <!-- <bk-button
                        class="mr10"
                        theme="primary"
                        type="button"
                        title="下一步"
                        @click.stop.prevent="checkData" :loading="isDataLoading">
                        下一步
                    </bk-button> -->
          <bk-button
            theme="default"
            type="button"
            :title="$t('取消')"
            :disabled="isLoading"
            @click="goBack">
            {{ $t('取消') }}
          </bk-button>
        </div>
      </ag-loader>
    </div>
  </div>
</template>
<script>
  import { catchErrorHandler, clearFilter, isTableFilter } from '@/common/util'

  const getDefaultData = () => {
    return {
      system_id: '',
      name: '',
      description: '',
      method: '',
      path: '',
      component_codename: ``,
      permission_level: '',
      timeout: 30,
      is_active: true,
      config_fields: []
    }
  }

  export default {
    name: '',
    components: {
    },
    data () {
      return {
        searchValue: '',
        componentList: [],
        pagination: {
          current: 1,
          count: 0,
          limit: 10
        },
        formData: getDefaultData(),
        componentData: {},
        isSliderShow: false,
        methodList: [
          {
            id: 'GET',
            name: 'GET'
          },
          {
            id: 'POST',
            name: 'POST'
          },
          {
            id: 'PUT',
            name: 'PUT'
          },
          {
            id: 'PATCH',
            name: 'PATCH'
          },
          {
            id: 'DELETE',
            name: 'DELETE'
          },
          {
            id: '*',
            name: 'GET/POST'
          }
        ],
        levelList: [
          {
            id: 'unlimited',
            name: this.$t('无限制')
          },
          {
            id: 'normal',
            name: this.$t('普通')
          }
        ],
        requestQueue: ['component'],
        allData: [],
        displayData: [],
        submitLoading: false,
        isLoading: false,
        curSelectList: [],
        deleteDialogConf: {
          visiable: false,
          loading: false,
          ids: []
        },
        detailLoading: false,
        isReleasing: false,
        needNewVersion: false,
        versionMessage: '',
        pathUrl: '',
        displayDataLocal: [],
        statusFilters: [{ value: 'delete', text: this.$t('删除') }, { value: 'update', text: this.$t('更新') }, { value: 'create', text: this.$t('新建') }],
        esb: {},
        tableEmptyConf: {
          keyword: '',
          isAbnormal: false
        },
        filterList: {},
        isFilter: false
      }
    },
    computed: {
      createNum () {
        const results = this.allData.filter(item => !item.resource_id)
        return results.length
      },
      updateNum () {
        const results = this.allData.filter(item => item.resource_id && item.component_path)
        return results.length
      },
      deleteNum () {
        const results = this.allData.filter(item => item.resource_id && !item.component_path)
        return results.length
      },
      methodFilters () {
        return this.$store.state.options.methodList.map(item => {
          return {
            value: item.id,
            text: item.id

          }
        })
      },
      addInfo () {
        return this.$t(`新建 <strong style="color: #2DCB56;"> {createNum} </strong> 条，`, { createNum: this.createNum })
      },
      updateInfo () {
        return this.$t(`更新 <strong style="color: #ffb400;"> {updateNum} </strong> 条，`, { updateNum: this.updateNum })
      },
      deleteInfo () {
        return this.$t(`删除 <strong style="color: #EA3536;"> {deleteNum} </strong> 条`, { deleteNum: this.deleteNum })
      },
      confirmIsLoading () {
        return this.isLoading
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
          this.displayData = this.allData
          this.pagination.count = this.displayData.length
          this.componentList = this.getDataByPage()
        }
      }
    },
    created () {
      this.init()
    },
    methods: {
      init () {
        this.getComponents()
        this.getEsbGateway()
      },

      async getComponents (isLoading = false) {
        this.isLoading = isLoading
        try {
          const res = await this.$store.dispatch('component/checkSyncComponent')
          this.allData = Object.freeze(res.data)
          this.displayData = res.data
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

      handlerChange (payload) {
        this.curSelectList = [...payload]
      },

      handlerAllChange (payload) {
        this.curSelectList = [...payload]
      },

      handleSysSelect (value, option) {
        const tempList = this.formData.component_codename.split('.')
        let customStr = ''
        if (tempList.length === 3) {
          customStr = tempList[2]
        }
        this.formData.component_codename = `generic.${option.lowerName}.${customStr}`
        this.$refs.systemFilterRef.setSelected(value)
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
          if (tempData.method === '*') {
            tempData.method = ''
          }
          if (tempData.config_fields.length > 0) {
            tempData.config = this.$refs.configRef.getData()
            delete tempData.config_fields
          }
          if (!this.isEdit) {
            delete tempData.config_fields
          }
          try {
            const methods = this.isEdit ? 'updateComponent' : 'addComponent'
            const params = this.isEdit ? {
              id: this.componentData.id,
              data: tempData
            } : tempData
            await this.$store.dispatch(`component/${methods}`, params)
            this.isSliderShow = false
            this.getComponents(true)
          } catch (e) {
            catchErrorHandler(e, this)
          } finally {
            this.submitLoading = false
          }
        }, validator => {
          console.error(validator)
        })
      },

      confirm () {
        this.checkReleaseData()
        this.$refs.resourcePopconfirm.cancel()
      },

      async checkReleaseData () {
        try {
          await this.$store.dispatch('component/ayncReleaseData')
          this.$router.push({
            name: 'apigwAccess'
          })
        } catch (e) {
          catchErrorHandler(e, this)
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

      async handlesync () {
        try {
          const res = await this.$store.dispatch('component/getReleaseStatus')
          this.isReleasing = res.data.is_releasing
          if (this.isReleasing) {
            setTimeout(() => {
              this.isReleasing = false
            }, 3000)
          } else {
            this.handlesyncRouter()
          }
        } catch (e) {
          console.warn(e)
          return false
        }
      },

      handlesyncRouter () {
        this.$router.push({
          name: 'syncApigwAccess'
        })
      },
      goBack () {
        this.$router.push({
          name: 'apigwAccess'
        })
      },
      filterData () {
        this.displayData = this.allData.filter(e => (e.component_path && e.component_path.includes(this.pathUrl)) || (e.component_name && e.component_name.includes(this.pathUrl)))
        this.componentList = this.getDataByPage()
        this.pagination.count = this.displayData.length
      },

      handleFilterChange (filters) {
        this.filterList = filters
        if (filters.component_method && filters.component_method.length) {
          this.displayData = this.allData.filter(item => filters.component_method.includes(item.component_method))
          this.componentList = this.getDataByPage()
          this.pagination.count = this.displayData.length
        } else if (filters.status && filters.status.length) {
          const filterCriteria = filters.status
          const filterList = []
          // 过滤对应操作类型
          if (filterCriteria.includes('delete')) {
            filterList.push(...this.allData.filter(item => item.resource_id && !item.component_path))
          }
          if (filterCriteria.includes('create')) {
            filterList.push(...this.allData.filter(item => item.component_id && !item.resource_id))
          }
          if (filterCriteria.includes('update')) {
            filterList.push(...this.allData.filter(item => item.resource_id && item.component_path))
          }
          this.displayData = filterList
          this.componentList = this.getDataByPage()
          this.pagination.count = this.displayData.length
        } else {
          this.getComponents()
        }
      },

      async getEsbGateway () {
        try {
          const res = await this.$store.dispatch('system/getEsbGateway')
          this.esb = res.data
        } catch (e) {
          catchErrorHandler(e, this)
        }
      },

      handleEditResource (data, resourceId) {
        if (!resourceId) {
          return false
        }
        const routeData = this.$router.resolve({
          path: `/${this.esb.gateway_id}/resource/${data.resource_id}/edit`,
          params: {
            id: this.esb.gateway_id,
            resourceId: data.resource_id
          }
        })
        window.open(routeData.href, '_blank')
      },

      clearFilterKey () {
        this.pathUrl = ''
        this.$refs.componentRef.clearFilter()
        if (this.$refs.componentRef && this.$refs.componentRef.$refs.tableHeader) {
          clearFilter(this.$refs.componentRef.$refs.tableHeader)
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
        .ag-table-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
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

    .btn-wrapper {
        padding-top: 10px;
        .btn {
            &:nth-child(1) {
                right: 100px;
            }
            &:nth-child(2) {
                right: 35px;
            }
        }
        
    }

    .text-resource {
        color: #3a84ff;
        cursor: pointer;
    }

    .resource-disabled {
        color: #dcdee5;
        cursor: not-allowed;
        user-select: none;
    }
</style>
