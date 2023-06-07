<template>
  <div>
    <bk-button
      class="mr10"
      @click="handleBatchRemovePolicy">
      {{ $t('批量删除') }}
    </bk-button>
    <bk-button
      class="mr10"
      @click="handleAddResource">
      {{ $t('添加') }}
    </bk-button>
    <!-- 按蓝鲸应用ID 资源名称搜索 -->
    <!-- <bk-input
            class="fr"
            :clearable="true"
            v-model="keyword"
            :placeholder="$t('搜索')"
            :right-icon="'bk-icon icon-search'"
            style="width: 300px;"
            @enter="handlerSearch">
        </bk-input> -->
    <bk-search-select
      class="fr"
      style="width: 500px;"
      :placeholder="$t('搜索')"
      :show-popover-tag-change="true"
      :clearable="true"
      :data="searchResourceCondition"
      :show-condition="false"
      v-model="searchFilters"
      @change="formatFilterData"
      @clear="clearSearchFilters">
    </bk-search-select>
    <bk-table
      :data="pagingList"
      :size="'small'"
      :max-height="600"
      :pagination="pagination"
      style="margin-top: 15px;"
      v-bkloading="{ isLoading: isTableLoading }"
      @header-dragend="dragendColumn"
      @row-click="tableRowClick"
      @page-change="handlePageChange"
      @page-limit-change="handlePageLimitChange"
      @selection-change="handleResourceSelect">
      <div slot="empty">
        <table-empty
          :keyword="tableEmptyConf.keyword"
          @clear-filter="clearFilterKey"
        />
      </div>
      <bk-table-column align="center" width="40">
        <template slot-scope="{ row }">
          <div :class="['play-shape', row.isIconView ? 'icon-view' : 'icon-conceal']" v-if="row.dimension !== 'api'">
            <i class="bk-icon icon-play-shape"></i>
          </div>
        </template>
      </bk-table-column>
      <bk-table-column type="selection" width="60" align="center"></bk-table-column>
      <bk-table-column :label="$t('蓝鲸应用ID')" prop="bk_app_code" :render-header="$renderHeader"></bk-table-column>
      <bk-table-column
        :label="$t('类型')"
        prop="dimension">
        <template slot-scope="{ row }">
          <template v-if="row.dimension === 'api'">
            {{ $t('全部资源') }}
          </template>
          <template v-if="row.dimension === 'resource'">
            {{ $t('具体资源') }}
          </template>
        </template>
      </bk-table-column>
      <bk-table-column :label="$t('资源')" prop="resource_ids" :show-overflow-tooltip="false">
        <template slot-scope="{ row }">
          <template v-if="row.dimension === 'api'">
            *
          </template>
          <template v-else>
            <template v-if="row.resource_ids && row.resource_ids.length && !row.isIconView">
              <bk-popover placement="top" :ext-cls="'aaaaaa'">
                <div class="parent" :style="{ 'height': row.rowHeight }">
                  <!-- 设置宽度 -->
                  <div class="column-wrapper" :style="{ width: eleTargetWidth + 'px' }">
                    <span v-for="(item, index) in formattedData(row.resource_ids)" :key="item.id">
                      {{ item.name }}<span v-if="!(index === row.resource_ids.length - 1)">,</span>
                    </span>
                  </div>
                </div>
                <div slot="content" style="white-space: normal;">
                  <p v-for="item in formattedData(row.resource_ids)" :key="item.id">
                    {{ item.name }}
                  </p>
                </div>
              </bk-popover>
            </template>
            <template v-else-if="row.isIconView">
              <div class="parent" :style="{ 'height': row.rowHeight }">
                <div>
                  <span v-for="item in formattedData(row.resource_ids)" :key="item.id" class="text-view">
                    {{ item.name }}
                  </span>
                </div>
              </div>
            </template>
            <template v-else>
              --
            </template>
          </template>
        </template>
      </bk-table-column>
      <bk-table-column :label="$t('操作')" :show-overflow-tooltip="false" width="120">
        <template slot-scope="props">
          <bk-button
            class="mr10"
            text
            theme="primary"
            @click.stop="handleEditResource(props.row)">
            {{ $t('编辑') }}
          </bk-button>
          <bk-popconfirm
            placement="top"
            @confirm="handlerDeletePolicy(props.row)">
            <bk-button
              class="mr10"
              text
              theme="primary">
              {{ $t('删除') }}
            </bk-button>
          </bk-popconfirm>
        </template>
      </bk-table-column>
    </bk-table>

    <bk-sideslider
      :title="resourceSliderConf.title"
      :width="800"
      :is-show.sync="resourceSliderConf.isShow"
      :quick-close="true"
      :before-close="handleBeforeClose"
      @hidden="sidesliderHidden">
      <div slot="content" class="p30">
        <bk-form :label-width="30" :model="curResource" :rules="rules" ref="validateForm1">
          <bk-form-item label="">
            <p class="top-tips">{{ $t('你将对指定的蓝鲸应用添加免用户认证白名单') }}</p>
          </bk-form-item>
          <bk-form-item :label="$t('蓝鲸应用ID')" :required="true" :label-width="150" :property="'bkAppCode'" :rules="rules.bkAppCode" :error-display-type="'normal'">
            <bk-input :placeholder="$t('请输入应用ID')" v-model="curResource.bkAppCode" :disabled="resourceSliderConf.type === 'edit'"></bk-input>
          </bk-form-item>
          <bk-form-item label="">
            <p class="top-tips">{{ $t('请选择要添加的资源') }}</p>
          </bk-form-item>
          <bk-form-item label="" :label-width="56">
            <bk-radio-group v-model="manner">
              <bk-radio value="api">
                {{ $t('全部资源') }}
                <i class="apigateway-icon icon-ag-info icon-class" v-bk-tooltips.right="$t('包括网关下所有资源，包括未来新创建的资源')"></i>
              </bk-radio>
              <br>
              <bk-radio value="resource" class="mt10">
                {{ $t('具体资源') }}
                <i class="apigateway-icon icon-ag-info icon-class" v-bk-tooltips.right="$t('仅包含当前选择的资源')"></i>
              </bk-radio>
            </bk-radio-group>
          </bk-form-item>
          <bk-form-item label="" v-if="manner === 'resource'">
            <div class="white-transfer-wrapper">
              <bk-transfer
                ext-cls="resource-transfer-wrapper"
                :target-list="resourceTargetList"
                :source-list="resourceList"
                :display-key="'name'"
                :setting-key="'id'"
                :title="[$t('未选资源'), $t('已选资源')]"
                :searchable="true"
                @change="handleResourceChange">
                <div
                  slot="source-option"
                  slot-scope="data"
                  class="transfer-source-item"
                  :title="data.name"
                >
                  {{ data.name }}
                </div>
                <div
                  slot="target-option"
                  slot-scope="data"
                  class="transfer-source-item"
                  :title="data.name"
                >
                  {{ data.name }}
                </div>
              </bk-transfer>
              <p class="tips-text">
                <i class="apigateway-icon icon-ag-info icon-class"></i>
                {{ $t('仅展示需要认证用户的资源') }}
              </p>
            </div>
          </bk-form-item>
          <bk-form-item label="">
            <bk-button theme="primary" class="mr10" :disabled="confirmLoading" @click="handleBindResource"> {{ $t('确定') }} </bk-button>
            <bk-button @click="handleHideResourceSlider"> {{ $t('取消') }} </bk-button>
          </bk-form-item>
        </bk-form>
      </div>
    </bk-sideslider>
  </div>
