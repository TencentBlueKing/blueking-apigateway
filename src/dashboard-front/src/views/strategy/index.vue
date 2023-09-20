<template>
  <div class="app-content">
    <bk-tab
      :active.sync="tabActive"
      type="unborder-card"
      :ext-cls="'ag-strategy-tab'"
      style="margin-top: -10px;"
      @tab-change="handleTabChange">
      <bk-tab-panel
        :name="'strategy'"
        :label="$t('策略列表')">
        <ag-loader :is-loading="isPageLoading" loader="table-loader" :offset-top="0" :offset-left="0">
          <div class="ag-top-header">
            <bk-button theme="primary" @click="handleCreateStrategy"> {{ $t('新建策略') }} </bk-button>
            <bk-input
              class="fr"
              :clearable="true"
              v-model="keyword"
              :placeholder="$t('请输入策略名，按Enter搜索')"
              :right-icon="'bk-icon icon-search'"
              style="width: 240px;"
              @enter="handleSearch">
            </bk-input>
          </div>
          <bk-table style="margin-top: 15px;"
            ref="strategyRef"
            :data="strategyList"
            :size="'small'"
            :pagination="pagination"
            v-bkloading="{ isLoading: isDataLoading }"
            :ext-cls="'ag-strategy-table'"
            :cell-style="{ 'overflow': 'visible', 'white-space': 'normal' }"
            v-show="tabActive === 'strategy'"
            @page-limit-change="handlePageLimitChange"
            @page-change="handlePageChange"
            @sort-change="handleSortChange(...arguments, 'strategy')"
            @filter-change="handleFilterChange">
            <div slot="empty">
              <table-empty
                ref-val="strategyRef"
                :keyword="strategyEmptyConf.keyword"
                :abnormal="strategyEmptyConf.isAbnormal"
                @reacquire="getApigwStrategies"
                @clear-filter="clearFilterKey"
              />
            </div>
            <bk-table-column :label="$t('名称')" prop="name" sortable column-key="name">
              <template slot-scope="props">
                <span class="ag-auto-text">
                  {{props.row.name || '--'}}
                </span>
              </template>
            </bk-table-column>
            <bk-table-column
              :label="$t('类型')"
              prop="type"
              column-key="type"
              :filters="typeFilters"
              :filter-multiple="false">>
              <template slot-scope="props">
                <template v-if="props.row.type === 'ip_access_control'">
                  {{ $t('IP访问控制') }}
                </template>
                <template v-else-if="props.row.type === 'rate_limit'">
                  {{ $t('频率控制') }}
                </template>
                <template v-else-if="props.row.type === 'cors'">
                  {{ $t('跨域资源共享(CORS)') }}
                </template>
                <template v-else-if="props.row.type === 'user_verified_unrequired_apps'">
                  {{ $t('免用户认证应用白名单') }}
                </template>
                <template v-else-if="props.row.type === 'error_status_code_200'">
                  {{ $t('网关错误使用HTTP状态码200(不推荐)') }}
                </template>
                <template v-else-if="props.row.type === 'circuit_breaker'">
                  {{ $t('断路器') }}
                </template>
                <template v-else>--</template>
              </template>
            </bk-table-column>
            <bk-table-column :label="$t('更新时间')" prop="updated_time" sortable column-key="updated_time" :render-header="$renderHeader"></bk-table-column>
            <bk-table-column :label="$t('操作')" width="150" :show-overflow-tooltip="false">
              <template slot-scope="props">
                <bk-button
                  class="mr10"
                  theme="primary"
                  text
                  @click="handleEditStrategy(props.row)">
                  {{ $t('编辑') }}
                </bk-button>
                <bk-dropdown-menu ref="dropdown" align="right">
                  <i class="bk-icon icon-more ag-more-btn ml10" slot="dropdown-trigger"></i>
                  <ul class="bk-dropdown-list" slot="dropdown-content" style="width: 80px; ">
                    <li>
                      <a href="javascript:;" @click="handleBindStage(props.row)"> {{ $t('绑定环境') }} </a>
                    </li>
                    <li v-if="props.row.type === 'rate_limit' || props.row.type === 'user_verified_unrequired_apps' || props.row.type === 'cors' || props.row.type === 'circuit_breaker'">
                      <a href="javascript:;" @click.stop.prevent="handleBindResource(props.row)"> {{ $t('绑定资源') }} </a>
                    </li>
                    <li>
                      <a href="javascript:;" @click="handleRemoveStrategy(props.row)"> {{ $t('删除') }} </a>
                    </li>
                  </ul>
                </bk-dropdown-menu>
              </template>
            </bk-table-column>
          </bk-table>
        </ag-loader>
      </bk-tab-panel>

      <bk-tab-panel
        :name="'IPGroup'"
        :label="$t('IP分组')">
        <ag-loader :is-loading="isPageLoading" loader="table-loader" :offset-top="0" :offset-left="0">
          <div class="ag-top-header">
            <bk-button theme="primary" @click="handleIPGroupCreate"> {{ $t('新建IP分组') }} </bk-button>
            <bk-input
              class="fr"
              :clearable="true"
              v-model="IPGroupKeyword"
              :placeholder="$t('请输入IP分组名，按Enter搜索')"
              :right-icon="'bk-icon icon-search'"
              style="width: 240px;"
              @enter="handleSearchIPGroup">
            </bk-input>
          </div>
          <bk-table style="margin-top: 15px;"
            ref="IPGroupRef"
            :data="IPGroupList"
            :size="'small'"
            :pagination="IPPagination"
            v-bkloading="{ isLoading: isDataLoading }"
            :ext-cls="'ag-strategy-table'"
            :cell-style="{ 'overflow': 'visible', 'white-space': 'normal' }"
            v-show="tabActive === 'IPGroup'"
            @page-limit-change="handleIPGroupPageLimitChange"
            @page-change="handleIPGroupPageChange"
            @sort-change="handleSortChange(...arguments, 'IPGroup')">
            <div slot="empty">
              <table-empty
                ref-val="IPGroupRef"
                :keyword="groupEmptyConf.keyword"
                :abnormal="groupEmptyConf.isAbnormal"
                @reacquire="getApigwIPGroups"
                @clear-filter="clearIPGroupKeywordy"
              />
            </div>
            <bk-table-column :label="$t('名称')" prop="name" sortable column-key="name"></bk-table-column>
            <bk-table-column :label="$t('更新时间')" prop="updated_time" sortable column-key="updated_time" :render-header="$renderHeader"></bk-table-column>
            <bk-table-column :label="$t('备注')" prop="comment">
              <template slot-scope="props">
                {{props.row.comment || '--'}}
              </template>
            </bk-table-column>
            <bk-table-column :label="$t('操作')" width="200">
              <template slot-scope="props">
                <bk-button
                  class="mr10"
                  theme="primary"
                  text
                  @click="handleEditIPGroup(props.row)">
                  {{ $t('编辑') }}
                </bk-button>
                <bk-button
                  class="mr10"
                  theme="primary"
                  text
                  @click="handleRemoveIPGroup(props.row)">
                  {{ $t('删除') }}
                </bk-button>
              </template>
            </bk-table-column>
          </bk-table>
        </ag-loader>
      </bk-tab-panel>
    </bk-tab>

    <bk-sideslider
      :title="IPGroupSliderConf.title"
      :width="838"
      :is-show.sync="IPGroupSliderConf.isShow"
      :quick-close="true"
      :before-close="handleIpBeforeClose">
      <div slot="content" class="p30">
        <bk-form ref="IPGroupForm" :label-width="100" :model="curIPGroup">
          <bk-form-item
            :label="$t('名称')"
            :required="true"
            :rules="IPGroupRule.name"
            :property="'name'"
            :error-display-type="'normal'">
            <bk-input :placeholder="$t('请输入')" v-model="curIPGroup.name"></bk-input>
          </bk-form-item>
          <bk-form-item :label="$t('IP列表')"
            :property="'ips'">
            <p class="f12" style="color: #63656E;">
              <i class="apigateway-icon icon-ag-info mr5"></i> {{ $t('多个IP以换行分隔，支持网段，如：1.0.0.1/8') }}
            </p>
            <code-viewer
              ref="IPGroupCodeViewer"
              :value="curIPGroup.ips"
              :width="'100%'"
              :height="370"
              :placeholder="$t('请输入IP')"
              :lang="'text'"
              @input="handleInputIP">
            </code-viewer>
          </bk-form-item>
          <bk-form-item :label="$t('备注')">
            <bk-input v-model="curIPGroup.comment"></bk-input>
          </bk-form-item>
          <bk-form-item label="">
            <bk-button theme="primary" class="mr10" @click="submitApigwIPGroup"> {{ $t('提交') }} </bk-button>
            <bk-button @click="handleHideIPGroupSlider"> {{ $t('取消') }} </bk-button>
          </bk-form-item>
        </bk-form>
      </div>
    </bk-sideslider>

    <bk-sideslider
      :title="stageBindSliderConf.title"
      :width="560"
      :is-show.sync="stageBindSliderConf.isShow"
      :quick-close="true"
      :before-close="handleBeforeClose">
      <div slot="content" class="p30" v-bkloading="{ isLoading: isBindLoading }">
        <bk-form ref="stageBindForm" :label-width="60" :model="curStrategy" style="min-height: 600px;">
          <bk-form-item
            :label="$t('名称')">
            <span class="f12">{{curStrategy.name}}</span>
          </bk-form-item>
          <bk-form-item
            :label="$t('环境')">
            <bk-select
              searchable
              multiple
              show-select-all
              v-model="scopeIds">
              <bk-option v-for="option in stageList"
                :key="option.id"
                :id="option.id"
                :name="option.name">
              </bk-option>
            </bk-select>
            <!-- <bk-tag-input
                            v-model="curStrategy.scope_ids"
                            placeholder="请选择环境"
                            :list="stageList"
                            :trigger="'focus'"
                            :content-max-height="200"
                            :allow-next-focus="false">
                        </bk-tag-input> -->
            <div class="ag-alert warning mt10">
              <i class="apigateway-icon icon-ag-info"></i>
              <p> {{ $t('如果环境已经绑定了一个策略，则会被本策略覆盖，请谨慎操作') }} </p>
            </div>
          </bk-form-item>
          <bk-form-item label="">
            <bk-button theme="primary" class="mr10" @click="checkBindeResources"> {{ $t('保存') }} </bk-button>
            <bk-button @click="handleHideStageSlider"> {{ $t('取消') }} </bk-button>
          </bk-form-item>
        </bk-form>
      </div>
    </bk-sideslider>

    <bk-sideslider
      :title="resourceBindSliderConf.title"
      :width="840"
      :is-show.sync="resourceBindSliderConf.isShow"
      :quick-close="true"
      :before-close="handleBeforeClose">
      <div slot="content" class="p30" v-bkloading="{ isLoading: isBindLoading }">
        <bk-form ref="resourceBindForm" :label-width="60" :model="curStrategy">
          <bk-form-item
            :label="$t('名称')">
            <span class="f12">{{curStrategy.name}}</span>
          </bk-form-item>
          <bk-form-item
            :label="$t($t('资源'))">
            <bk-transfer
              ext-cls="resource-transfer-wrapper"
              :target-list="resourceTargetList"
              :source-list="resourceList"
              :display-key="'resourceName'"
              :setting-key="'id'"
              :sortable="true"
              :sort-key="'resourceName'"
              :title="[$t('未选资源'), $t('已选资源')]"
              :searchable="true"
              @change="handleResourceChange">
              <div
                slot="source-option"
                slot-scope="data"
                class="transfer-source-item"
                :title="data.resourceName"
              >
                {{ data.resourceName }}
              </div>
              <div
                slot="target-option"
                slot-scope="data"
                class="transfer-source-item"
                :title="data.resourceName"
              >
                {{ data.resourceName }}
              </div>
            </bk-transfer>
            <div class="ag-alert warning mt10">
              <i class="apigateway-icon icon-ag-info"></i>
              <p> {{ $t('如果资源已经绑定了一个策略，则会被本策略覆盖，请谨慎操作') }} </p>
            </div>
          </bk-form-item>
          <bk-form-item label="">
            <bk-button theme="primary" class="mr10" @click="checkBindeResources" :loading="isChecking"> {{ $t('保存') }} </bk-button>
            <bk-button @click="handleHideResourceSlider"> {{ $t('取消') }} </bk-button>
          </bk-form-item>
        </bk-form>
      </div>
    </bk-sideslider>

    <!-- <bk-dialog
            v-model="deleteStrategyDialogConf.visiable"
            theme="primary"
            :mask-close="false"
            :width="525"
            :title="`确定要策略【${curStrategy.name}】？`"
            @cancel="deleteStrategyDialogConf.visiable = false"
            @confirm="removeStrategy">
            <p class="tc p10">将删除该策略相关配置，不可恢复，请确认删除</p>
        </bk-dialog> -->

    <bk-dialog
      v-model="strategyDialogConf.isShow"
      theme="primary"
      :width="480"
      :mask-close="false"
      :header-position="'left'"
      :title="strategyDialogConf.title"
      :loading="strategyDialogConf.isLoading"
      @confirm="handleSubmitStrategy"
      @cancel="handleCancel">
      <bk-form
        :label-width="200"
        form-type="vertical"
        :model="curStrategy"
        :rules="rules"
        ref="strategyForm">
        <bk-form-item :strategy="$t('策略名称')" :required="true" :property="'name'">
          <bk-input v-model="curStrategy.name"></bk-input>
        </bk-form-item>
      </bk-form>
    </bk-dialog>

    <bk-dialog
      v-model="unbindResourceConf.isShow"
      theme="primary"
      :width="670"
      :title="`${curStrategy.scope_type === 'stage' ? $t('环境') : $t('资源') }${$t('绑定变更，请确认')}`"
      :mask-close="true"
      @cancel="unbindResourceConf.isShow = false"
      @confirm="submitBindingData">
      <div>
        <bk-table
          :data="bindChangeResources"
          :size="'small'"
          :max-height="280"
          :key="tableIndex">
          <div slot="empty">
            <table-empty empty />
          </div>
          <bk-table-column :label="$t('环境名称')" prop="name" v-if="curStrategy.scope_type === 'stage'" :render-header="$renderHeader"></bk-table-column>
          <bk-table-column :label="$t('请求路径')" prop="path" v-if="curStrategy.scope_type === 'resource'" :render-header="$renderHeader">
            <template slot-scope="props">
              <span class="ag-auto-text">{{props.row.path || '--'}}</span>
            </template>
          </bk-table-column>
          <bk-table-column :label="$t('请求方法')" prop="method" v-if="curStrategy.scope_type === 'resource'" :render-header="$renderHeader"></bk-table-column>
          <bk-table-column :label="$t('原策略')">
            <template slot-scope="props">
              <span class="ag-auto-text">{{props.row.oldStrategy.access_strategy_name || '--'}}</span>
            </template>
          </bk-table-column>
          <bk-table-column :label="$t('目标策略')" :render-header="$renderHeader">
            <template slot-scope="props">
              <template v-if="props.row.bindStatus === 'delete'">
                --
              </template>
              <template v-else>
                <span class="ag-auto-text">{{props.row.newStrategy.name || '--'}}</span>
              </template>
            </template>
          </bk-table-column>
          <bk-table-column :label="$t('变更状态')" prop="bindStatus" :render-header="$renderHeader">
            <template slot-scope="props">
              <template v-if="props.row.bindStatus === 'add'">
                <span class="ag-tag primary"> {{ $t('绑定') }} </span>
              </template>
              <template v-else-if="props.row.bindStatus === 'delete'">
                <span class="ag-tag warning"> {{ $t('解绑') }} </span>
              </template>
              <template v-else-if="props.row.bindStatus === 'merge'">
                <span class="ag-tag danger"> {{ $t('覆盖') }} </span>
              </template>
            </template>
          </bk-table-column>
        </bk-table>
        <template v-if="curStrategy.scope_type === 'stage'">
          <div class="ag-alert warning mt10" v-if="mergeResources.length">
            <i class="apigateway-icon icon-ag-info"></i>
            <p> {{ $t('部分环境已经绑定了策略，如果继续操作，原来的策略将被本策略覆盖') }} </p>
          </div>
          <div class="ag-alert warning mt10" v-else-if="unbindResources.length">
            <i class="apigateway-icon icon-ag-info"></i>
            <p> {{ $t('部分环境被取消选中，如果继续操作，原来的绑定将被解绑') }} </p>
          </div>
        </template>
        <template v-else>
          <div class="ag-alert warning mt10" v-if="mergeResources.length">
            <i class="apigateway-icon icon-ag-info"></i>
            <p> {{ $t('部分资源已经绑定了策略，如果继续操作，原来的策略将被本策略覆盖') }} </p>
          </div>
          <div class="ag-alert warning mt10" v-else-if="unbindResources.length">
            <i class="apigateway-icon icon-ag-info"></i>
            <p> {{ $t('部分资源被取消选中，如果继续操作，原来的绑定将被解绑') }} </p>
          </div>
        </template>
      </div>
    </bk-dialog>
  </div>
