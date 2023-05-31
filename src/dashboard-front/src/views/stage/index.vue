<template>
  <div class="app-content">
    <div class="ag-top-header">
      <bk-button theme="primary" @click="handleCreateStage"> {{ $t('新建环境') }} </bk-button>
      <bk-input
        class="fr"
        :clearable="true"
        v-model="keyword"
        :placeholder="$t('请输入环境名称，按Enter搜索')"
        :right-icon="'bk-icon icon-search'"
        style="width: 300px;"
        @enter="handleSearch">
      </bk-input>
    </div>
    <bk-table style="margin-top: 15px;"
      :data="stageList"
      :size="'small'"
      :pagination="pagination"
      v-bkloading="{ isLoading: isDataLoading }"
      :ext-cls="'ag-stage-table'"
      @page-limit-change="handlePageLimitChange"
      @page-change="handlePageChange">
      <div slot="empty">
        <table-empty
          :keyword="tableEmptyConf.keyword"
          :abnormal="tableEmptyConf.isAbnormal"
          @reacquire="getApigwStages"
          @clear-filter="clearFilterKey"
        />
      </div>
      <bk-table-column :label="$t('名称')" prop="name"></bk-table-column>
      <bk-table-column :label="$t('描述')" prop="description" :show-overflow-tooltip="true">
        <template slot-scope="props">
          <template v-if="props.row.description">
            <span class="ag-auto-text">
              {{$t(props.row.description)}}
            </span>
          </template>
          <template v-else>
            --
          </template>
        </template>
      </bk-table-column>
      <bk-table-column :label="$t('发布状态')" prop="release_status" :show-overflow-tooltip="true" :render-header="$renderHeader">
        <template slot-scope="props">
          <template v-if="props.row.release_status">
            <span class="ag-ouline-dot success mr10"></span> {{ $t('已发布') }}
          </template>
          <template v-else>
            <span class="ag-ouline-dot mr10"></span> {{ $t('未发布') }}
          </template>
        </template>
      </bk-table-column>
      <bk-table-column :label="$t('访问策略')" v-if="stageFlagState" :render-header="$renderHeader">
        <template slot-scope="props">
          <template v-if="props.row.access_strategies.length">
            <router-link
              class="ag-text-link ag-auto-text"
              :to="{
                name: 'apigwStrategyEdit',
                params: {
                  id: apigwId,
                  strategyId: props.row.access_strategies[0].access_strategy_id
                },
                query: {
                  from: 'apigwStage'
                }
              }">{{props.row.access_strategies[0].access_strategy_name}}</router-link>
          </template>
          <template v-else>
            --
          </template>
        </template>
      </bk-table-column>
      <!-- <bk-table-column :label="$t('网关插件')" v-if="plugInFlagState">
                <template slot-scope="props">
                    <template v-if="props.row.plugins.length">
                        <router-link
                            class="ag-text-link ag-auto-text"
                            :to="{
                                name: 'apigwStrategyEdit',
                                params: {
                                    id: apigwId,
                                    strategyId: props.row.plugins[0].plugin_id
                                },
                                query: {
                                    from: 'apigwStage'
                                }
                            }">{{props.row.plugins[0].plugin_name}}</router-link>
                    </template>
                    <template v-else>
                        --
                    </template>
                </template>
            </bk-table-column> -->
      <bk-table-column width="200" :label="$t('发布时间')" prop="release_time" :render-header="$renderHeader"></bk-table-column>
      <bk-table-column width="300" :label="$t('当前版本')" prop="resource_version_name" :render-header="$renderHeader">
        <template slot-scope="props">
          <template v-if="props.row.release_status">
            <span class="ag-auto-text">
              {{props.row.resource_version_display || '--'}}
              <!-- {{props.row.resource_version_title || '--'}} ({{props.row.resource_version_name || '--'}}) -->
            </span>
          </template>
          <template v-else>
            --
          </template>
        </template>
      </bk-table-column>
      <bk-table-column :label="$t('操作')" width="150" class="ag-action" :show-overflow-tooltip="false">
        <template slot-scope="props">
          <bk-button
            class="mr10"
            text
            theme="primary"
            @click="handleEditStage(props.row)">
            {{ $t('编辑') }}
          </bk-button>
          <bk-dropdown-menu ref="dropdown" align="right">
            <i class="bk-icon icon-more ag-more-btn ml10" slot="dropdown-trigger"></i>
            <ul class="bk-dropdown-list" slot="dropdown-content" style="padding: 0 5px;">
              <li>
                <a href="javascript:;" @click.stop.prevent="handleRelease(props.row)"> {{ $t('发布') }} </a>
              </li>
              <template v-if="props.row.status">
                <li>
                  <a href="javascript:;" @click.stop.prevent="handleOfflineStage(props.row)"> {{ $t('下线') }} </a>
                </li>
              </template>
              <template v-else>
                <li class="disabled" v-bk-tooltips.left="{ content: $t('环境未发布') , boundary: 'window' }">
                  <a href="javascript:;"> {{ $t('下线') }} </a>
                </li>
              </template>
                            
              <template v-if="props.row.deletable">
                <li>
                  <a href="javascript:;" @click.stop.prevent="handleDeleteStage(props.row)"> {{ $t('删除') }} </a>
                </li>
              </template>
              <template v-else>
                <li class="disabled" v-bk-tooltips.left="{ content: props.row.status ? $t('环境下线后，才能删除') : $t('内置环境，不允许删除'), boundary: 'window' }">
                  <a href="javascript:;"> {{ $t('删除') }} </a>
                </li>
              </template>
            </ul>
          </bk-dropdown-menu>
        </template>
      </bk-table-column>
    </bk-table>

    <bk-dialog
      v-model="offlineDialogConf.visiable"
      theme="primary"
      :width="525"
      :loading="isOfflineLoading"
      :title="`${$t('确定要下线环境')}【${curStage.name}】？`"
      :mask-close="true"
      @cancel="offlineDialogConf.visiable = false"
      @confirm="offlineStage">
      <p class="p10"> {{ $t('环境下线后，该环境下所发布的API资源将不可访问，可能会影响相当一部分应用和用户。请确保已经告知用户，或者确认需要强制下线') }} </p>
    </bk-dialog>

    <bk-dialog v-model="deleteDialogConf.visiable"
      theme="primary"
      :width="525"
      :title="`${$t('确定要删除环境')}【${curStage.name}】？`"
      :mask-close="true"
      @cancel="deleteDialogConf.visiable = false"
      @confirm="removeStage">
      <p class="p10"> {{ $t('环境删除后，将删除该环境相关配置，不可恢复，请确认删除') }} </p>
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
        stageList: [
        ],
        pagination: {
          current: 1,
          count: 0,
          limit: 10
        },
        isOfflineLoading: false,
        stageDialogConf: {
          isLoading: false,
          visiable: false,
          title: this.$t('新建标签')
        },
        curStage: {
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
              trigger: 'blur'
            }
          ]
        },
        offlineDialogConf: {
          visiable: false
        },
        deleteDialogConf: {
          visiable: false
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
      curApigwFeature () {
        return this.$store.state.curApigw
      },
      stageFlagState () {
        if (!this.curApigwFeature.feature_flags) return false
        return this.curApigwFeature.feature_flags && this.curApigwFeature.feature_flags.ACCESS_STRATEGY_ENABLED
      },
      plugInFlagState () {
        if (!this.curApigwFeature.feature_flags) return false
        return this.curApigwFeature.feature_flags && this.curApigwFeature.feature_flags.PLUGIN_ENABLED
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
        this.getApigwStages()
      },

      async getApigwStages (page) {
        const apigwId = this.apigwId
        const curPage = page || this.pagination.current
        const pageParams = {
          limit: this.pagination.limit,
          offset: this.pagination.limit * (curPage - 1),
          name: this.keyword
        }

        this.isDataLoading = true
        try {
          const res = await this.$store.dispatch('stage/getApigwStages', { apigwId, pageParams })
          res.data.results.forEach(item => {
            item.release_time = item.release_time || '--'
            item.resource_version_name = item.resource_version_name || '--'
          })
          this.stageList = res.data.results
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
        this.getApigwStages(this.pagination.current)
      },

      handlePageChange (newPage) {
        this.pagination.current = newPage
        this.getApigwStages(newPage)
      },

      handleCreateStage () {
        this.$router.push({
          name: 'apigwStageCreate'
        })
      },

      handleCancel () {
        this.clearStageForm()
      },

      clearStageForm () {
        this.curStage.name = ''
        delete this.curStage.id
        this.$refs.stageForm.formItems.forEach(item => {
          item.validator = {
            state: '',
            content: ''
          }
        })
      },

      async addStage () {
        try {
          const data = { name: this.curStage.name }
          const apigwId = this.apigwId
          await this.$store.dispatch('stage/addApigwStage', { apigwId, data })
          this.stageDialogConf.visiable = false
          this.clearStageForm()
          this.getApigwStages()
          this.$bkMessage({
            theme: 'success',
            message: this.$t('新建成功！')
          })
        } catch (e) {
          catchErrorHandler(e, this)
        }
      },

      async updateStage () {
        try {
          const data = { name: this.curStage.name }
          const apigwId = this.apigwId
          const stageId = this.curStage.id
          await this.$store.dispatch('stage/updateApigwStage', { apigwId, stageId, data })
          this.stageDialogConf.visiable = false
          this.clearStageForm()
          this.getApigwStages()

          this.$bkMessage({
            theme: 'success',
            message: this.$t('更新成功！')
          })
        } catch (e) {
          catchErrorHandler(e, this)
        }
      },

      async offlineStage () {
        this.isOfflineLoading = true
        try {
          const apigwId = this.apigwId
          const stageId = this.curStage.id
          const data = { status: 0 }

          await this.$store.dispatch('stage/updateApigwStageStatus', { apigwId, stageId, data })

          this.$bkMessage({
            theme: 'success',
            message: this.$t('下线成功！')
          })
          this.curStage.status = 0
          this.getApigwStages()
          this.offlineDialogConf.visiable = false
        } catch (e) {
          catchErrorHandler(e, this)
        } finally {
          this.isOfflineLoading = false
        }
      },

      async removeStage () {
        try {
          const apigwId = this.apigwId
          const stageId = this.curStage.id
          await this.$store.dispatch('stage/deleteApigwStage', { apigwId, stageId })
          // 当前页只有一条数据
          if (this.stageList.length === 1 && this.pagination.current > 1) {
            this.pagination.current--
          }
          this.getApigwStages()

          this.$bkMessage({
            theme: 'success',
            message: this.$t('删除成功！')
          })
        } catch (e) {
          catchErrorHandler(e, this)
        }
      },

      handleSearch (event) {
        console.log(event)
        this.getApigwStages()
      },

      handleRename (data) {
        this.curStage = JSON.parse(JSON.stringify(data))
        this.stageDialogConf.title = this.$t('重命名标签')
        this.stageDialogConf.visiable = true
      },

      handleEditStage (data) {
        this.$router.push({
          name: 'apigwStageEdit',
          params: {
            id: this.apigwId,
            stageId: data.id
          }
        })
      },

      handleOfflineStage (data) {
        if (!data.status) {
          return false
        }
        this.curStage = data
        this.offlineDialogConf.visiable = true
      },

      handleRelease (data) {
        this.$router.push({
          name: 'apigwVersionCreate',
          params: {
            id: this.apigwId
          },
          query: {
            from: 'apigwStage',
            stageId: data.id
          }
        })
      },

      handleDeleteStage (data) {
        if (!data.deletable) {
          return false
        }

        this.curStage = data
        this.deleteDialogConf.visiable = true
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