</template>

<script>
  import { catchErrorHandler } from '@/common/util'
  import jsYaml from 'js-yaml'
  import _ from 'lodash'
  import sidebarMixin from '@/mixins/sidebar-mixin'

  export default {
    name: 'WhitelistTable',
    mixins: [sidebarMixin],

    props: {
      yamlStr: {
        type: String,
        default: ''
      },
      type: {
        type: String,
        default: 'create'
      }
    },

    data () {
      return {
        keyword: '',
        dataList: [],
        pagingList: [],
        searchList: [],
        pagination: {
          current: 1,
          count: 0,
          limit: 10
        },
        whiteListPolicyList: [],
        resourceSliderConf: {
          isShow: false,
          type: 'add',
          title: this.$t('添加白名单')
        },
        // 已选择的数据
        resourceTargetList: [],
        // 数据源
        resourceList: [],
        resourceIds: [],
        manner: 'api',
        curResource: {
          bkAppCode: ''
        },
        isTableLoading: false,
        showResourceList: [],
        timer: null,
        confirmLoading: false,
        searchResourceCondition: [
          {
            name: this.$t('蓝鲸应用ID'),
            id: 'bk_app_code',
            children: []
          },
          {
            name: this.$t('资源名称'),
            id: 'resource_id',
            children: []
          }
        ],
        // 下拉显示的数据
        searchFilters: [],
        searchParams: {
          bk_app_code: '',
          resource_id: ''
        },
        eleTargetWidth: '150',
        rules: {
          bkAppCode: [
            {
              required: true,
              message: this.$t('必填项'),
              trigger: 'blur'
            },
            {
              regex: /^[a-z0-9][a-z0-9_-]{0,31}$/,
              message: this.$t('由小写字母、数字、连字符(-)组成，首字符必须是字母，长度小于 32 个字符'),
              trigger: 'blur'
            }
          ]
        },
        tableEmptyConf: {
          keyword: ''
        },
        sourceEl: null
      }
    },

    computed: {
      apigwId () {
        return this.$route.params.id
      },
      formattedData () {
        return (resourceIds) => {
          const list = this.resourceList.filter(item => {
            if (resourceIds.includes(item.id)) {
              return true
            }
          })
          return list.length ? list : '--'
        }
      },
      childListformattedData () {
        return (resourceId) => {
          return this.resourceList.filter(item => item.id === resourceId) || '--'
        }
      }
    },

    watch: {
      keyword (value) {
        if (value === '') {
          this.getTableData()
        }
      },
      searchFilters () {
        this.$nextTick(() => {
          this.searchParams.bk_app_code = ''
          this.searchParams.resource_id = ''
          this.searchFilters.forEach(item => {
            this.searchParams[item.id] = item.values[0].id
          })
        })
      },
      'searchParams.bk_app_code' (val) {
        this.pagination.current = 1
        this.pagination.count = 0
        this.getSearchDataList()
      },
      'searchParams.resource_id' (val) {
        this.pagination.current = 1
        this.pagination.count = 0
        this.getSearchDataList()
      }
    },

    created () {
      this.init()
      if (this.type === 'edit') {
        this.yamlConvertJson(this.yamlStr || '')
      }
    },

    mounted () {
      this.dragendColumn()
      this.getResourcesViewWidth()
    },

    methods: {
      init () {
        this.$nextTick(() => {
          this.getTableData()
        })
        this.getResources()
      },
            
      // 模糊搜索使用
      // 根据蓝鲸应用ID, 资源进行搜索
      handlerSearch () {
        if (this.keyword === '') {
          return false
        }
        if (this.timer) {
          clearTimeout(this.timer)
        }
        this.timer = setTimeout(() => {
          this.isTableLoading = true
          const searchList = this.dataList.filter(item => {
            if (item.bk_app_code.indexOf(this.keyword) !== -1) {
              return true
            }
            const list = this.resourceList.filter(resource => resource.name.indexOf(this.keyword) !== -1)
            if (list.length) {
              const r = list.filter(resourceItem => item.resource_ids.includes(resourceItem.id))
              if (r.length) {
                return true
              }
            }
          })
          this.pagingList = searchList
          this.timer = null
          this.updateTableEmptyConfig()
          setTimeout(() => {
            this.isTableLoading = false
          }, 200)
        }, 300)
      },

      async getResources () {
        const apigwId = this.apigwId
        try {
          const res = await this.$store.dispatch('gatewayPlugin/getResources', { apigwId })
          this.resourceList = res.data
          this.searchResourceCondition[1].children = this.resourceList.map(item => {
            return {
              id: item.id,
              name: item.name
            }
          })
        } catch (e) {
          catchErrorHandler(e, this)
        }
      },

      handleEditResource (data) {
        this.resourceSliderConf.isShow = true
        this.resourceSliderConf.type = 'edit'
        this.resourceSliderConf.title = this.$t('编辑白名单')
        this.curResource.bkAppCode = data.bk_app_code
        this.manner = data.dimension
        this.resourceTargetList = data.resource_ids
        if (this.rules.bkAppCode.length > 2) {
          this.rules.bkAppCode.pop()
        }
        this.handleResourceScroll()
        // 编辑需要添加资源选择对比
        const initData = {
          ...this.curResource,
          manner: this.manner,
          resourceIds: this.resourceIds
        }
        this.initSidebarFormData(initData)
      },

      handleAddResource () {
        this.resourceSliderConf.isShow = true
        this.resourceSliderConf.type = 'add'
        this.resourceSliderConf.title = this.$t('添加白名单')
        this.resourceTargetList = []
        this.rules.bkAppCode.push({
          validator: (value) => {
            const filterArr = this.dataList.filter(item => item.bk_app_code === value)
            return !filterArr.length
          },
          message: this.$t('该蓝鲸应用ID白名单已存在'),
          trigger: 'blur'
        })
        this.handleResourceScroll()
        // 添加
        const initData = {
          ...this.curResource,
          manner: this.manner
        }
        this.initSidebarFormData(initData)
      },

      // 分页
      getTableData () {
        this.isTableLoading = true
        let pageSize = Math.ceil(this.dataList.length / this.pagination.limit)
        let tableDataList = this.dataList
        // 筛选条件数据
        if (this.searchParams.bk_app_code || this.searchParams.resource_id) {
          tableDataList = this.searchList
          pageSize = Math.ceil(this.searchList.length / this.pagination.limit)
        }
        if (pageSize < this.pagination.current) {
          this.pagination.current = pageSize
        }
        if (this.pagination.current < 1) {
          this.pagination.current = 1
        }
        const startCurrent = this.pagination.current - 1
        this.pagingList = tableDataList.slice(startCurrent < 0 ? 0 : startCurrent * this.pagination.limit, this.pagination.current * this.pagination.limit)
        this.pagination.count = tableDataList.length || 0
        // 添加子项
        this.searchResourceCondition[0].children = tableDataList.map(item => {
          return {
            id: item.bk_app_code,
            name: item.bk_app_code
          }
        })
        setTimeout(() => {
          this.isTableLoading = false
        }, 300)
      },

      handlePageChange (newPage, pageSize) {
        this.pagination.current = newPage
        this.pagination.limit = pageSize
        this.getTableData()
      },

      handlePageLimitChange (limit) {
        this.pagination.limit = limit
        this.getTableData()
      },

      handleBatchRemovePolicy () {
        const self = this
        if (!self.whiteListPolicyList.length) {
          self.$bkMessage({
            theme: 'error',
            message: this.$t('请选择要删除的白名单')
          })
          return false
        }

        self.$bkInfo({
          title: this.$t('确认要批量删除白名单？'),
          confirmFn () {
            self.deleteInBatchesPolicy()
          }
        })
      },

      sidesliderHidden () {
        this.clearSidesliderForm()
        this.removeResourceScroll()
      },
      handleResourceSelect (selectedList) {
        this.whiteListPolicyList = selectedList
      },

      handleResourceChange (sourceList, targetList, targetValueList) {
        this.resourceIds = targetValueList
      },

      handlerAddPolicy () {
        const dimension = this.manner
        const resourceIds = dimension === 'api' ? [] : this.resourceIds
        this.dataList.push({
          bk_app_code: this.curResource.bkAppCode,
          dimension,
          resource_ids: resourceIds,
          rowHeight: 'auto',
          isIconView: false
        })
        this.handleHideResourceSlider()
        this.getTableData()
        this.confirmLoading = false
      },

      handlerUpdatePolicy () {
        const dimension = this.manner
        const resourceIds = dimension === 'api' ? [] : this.resourceIds
        this.dataList.find(item => {
          if (item.bk_app_code === this.curResource.bkAppCode) {
            this.$set(item, 'dimension', dimension)
            this.$set(item, 'resource_ids', resourceIds)
          }
        })
        this.handleHideResourceSlider()
        this.getTableData()
        this.confirmLoading = false
      },

      handlerDeletePolicy (data) {
        for (let i = 0; i < this.dataList.length; i++) {
          if (this.dataList[i].bk_app_code === data.bk_app_code) {
            this.dataList.splice(i, 1)
            break
          }
        }
        this.getSearchDataList()
        this.getTableData()
      },

      // 批量删除
      deleteInBatchesPolicy () {
        this.dataList = this.dataList.filter((x) => !this.whiteListPolicyList.some((item) => x.bk_app_code === item.bk_app_code))
        this.getTableData()
      },

      sendPolicyData () {
        this.$emit('parmas-yaml', this.jsonConvertYaml())
      },

      jsonConvertYaml () {
        const mapList = this.dataList.map(item => {
          return {
            'bk_app_code': item.bk_app_code,
            'dimension': item.dimension,
            'resource_ids': item.resource_ids
          }
        })
        const jsonStr = JSON.stringify({ 'exempted_apps': mapList })
        try {
          return {
            data: jsYaml.dump(JSON.parse(jsonStr)),
            error: false
          }
        } catch (err) {
          return {
            data: '',
            error: true
          }
        }
      },

      // 接口数组转换
      yamlConvertJson (yamlStr) {
        try {
          const yamlData = jsYaml.load(yamlStr) || { exempted_apps: [] }
          const { exempted_apps: list } = yamlData
          if (list.length) {
            this.dataList = list.map(item => {
              return {
                'bk_app_code': item.bk_app_code,
                'dimension': item.dimension,
                'resource_ids': item.resource_ids,
                'rowHeight': 'auto',
                'isIconView': false
              }
            })
            // 排序
            this.dataList.sort((a, b) => {
              return ('' + a.bk_app_code).localeCompare(b.bk_app_code)
            })
          }
          this.getTableData()
        } catch (err) {
          console.error(err)
        }
      },
            
      handleBindResource () {
        this.confirmLoading = true
        this.$refs.validateForm1.validate().then(validator => {
          if (this.resourceSliderConf.type === 'add') {
            this.handlerAddPolicy()
          } else {
            this.handlerUpdatePolicy()
          }
        }, validator => {
          this.confirmLoading = false
        })
      },

      handleHideResourceSlider () {
        this.resourceSliderConf.isShow = false
        this.clearSidesliderForm()
      },

      clearSidesliderForm () {
        this.resourceIds = []
        this.curResource.bkAppCode = ''
        this.manner = 'api'
      },

      handlerIcon (data) {
        if (data.rowHeight === 'auto' || !data.isIconView) {
          this.pagingList.forEach(item => {
            this.$set(item, 'rowHeight', 'auto')
          })
          data.rowHeight = `${data.resource_ids.length * 30}px`
        } else {
          this.pagingList.forEach(item => {
            this.$set(item, 'rowHeight', 'auto')
          })
        }
        if (!data.isIconView) {
          this.pagingList.forEach(item => {
            item.isIconView = false
          })
          data.isIconView = true
        } else {
          this.pagingList.forEach(item => {
            this.$set(item, 'isIconView', false)
          })
        }
      },

      formatFilterData () {
        const map = {}
        this.searchFilters.forEach(filter => {
          map[filter.id] = filter
        })
        const keys = Object.keys(map)
        this.searchFilters = []
        keys.forEach(key => {
          this.searchFilters.push(map[key])
        })
      },

      getSearchDataList () {
        if (!this.searchParams.bk_app_code && !this.searchParams.resource_id) {
          this.getTableData()
          return
        }
        if (this.searchParams.bk_app_code && this.searchParams.resource_id) {
          this.filterSearchList('all')
        } else {
          if (this.searchParams.bk_app_code) {
            this.filterSearchList('bk_app_code')
          }
          if (this.searchParams.resource_id) {
            this.filterSearchList('resource_id')
          }
        }
        this.updateTableEmptyConfig()
      },

      filterSearchList (key) {
        this.isTableLoading = true
        if (key === 'all') {
          this.pagingList = this.dataList.filter(item => {
            if (item.bk_app_code === this.searchParams.bk_app_code && item.resource_ids.includes(this.searchParams.resource_id)) {
              return true
            }
          })
        } else {
          if (key === 'bk_app_code') {
            this.pagingList = this.dataList.filter(item => {
              if (item.bk_app_code === this.searchParams[key]) {
                return true
              }
            })
          } else {
            this.pagingList = this.dataList.filter(item => {
              if (item.resource_ids.includes(this.searchParams[key])) {
                return true
              }
            })
          }
        }
        this.searchList = this.pagingList
        this.pagination.count = this.pagingList.length || 0
        setTimeout(() => {
          this.isTableLoading = false
        }, 300)
      },

      clearSearchFilters () {
        this.getTableData()
      },

      tableRowClick (row) {
        this.handlerIcon(row)
      },

      dragendColumn (newWidth) {
        this.eleTargetWidth = newWidth - 20
      },

      // 合适时机调用
      getResourcesViewWidth () {
        this.$nextTick(() => {
          setTimeout(() => {
            let content = document.querySelector('.parent')
            if (content) {
              while (content.tagName !== 'BODY') {
                content = content.parentNode
                if (content.className === 'cell') {
                  this.eleTargetWidth = content.clientWidth - 20
                  break
                }
              }
            }
          }, 0)
        })
      },

      clearFilterKey () {
        this.searchFilters = []
        this.searchParams = {
          bk_app_code: '',
          resource_id: ''
        }
      },

      updateTableEmptyConfig () {
        this.tableEmptyConf.keyword = this.searchFilters.length ? 'placeholder' : ''
      },

      async handleResourceScroll () {
        this.$nextTick(() => {
          this.sourceEl = document.querySelectorAll('.white-transfer-wrapper ul.content')
          this.sourceEl.forEach((el) => {
            el.addEventListener('scroll', this.hideToolTips)
          })
        })
      },

      hideToolTips: _.throttle(() => {
        const tipsEl = document.querySelectorAll('.tippy-popper')
        if (tipsEl.length) {
          tipsEl[0].parentNode.removeChild(tipsEl[tipsEl.length - 1])
        }
      }, 60),

      removeResourceScroll () {
        this.sourceEl.forEach((el) => {
          el.removeEventListener('scroll', this.hideToolTips)
        })
      },

      async handleBeforeClose () {
        // 添加
        const initData = {
          ...this.curResource,
          manner: this.manner
        }
        // 编辑
        if (this.resourceSliderConf.type === 'edit') {
          initData['resourceIds'] = this.resourceIds
        }
        return this.$isSidebarClosed(JSON.stringify(initData))
      }
    }
  }