</template>

<script>
  import { catchErrorHandler, clearFilter } from '@/common/util'
  import sidebarMixin from '@/mixins/sidebar-mixin'

  export default {
    mixins: [sidebarMixin],
    data () {
      return {
        keyword: '',
        IPGroupKeyword: '',
        filterType: '',
        isPageLoading: true,
        isDataLoading: false,
        isTabContentLoading: true,
        tabActive: 'strategy',
        scopeIds: [],
        orderBy: {
          strategy: '',
          IPGroup: ''
        },
        strategyList: [],
        IPGroupList: [],
        tableIndex: 0,
        isChecking: false,
        isBindLoading: false,
        IPGroupSliderConf: {
          title: this.$t('新建IP分组'),
          isShow: false
        },
        pagination: {
          current: 1,
          count: 0,
          limit: 10
        },
        IPPagination: {
          current: 1,
          count: 0,
          limit: 10
        },
        strategyDialogConf: {
          isLoading: false,
          isShow: false,
          title: this.$t('新建策略')
        },
        stageBindSliderConf: {
          isLoading: false,
          isShow: false,
          title: this.$t('绑定环境')
        },
        resourceBindSliderConf: {
          isLoading: false,
          isShow: false,
          title: this.$t('绑定资源')
        },
        stageBindList: [],
        stageList: [],
        resourceList: [],
        resourceSourceList: [],
        resourceTargetList: [],
        resourceTargetListCache: [], // 用于解绑对比
        curStrategy: {
          name: ''
        },
        curIPGroup: {
          name: '',
          ips: '',
          comment: ''
        },
        IPGroupRule: {
          name: [
            {
              required: true,
              message: this.$t('必填项'),
              trigger: 'blur'
            },
            {
              max: 64,
              message: this.$t('不能多于64个字符'),
              trigger: 'blur'
            }
          ],
          ips: [
            {
              required: true,
              message: this.$t('必填项'),
              trigger: 'blur'
            },
            {
              validator (value) {
                const ipReg = /^((2(5[0-5]|[0-4]\d))|[0-1]?\d{1,2})(\.((2(5[0-5]|[0-4]\d))|[0-1]?\d{1,2})){3}$/
                const ips = value.split(/[\s\n]/)
                for (const ip of ips) {
                  if (!ipReg.test(ip)) {
                    return false
                  }
                }
                return true
              },
              message: this.$t('请输入合法IP地址'),
              trigger: 'blur'
            }
          ]
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
              trigger: 'blur'
            }
          ]
        },
        unbindResources: [],
        addResources: [],
        mergeResources: [],
        bindChangeResources: [],
        unbindResourceConf: {
          isShow: false
        },
        strategyEmptyConf: {
          keyword: '',
          isAbnormal: false
        },
        groupEmptyConf: {
          keyword: '',
          isAbnormal: false
        }
      }
    },
    computed: {
      apigwId () {
        return this.$route.params.id
      },
      typeFilters () {
        return [
          {
            value: 'ip_access_control',
            text: this.$t('IP访问控制')
          },
          {
            value: 'rate_limit',
            text: this.$t('频率控制')
          },
          {
            value: 'cors',
            text: this.$t('跨域资源共享(CORS)')
          },
          {
            value: 'circuit_breaker',
            text: this.$t('断路器')
          },
          {
            value: 'user_verified_unrequired_apps',
            text: this.$t('免用户认证应用白名单')
          },
          {
            value: 'error_status_code_200',
            text: this.$t('网关错误使用HTTP状态码200(不推荐)')
          }
        ]
      }
    },
    watch: {
      keyword (newVal, oldVal) {
        if (oldVal && !newVal) {
          this.handleSearch()
        }
      },
      filterType () {
        this.handleSearch()
      },
      IPGroupKeyword (newVal, oldVal) {
        if (oldVal && !newVal) {
          this.handleSearchIPGroup()
        }
      },
      'orderBy.strategy' () {
        this.handleSearch()
      },
      'orderBy.IPGroup' () {
        this.handleSearchIPGroup()
      }
    },
    created () {
      this.init()
    },
    methods: {
      init () {
        this.getApigwStages()
        this.getApigwResources()
        if (this.$route.query.type === 'IPGroup') {
          this.tabActive = 'IPGroup'
          this.getApigwIPGroups()
        } else {
          this.getApigwStrategies()
        }
      },

      async getApigwStrategies (page) {
        const apigwId = this.apigwId
        const curPage = page || this.pagination.current
        const pageParams = {
          limit: this.pagination.limit,
          offset: this.pagination.limit * (curPage - 1),
          query: this.keyword,
          order_by: this.orderBy['strategy']
        }

        if (this.filterType) {
          pageParams['type'] = this.filterType.toLowerCase()
        }

        this.isDataLoading = true
        try {
          const res = await this.$store.dispatch('strategy/getApigwStrategies', { apigwId, pageParams })
          this.strategyList = res.data.results
          this.pagination.count = res.data.count
          this.updateTableEmptyConfig()
          this.strategyEmptyConf.isAbnormal = false
        } catch (e) {
          this.strategyEmptyConf.isAbnormal = true
          catchErrorHandler(e, this)
        } finally {
          this.isPageLoading = false
          this.isDataLoading = false
          this.$store.commit('setMainContentLoading', false)
        }
      },

      async getApigwIPGroups (page) {
        const apigwId = this.apigwId
        const curPage = page || this.IPPagination.current
        const pageParams = {
          limit: this.IPPagination.limit,
          offset: this.IPPagination.limit * (curPage - 1),
          query: this.IPGroupKeyword,
          order_by: this.orderBy['IPGroup']
        }

        this.isDataLoading = true
        try {
          const res = await this.$store.dispatch('strategy/getApigwIPGroups', { apigwId, pageParams })

          this.IPGroupList = res.data.results
          this.IPPagination.count = res.data.count
          this.updateGroupEmptyConf()
          this.groupEmptyConf.isAbnormal = false
        } catch (e) {
          this.groupEmptyConf.isAbnormal = true
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
        this.getApigwStrategies(this.pagination.current)
      },

      handlePageChange (newPage) {
        this.pagination.current = newPage
        this.getApigwStrategies(newPage)
      },

      handleIPGroupPageLimitChange (limit) {
        this.IPPagination.limit = limit
        this.IPPagination.current = 1
        this.getApigwIPGroups(this.IPPagination.current)
      },

      handleIPGroupPageChange (newPage) {
        this.IPPagination.current = newPage
        this.getApigwIPGroups(newPage)
      },

      handleCreateStrategy () {
        this.$router.push({
          name: 'apigwStrategyCreate'
        })
      },

      handleIPGroupCreate () {
        this.curIPGroup = {
          name: '',
          ips: '',
          comment: ''
        }
        this.IPGroupSliderConf.title = this.$t('新建IP分组')
        this.IPGroupSliderConf.isShow = true
        this.initSidebarFormData(this.curIPGroup)
      },

      handleEditIPGroup (data) {
        this.curIPGroup = JSON.parse(JSON.stringify(data))
        this.IPGroupSliderConf.title = this.$t('IP分组详情')
        this.IPGroupSliderConf.isShow = true

        setTimeout(() => {
          this.$refs.IPGroupCodeViewer.$ace.scrollToLine(1, true, true)
          this.initSidebarFormData(this.curIPGroup)
        }, 300)
      },

      submitApigwIPGroup () {
        this.$refs.IPGroupForm.validate().then(() => {
          const params = this.formatIPGroupData()

          if (this.checkIPGroupData(params)) {
            if (this.curIPGroup.id) {
              this.updateApigwIPGroup(params)
            } else {
              this.addApigwIPGroup(params)
            }
          }
        })
      },

      checkIPGroupData (params) {
        if (!params.name) {
          this.$bkMessage({
            theme: 'error',
            message: this.$t('请输入名称')
          })
          this.$refs.form.validate()
          return false
        }

        return true
      },

      formatIPGroupData () {
        const params = JSON.parse(JSON.stringify(this.curIPGroup))
        return params
      },

      async addApigwIPGroup (data) {
        this.isDataLoading = true
        try {
          const apigwId = this.apigwId
          await this.$store.dispatch('strategy/addApigwIPGroup', { apigwId, data })

          this.$bkMessage({
            theme: 'success',
            message: this.$t('新建成功！')
          })
          this.getApigwIPGroups()
          this.handleHideIPGroupSlider()
        } catch (e) {
          catchErrorHandler(e, this)
        } finally {
          this.isDataLoading = false
        }
      },

      async updateApigwIPGroup (data) {
        try {
          const apigwId = this.apigwId
          const IPGroupId = data.id
          await this.$store.dispatch('strategy/updateApigwIPGroup', { apigwId, IPGroupId, data })

          this.$bkMessage({
            theme: 'success',
            message: this.$t('更新成功！')
          })
          this.getApigwIPGroups()
          this.handleHideIPGroupSlider()
        } catch (e) {
          catchErrorHandler(e, this)
        }
      },

      handleHideIPGroupSlider () {
        this.curIPGroup = {
          name: '',
          ips: '',
          comment: ''
        }
        this.IPGroupSliderConf.isShow = false
      },

      handleSubmitStrategy () {
        this.strategyDialogConf.isLoading = true
        this.$refs.strategyForm.validate().then(() => {
          if (this.curStrategy.id !== undefined) {
            this.updateStrategy()
          } else {
            this.addStrategy()
          }
        }).finally(() => {
          this.$nextTick(() => {
            this.strategyDialogConf.isLoading = false
          })
        })
      },

      handleCancel () {
        this.clearStrategyForm()
      },

      handleEditStrategy (data) {
        this.$router.push({
          name: 'apigwStrategyEdit',
          params: {
            id: this.apigwId,
            strategyId: data.id
          }
        })
      },

      clearStrategyForm () {
        this.curStrategy.name = ''
        delete this.curStrategy.id
        this.$refs.strategyForm.formItems.forEach(item => {
          item.validator = {
            state: '',
            content: ''
          }
        })
      },

      async addStrategy () {
        try {
          const data = { name: this.curStrategy.name }
          const apigwId = this.apigwId
          await this.$store.dispatch('strategy/addApigwStrategy', { apigwId, data })
          this.strategyDialogConf.isShow = false
          this.clearStrategyForm()
          this.getApigwStrategies()
          this.$bkMessage({
            theme: 'success',
            message: this.$t('新建成功！')
          })
        } catch (e) {
          catchErrorHandler(e, this)
        }
      },

      async updateStrategy () {
        try {
          const data = { name: this.curStrategy.name }
          const apigwId = this.apigwId
          const strategyId = this.curStrategy.id
          await this.$store.dispatch('strategy/updateApigwStrategy', { apigwId, strategyId, data })
          this.strategyDialogConf.isShow = false
          this.clearStrategyForm()
          this.getApigwStrategies()

          this.$bkMessage({
            theme: 'success',
            message: this.$t('更新成功！')
          })
        } catch (e) {
          catchErrorHandler(e, this)
        }
      },

      async removeStrategy () {
        try {
          const apigwId = this.apigwId
          const strategyId = this.curStrategy.id
          await this.$store.dispatch('strategy/deleteApigwStrategy', { apigwId, strategyId })
          // 当前页只有一条数据
          if (this.strategyList.length === 1 && this.pagination.current > 1) {
            this.pagination.current--
          }
          this.getApigwStrategies()

          this.$bkMessage({
            theme: 'success',
            message: this.$t('删除成功！')
          })
        } catch (e) {
          catchErrorHandler(e, this)
        }
      },

      async removeIPGroup (data) {
        try {
          const apigwId = this.apigwId
          const IPGroupId = data.id
          await this.$store.dispatch('strategy/deleteApigwIPGroup', { apigwId, IPGroupId })

          // 当前页只有一条数据
          if (this.IPGroupList.length === 1 && this.IPPagination.current > 1) {
            this.IPPagination.current--
          }
          this.getApigwIPGroups()

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

        this.getApigwStrategies()
      },

      handleSearchIPGroup (event) {
        this.IPPagination.current = 1
        this.IPPagination.count = 0
        this.getApigwIPGroups()
      },

      handleRename (data) {
        this.curStrategy = JSON.parse(JSON.stringify(data))
        this.strategyDialogConf.title = this.$t('重命名策略')
        this.strategyDialogConf.isShow = true
      },

      handleRemoveStrategy (data) {
        const self = this

        this.curStrategy = data
        this.$bkInfo({
          title: `${this.$t('确定删除')}【${data.name}】${this.$t('策略')}？`,
          subTitle: this.$t('将删除相关配置，不可恢复，请确认是否删除？'),
          confirmFn () {
            self.removeStrategy()
          }
        })
      },

      handleRemoveIPGroup (data) {
        const self = this

        this.curStrategy = data
        this.$bkInfo({
          title: `${this.$t('确定删除')}【${data.name}】${this.$t('IP分组')}？`,
          subTitle: this.$t('将删除相关配置，不可恢复，请确认是否删除？'),
          confirmFn () {
            self.removeIPGroup(data)
          }
        })
      },

      async handleBindStage (data) {
        this.curStrategy = data
        this.curStrategy.scope_type = 'stage'
        // this.$set(this.curStrategy, 'scope_ids', [])
        this.scopeIds = []
        this.stageBindSliderConf.isShow = true

        await this.getApigwStrategyStages()
        this.initSidebarFormData(this.scopeIds)
      },

      async getApigwStages (page) {
        const apigwId = this.apigwId
        const pageParams = {
          no_page: true,
          order_by: 'name'
        }

        try {
          const res = await this.$store.dispatch('stage/getApigwStages', { apigwId, pageParams })

          this.stageList = res.data.results
        } catch (e) {
          catchErrorHandler(e, this)
        }
      },

      async getApigwStrategyStages () {
        const apigwId = this.apigwId
        const strategyId = this.curStrategy.id
        const scopeType = 'stage'
        const type = this.curStrategy.type

        this.isBindLoading = true
        try {
          const res = await this.$store.dispatch('strategy/getApigwStrategyBindings', { apigwId, strategyId, scopeType, type })
          res.data.results.forEach(item => {
            // this.curStrategy.scope_ids.push(item.scope_id)
            this.scopeIds.push(item.scope_id)
          })
        } catch (e) {
          catchErrorHandler(e, this)
        } finally {
          this.isBindLoading = false
        }
      },

      async submitApigwStrategyStages () {
        const apigwId = this.apigwId
        const strategyId = this.curStrategy.id
        const data = {
          scope_type: this.curStrategy.scope_type,
          scope_ids: this.scopeIds,
          type: this.curStrategy.type,
          delete: true
        }

        try {
          await this.$store.dispatch('strategy/updateApigwStrategyBindings', { apigwId, strategyId, data })
          this.$bkMessage({
            theme: 'success',
            message: this.$t('绑定环境成功')
          })
          this.stageBindSliderConf.isShow = false
        } catch (e) {
          catchErrorHandler(e, this)
        }
      },

      handleHideStageSlider () {
        this.stageBindSliderConf.isShow = false
      },

      async handleBindResource (data) {
        this.curStrategy = data
        this.curStrategy.scope_type = 'resource'
        // this.$set(this.curStrategy, 'scope_ids', [])
        this.scopeIds = []
        this.resourceBindSliderConf.isShow = true

        await this.getApigwStrategyResources()
        this.initSidebarFormData(this.scopeIds)
      },

      async getApigwResources (page) {
        const apigwId = this.apigwId
        const pageParams = {
          no_page: true,
          order_by: 'path'
        }

        try {
          const res = await this.$store.dispatch('resource/getApigwResources', { apigwId, pageParams })

          res.data.results.forEach(item => {
            item.resourceName = `${item.method}：${item.path}`
          })
          this.resourceList = res.data.results
        } catch (e) {
          catchErrorHandler(e, this)
        }
      },

      sort (list, key) {
        const sortKeys = list.map(item => {
          return item[key]
        })
        const results = []
        sortKeys.sort()

        sortKeys.forEach(sortItem => {
          list.forEach(item => {
            if (item[key] === sortItem) {
              results.push(item)
            }
          })
        })
        return results
      },

      async getApigwStrategyResources () {
        const apigwId = this.apigwId
        const strategyId = this.curStrategy.id
        const scopeType = 'resource'
        const type = this.curStrategy.type

        this.isBindLoading = true
        try {
          const res = await this.$store.dispatch('strategy/getApigwStrategyBindings', { apigwId, strategyId, scopeType, type })
          this.resourceTargetList = []
          this.resourceTargetListCache = []

          res.data.results.forEach(item => {
            // this.curStrategy.scope_ids.push(item.scope_id)
            this.scopeIds.push(item.scope_id)
            this.resourceTargetList.push(item.scope_id)
            this.resourceTargetListCache.push(item.scope_id)
          })
        } catch (e) {
          catchErrorHandler(e, this)
        } finally {
          this.isBindLoading = false
        }
      },

      async checkBindeResources () {
        if (this.isChecking) {
          return false
        }
        this.isChecking = true

        const apigwId = this.apigwId
        const strategyId = this.curStrategy.id
        const originList = this.curStrategy.scope_type === 'stage' ? this.stageList : this.resourceList
        const data = {
          scope_type: this.curStrategy.scope_type,
          scope_ids: this.scopeIds,
          type: this.curStrategy.type
        }
        try {
          const res = await this.$store.dispatch('strategy/checkApigwStrategyBindings', { apigwId, strategyId, data })
          const addList = res.data.normal_bind.map(item => {
            return item.scope_id
          })

          const deleteList = res.data.unbind.map(item => {
            return item.scope_id
          })

          const mergeList = res.data.overwrite_bind.map(item => {
            return item.scope_id
          })

          this.addResources = originList.filter(resource => {
            return addList.includes(resource.id)
          })

          this.unbindResources = originList.filter(resource => {
            return deleteList.includes(resource.id)
          })

          this.mergeResources = originList.filter(resource => {
            return mergeList.includes(resource.id)
          })

          this.bindChangeResources = []

          this.mergeResources.forEach(item => {
            item.bindStatus = 'merge'
            item.newStrategy = this.curStrategy
            item.oldStrategy = res.data.overwrite_bind.find(mergeItem => {
              return mergeItem.scope_id === item.id
            })
            this.bindChangeResources.push(item)
          })

          this.unbindResources.forEach(item => {
            item.bindStatus = 'delete'
            item.newStrategy = this.curStrategy
            item.oldStrategy = res.data.unbind.find(deleteItem => {
              return deleteItem.scope_id === item.id
            })
            this.bindChangeResources.push(item)
          })

          this.addResources.forEach(item => {
            item.bindStatus = 'add'
            item.newStrategy = this.curStrategy
            item.oldStrategy = res.data.normal_bind.find(addItem => {
              return addItem.scope_id === item.id
            })
            this.bindChangeResources.push(item)
          })

          if (this.bindChangeResources.length) {
            this.tableIndex++
            setTimeout(() => {
              this.unbindResourceConf.isShow = true
            }, 10)
          } else {
            this.submitBindingData()
          }
        } catch (e) {
          catchErrorHandler(e, this)
        } finally {
          this.isChecking = false
        }
      },

      submitBindingData () {
        if (this.curStrategy.scope_type === 'stage') {
          this.submitApigwStrategyStages()
        } else {
          this.submitApigwStrategyResources()
        }
      },

      async submitApigwStrategyResources () {
        const apigwId = this.apigwId
        const strategyId = this.curStrategy.id
        const data = {
          scope_type: this.curStrategy.scope_type,
          scope_ids: this.scopeIds,
          type: this.curStrategy.type,
          delete: true
        }

        try {
          await this.$store.dispatch('strategy/updateApigwStrategyBindings', { apigwId, strategyId, data })
          this.$bkMessage({
            theme: 'success',
            message: this.$t('绑定资源成功')
          })
          this.resourceBindSliderConf.isShow = false
        } catch (e) {
          catchErrorHandler(e, this)
        }
      },

      handleHideResourceSlider () {
        this.resourceBindSliderConf.isShow = false
      },

      handleResourceChange (sourceList, targetList, targetValueList) {
        // console.log(this.curStrategy.scope_ids)
        // this.curStrategy.scope_ids = targetValueList
        this.scopeIds = targetValueList
      },

      handleSortChange (params, type) {
        if (params.prop === 'name') {
          if (params.order === 'descending') {
            this.orderBy[type] = '-name'
          } else if (params.order === 'ascending') {
            this.orderBy[type] = 'name'
          } else {
            this.orderBy[type] = ''
          }
        }

        if (params.prop === 'updated_time') {
          if (params.order === 'descending') {
            this.orderBy[type] = '-updated_time'
          } else if (params.order === 'ascending') {
            this.orderBy[type] = 'updated_time'
          } else {
            this.orderBy[type] = ''
          }
        }
      },

      handleTabChange () {
        this.isPageLoading = true
        if (this.tabActive === 'IPGroup') {
          this.IPGroupKeyword = ''
          this.IPPagination = {
            current: 1,
            count: 0,
            limit: 10
          }
          this.getApigwIPGroups()
        } else {
          this.keyword = ''
          this.pagination = {
            current: 1,
            count: 0,
            limit: 10
          }
          this.getApigwStrategies()
        }
      },

      handleInputIP (content) {
        this.curIPGroup.ips = content
      },

      handleFilterChange (filters) {
        if (filters.type) {
          this.filterType = filters.type[0] ? filters.type[0] : ''
        }
      },

      clearFilterKey (ref) {
        this.keyword = ''
        this.$refs[ref].clearFilter()
        if (this.$refs.strategyRef && this.$refs.strategyRef.$refs.tableHeader) {
          clearFilter(this.$refs.strategyRef.$refs.tableHeader)
        }
      },

      updateTableEmptyConfig () {
        if (this.keyword || this.filterType) {
          this.strategyEmptyConf.keyword = 'placeholder'
          return
        }
        this.strategyEmptyConf.keyword = ''
      },

      clearIPGroupKeywordy (ref) {
        this.IPGroupKeyword = ''
        this.$refs[ref].clearFilter()
      },

      updateGroupEmptyConf () {
        this.groupEmptyConf.keyword = this.IPGroupKeyword
      },

      // ip分组
      async handleIpBeforeClose () {
        return this.$isSidebarClosed(JSON.stringify(this.curIPGroup))
      },

      // 环境/资源
      async handleBeforeClose () {
        return this.$isSidebarClosed(JSON.stringify(this.scopeIds))
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

    .ag-strategy-tab {
        background: transparent;
    }
</style>