</script>

<style lang="postcss" scoped>
    .top-tips {
        font-size: 14px;
        font-weight: bold;
        line-height: 1;
        color: #63656e;
    }
    .icon-class {
        font-size: 16px;
    }
    .white-transfer-wrapper {
        padding: 20px;
        padding-bottom: 10px;
        border: 1px solid #dde4eb;
        background-color: rgb(244, 247, 250);

        .icon-class {
            color: #63656e;
        }

        .tips-text {
            margin-top: 8px;
            font-size: 12px;
            color: #63656e;
        }
    }

    .play-shape {
        display: flex;
        width: 100%;
        height: 100%;
        align-items: center;
        justify-content: center;
        position: relative;
        cursor: pointer;
        font-size: 14px;
        height: 20px;
        color: #c4c6cc;

        &::before {
            content: '';
            position: absolute;
            padding: 10px;
        }
    }

    .icon-view {
        transition: all .3s;
        transform: rotate(90deg);
    }

    .icon-conceal {
        transition: all .2s;
        transform: rotate(0deg);
    }
    .parent {
        position: relative;
    }

    .column-wrapper {
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }

    .text-view {
        float: left;
        display: block;
        width: 100%;
    }

    /deep/ .bk-table-footer-wrapper, .bk-table-header-wrapper {
        overflow: auto;
    }

    .transfer-source-item {
        white-space: nowrap;
        text-overflow: ellipsis;
        overflow: hidden;
    }
    
</style>
