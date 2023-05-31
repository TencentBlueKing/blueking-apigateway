<template>
  <div class="app-content">
    <div class="ag-top-header">
      <bk-button theme="primary" class="mr5" @click="handleShowDialog"> {{ $t('生成版本') }} </bk-button>
      <template v-if="selectedList.length > 2">
        <bk-popover :content="$t('一次只能选择两个版本做对比')">
          <bk-button theme="default" class="mr5" disabled> {{ $t('版本对比') }} </bk-button>
        </bk-popover>
      </template>
      <template v-else>
        <bk-button theme="default" class="mr5" @click="handleShowDiffDialog"> {{ $t('版本对比') }} </bk-button>
      </template>
    </div>
    <bk-table
      style="margin-top: 15px;"
      :data="versionList"
      :size="'small'"
      :pagination="pagination"
      v-bkloading="{ isLoading: isDataLoading }"
      v-if="!isPageLoading"
      @select="handlePageSelect"
      @select-all="handlePageSelectAll"
      @page-limit-change="handlePageLimitChange"
      @page-change="handlePageChange">
      <div slot="empty">
        <table-empty
          :keyword="tableEmptyConf.keyword"
          :abnormal="tableEmptyConf.isAbnormal"
          @reacquire="getApigwVersions"
        />
      </div>
      <bk-table-column type="selection" width="60" align="center"></bk-table-column>
      <bk-table-column width="250" :label="$t('版本号')" prop="version">
        <template slot-scope="props">
          <template v-if="props.row.version">
            <bk-button class="ag-auto-text" :text="true" @click="handleShowDetail(props.row)">
              {{props.row.version}}
            </bk-button>
          </template>
          <template v-else>
            --
          </template>
        </template>
      </bk-table-column>
      <bk-table-column :label="$t('版本标题')" prop="title" :render-header="$renderHeader">
        <template slot-scope="props">
          <template v-if="props.row.title">
            <span class="ag-auto-text">
              {{props.row.title}}
            </span>
          </template>
          <template v-else>
            --
          </template>
        </template>
      </bk-table-column>
      <bk-table-column :label="$t('发布环境')" :render-header="$renderHeader">
        <template slot-scope="props">
          <template v-if="props.row.released_stages.length">
            <div style="display: inline-block;" v-bk-tooltips.top="props.row.stage_text.join('; ')">
              <span class="ag-label vm" v-for="stage of props.row.released_stages" :key="stage.id">
                {{stage.name}}
              </span>
            </div>
          </template>
          <template v-else>
            --
          </template>
        </template>
      </bk-table-column>
      <bk-table-column width="200" :label="$t('创建时间')" prop="created_time" :render-header="$renderHeader"></bk-table-column>
      <bk-table-column :label="$t('版本说明')" prop="comment" :render-header="$renderHeader">
        <template slot-scope="props">
          <template v-if="props.row.comment">
            <div>
              {{props.row.comment}}
            </div>
          </template>
          <template v-else>
            --
          </template>
        </template>
      </bk-table-column>
      <bk-table-column label="SDK" prop="comment">
        <template slot-scope="props">
          <template v-if="props.row.has_sdk">
            <router-link class="ag-link primary" :to="{ name: 'apigwSdk', params: { id: apigwId }, query: { version: props.row.id, action: 'search' } }" v-bk-tooltips="$t('查看已生成SDK')">
              <span class="ag-dot success vm mr5"></span> {{ $t('已生成') }}
            </router-link>
          </template>
          <template v-else>
            <router-link class="ag-link primary" :to="{ name: 'apigwSdk', params: { id: apigwId }, query: { version: props.row.id, action: 'create' } }" v-bk-tooltips="$t('去生成SDK')">
              <span class="ag-dot default vm mr5"></span> {{ $t('未生成') }}
            </router-link>
          </template>
        </template>
      </bk-table-column>
      <bk-table-column :label="$t('操作')" width="120">
        <template slot-scope="props">
          <bk-button class="mr10" theme="primary" text @click="handleEditDialog(props.row)"> {{ $t('编辑') }} </bk-button>
          <bk-button theme="primary" text @click="handleRelease(props.row)"> {{ $t('发布') }} </bk-button>
          <!-- <bk-button class="ml10" theme="primary" text @click="handleDiff(props.row)" v-bk-tooltips="'默认与当前资源列表做对比'">对比</bk-button> -->
        </template>
      </bk-table-column>
    </bk-table>

    <bk-sideslider
      :is-show.sync="diffSidesliderConf.isShow"
      :title="diffSidesliderConf.title"
      :width="diffSidesliderConf.width"
      :quick-close="true"
      :before-close="handleBeforeClose">
      <div slot="content" class="p20">
        <version-diff ref="versionDiffRef" :apigw-id="apigwId" :source-id="diffSourceId" :target-id="diffTargetId" :version-list="versionList"></version-diff>
      </div>
    </bk-sideslider>

    <bk-sideslider
      :is-show.sync="detailSidesliderConf.isShow"
      :title="detailSidesliderConf.title"
      :quick-close="true"
      :width="1000">
      <div slot="header">
        <div class="ag-version-title fl">
          {{curVersion.name}}
        </div>
        <div class="ag-version-metedata fr">
          <div class="item">
            <span class="key"> {{ $t('生成时间：') }} </span>
            <span class="value">{{curVersion.created_time}}</span>
          </div>
          <div class="item">
            <span class="key"> {{ $t('创建者：') }} </span>
            <span class="value">{{curVersion.created_by}}</span>
          </div>
        </div>
      </div>
      <div slot="content" class="p30" v-bkloading="{ isLoading: isDetailLoading, opacity: 1 }" style="min-height: 250px;">
        <bk-table
          :data="curVersion.data"
          :size="'small'"
          v-if="!isDetailLoading"
          @page-change="handlePageChange">
          <div slot="empty">
            <table-empty empty />
          </div>
          <bk-table-column type="expand" width="30" align="center">
            <div slot-scope="props" class="ag-resource-item">
              <p class="title"> {{ $t('基本信息') }} </p>
              <bk-container class="ag-kv-box" :col="12" :margin="6">
                <bk-row>
                  <bk-col :span="2">
                    <label class="ag-key"> {{ $t('资源名称：') }} </label>
                  </bk-col>
                  <bk-col :span="9">
                    <div class="ag-value">{{props.row.name || '--'}}</div>
                  </bk-col>
                </bk-row>

                <bk-row>
                  <bk-col :span="2">
                    <label class="ag-key"> {{ $t('资源描述：') }} </label>
                  </bk-col>
                  <bk-col :span="9">
                    <div class="ag-value">{{props.row.description || '--'}}</div>
                  </bk-col>
                </bk-row>

                <bk-row>
                  <bk-col :span="2">
                    <label class="ag-key"> {{ $t('标签：') }} </label>
                  </bk-col>
                  <bk-col :span="9">
                    <div class="ag-value">{{props.row.labels || '--'}}</div>
                  </bk-col>
                </bk-row>

                <bk-row class="mb0">
                  <bk-col :span="2">
                    <label class="ag-key"> {{ $t('是否公开：') }} </label>
                  </bk-col>
                  <bk-col :span="9">
                    <div class="ag-value">{{props.row.is_public || '--'}}</div>
                  </bk-col>
                </bk-row>
              </bk-container>

              <p class="title mt20"> {{ $t('IP配置') }} </p>
              <bk-container class="ag-kv-box" :col="12" :margin="6">
                <bk-row>
                  <bk-col :span="2">
                    <label class="ag-key"> {{ $t('IP获取地址：') }} </label>
                  </bk-col>
                  <bk-col :span="9">
                    <div class="ag-value">{{props.row.host || '--'}}</div>
                  </bk-col>
                </bk-row>

                <bk-row>
                  <bk-col :span="2">
                    <label class="ag-key"> {{ $t('路径资源：') }} </label>
                  </bk-col>
                  <bk-col :span="9">
                    <div class="ag-value">{{props.row.description || '--'}}</div>
                  </bk-col>
                </bk-row>
              </bk-container>
            </div>
          </bk-table-column>
          <bk-table-column :label="$t('请求路径')" prop="path" :render-header="$renderHeader"></bk-table-column>
          <bk-table-column :label="$t('请求方法')" prop="method" :render-header="$renderHeader"></bk-table-column>
          <bk-table-column :label="$t('描述')">
            <template slot-scope="props">
              {{props.row.description || '--'}}
            </template>
          </bk-table-column>
        </bk-table>
      </div>
    </bk-sideslider>

    <version-create-dialog
      ref="versionCreateDialog"
      :is-new="false"
      @success="handleSuccess">
    </version-create-dialog>

    <version-create-dialog
      ref="versionEditDialog"
      :is-new="false"
      :ok-text="$t('确认')"
      :params="curVersion"
      @success="handleEditSuccess">
    </version-create-dialog>

    <bk-dialog
      v-model="releaseDialogConf.visiable"
      theme="primary"
      :width="566"
      :mask-close="false"
      :header-position="'left'"
      :title="$t('发布版本')"
      :loading="releaseDialogConf.isLoading"
      @confirm="handleSubmitRelease"
      @cancel="handleCancelRelease">
      <bk-form
        style="width: 500px;"
        class="mt20 mb10"
        :label-width="100"
        :model="releaseParams"
        :rules="rules"
        ref="releaseForm">
        <bk-form-item :label="$t('环境')" :property="'stage_id'">
          <bk-select v-model="releaseParams.stage_id" searchable @selected="handleStageSelect">
            <bk-option v-for="option in stageList"
              :key="option.id"
              :id="option.id"
              :name="option.name">
            </bk-option>
          </bk-select>
        </bk-form-item>

        <bk-form-item :label="$t('当前版本')">
          <div class="ag-version-item ">
            <p class="name">{{curStageVersion.resource_version_name || '--'}}</p>
            <p class="comment">{{curStageVersion.comment || '--'}}</p>
          </div>
        </bk-form-item>

        <bk-form-item :label="$t('发布版本')">
          <div class="ag-version-item success">
            <p class="name">{{curVersion.name}}</p>
            <p class="comment">{{curVersion.comment || '--'}}</p>
          </div>
        </bk-form-item>

        <bk-form-item :label="$t('发布日志')">
          <bk-input v-model="releaseParams.comment"></bk-input>
        </bk-form-item>
      </bk-form>
    </bk-dialog>

    <bk-dialog
      v-model="releaseSuccessDialogConf.visiable"
      theme="primary"
      :width="500"
      :mask-close="false"
      :title="$t('生成版本成功')">
      <p class="p10 tc"> {{ $t('生成版本成功后，需要将版本发布到指定环境，才能生效') }} </p>
      <div slot="footer">
        <bk-button class="mr5" theme="primary" @click="handleRelease(releaseSuccessDialogConf.params)"> {{ $t('发布版本') }} </bk-button>
        <bk-button @click="releaseSuccessDialogConf.visiable = false"> {{ $t('确定') }} </bk-button>
      </div>
    </bk-dialog>
  </div>
</template>

<script>
  import { catchErrorHandler } from '@/common/util'
  import versionCreateDialog from '@/components/create-version'
  import versionDiff from '@/components/version-diff'
  import sidebarMixin from '@/mixins/sidebar-mixin'

  export default {
    components: {
      versionCreateDialog,
      versionDiff
    },
    mixins: [sidebarMixin],
    data () {
      return {
        keyword: '',
        isPageLoading: true,
        isDataLoading: false,
        isDetailLoading: false,
        versionList: [],
        stageList: [],
        selectedList: [],
        pagination: {
          current: 1,
          count: 0,
          limit: 10
        },
        sourceVersion: {
          id: '',
          title: '',
          name: ''
        },
        targetVersion: {
          id: '',
          title: '',
          name: ''
        },
        diffSourceId: '',
        diffTargetId: '',
        diffData: {
          add: [],
          delete: [],
          update: []
        },
        detailSidesliderConf: {
          isShow: false
        },
        diffSidesliderConf: {
          isShow: false,
          width: 1040,
          title: this.$t('版本资源对比')
        },
        releaseDialogConf: {
          visiable: false,
          isLoading: false
        },
        releaseSuccessDialogConf: {
          visiable: false
        },
        curStageVersion: {
          resource_version_name: '',
          comment: ''
        },
        versionDialogConf: {
          isLoading: false,
          visiable: false,
          title: this.$t('生成版本')
        },
        versionParams: {
          comment: ''
        },
        releaseParams: {
          stage_id: '',
          comment: ''
        },
        curVersion: {
          name: ''
        },
        rules: {
          stage_id: [
            {
              required: true,
              message: this.$t('必填项'),
              trigger: 'blur'
            }
          ]
        },
        tableEmptyConf: {
          isAbnormal: false,
          keyword: ''
        }
      }
    },
    computed: {
      apigwId () {
        return this.$route.params.id
      }
    },
    created () {
      this.init()
    },
    methods: {
      init () {
        this.getApigwVersions()
        this.getApigwStages()
      },

      async getApigwVersions (page) {
        const apigwId = this.apigwId
        const curPage = page || this.pagination.current
        const pageParams = {
          limit: this.pagination.limit,
          offset: this.pagination.limit * (curPage - 1),
          name: this.keyword
        }

        this.isDataLoading = true
        try {
          const res = await this.$store.dispatch('version/getApigwVersions', { apigwId, pageParams })
          res.data.results.forEach(item => {
            item.stage_text = item.released_stages.map(item => {
              return item.name
            })
          })
          this.versionList = res.data.results
          this.pagination.count = res.data.count
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
        this.getApigwVersions(this.pagination.current)
      },

      handlePageChange (newPage) {
        this.pagination.current = newPage
        this.getApigwVersions(newPage)
      },

      handleShowDialog () {
        this.$refs.versionCreateDialog.show()
      },

      handleDiff (data) {
        this.diffSidesliderConf.width = window.innerWidth <= 1280 ? 1040 : 1280
        this.diffSidesliderConf.isShow = true
        this.sourceVersion = data
        this.diffSourceId = this.sourceVersion.id
        this.diffTargetId = ''
      },

      handleShowDiffDialog () {
        if (this.selectedList.length > 2) {
          return false
        }

        this.diffSidesliderConf.width = window.innerWidth <= 1280 ? 1040 : 1280
        this.diffSidesliderConf.isShow = true
        this.sourceVersion = this.selectedList[0] || ''
        this.targetVersion = this.selectedList[1] || ''
        this.diffSourceId = this.sourceVersion.id
        this.diffTargetId = this.targetVersion.id
        // this.getVersionDiff(sourceId, targetId)
        this.$nextTick(() => {
          if (this.$refs.versionDiffRef) {
            this.initSidebarFormData(this.$refs.versionDiffRef.searchParams || {})
          }
        })
      },

      async getVersionDiff (sourceId, targetId) {
        try {
          const apigwId = this.apigwId
          const res = await this.$store.dispatch('version/getVersionDiff', { apigwId, sourceId, targetId })
          res.data.add.forEach(item => {
            item.isExpanded = false
          })
          res.data.delete.forEach(item => {
            item.isExpanded = false
          })
          res.data.update.forEach(item => {
            item.isExpanded = false
          })
          this.diffData = res.data
        } catch (e) {
          catchErrorHandler(e, this)
        }
      },

      handleEditDialog (data) {
        this.curVersion = JSON.parse(JSON.stringify(data))
        this.$nextTick(() => {
          this.$refs.versionEditDialog.show()
        })
      },

      handleSubmitVersion () {
        this.versionDialogConf.isLoading = true
        this.$refs.versionForm.validate().then(() => {
          this.createVersion()
        }).finally(() => {
          this.$nextTick(() => {
            this.versionDialogConf.isLoading = false
          })
        })
      },

      handleCancel () {
        this.clearVersionForm()
      },

      clearVersionForm () {
        this.versionParams.comment = ''
        this.$refs.versionForm.formItems.forEach(item => {
          item.validator = {
            state: '',
            content: ''
          }
        })
      },

      async createVersion () {
        try {
          const data = { comment: this.versionParams.comment }
          const apigwId = this.apigwId
          await this.$store.dispatch('version/createApigwVersion', { apigwId, data })
          this.versionDialogConf.visiable = false
          this.clearVersionForm()
          this.getApigwVersions()
          this.$bkMessage({
            theme: 'success',
            message: this.$t('版本生成成功！')
          })
        } catch (e) {
          catchErrorHandler(e, this)
        }
      },

      handleSuccess (data) {
        this.getApigwVersions()
        setTimeout(() => {
          this.releaseSuccessDialogConf.params = data
          this.releaseSuccessDialogConf.visiable = true
        }, 500)
      },

      handleEditSuccess (data) {
        this.getApigwVersions()
      },

      async updateVersion () {
        try {
          const data = { name: this.curVersion.name }
          const apigwId = this.apigwId
          const versionId = this.curVersion.id
          await this.$store.dispatch('version/updateApigwVersion', { apigwId, versionId, data })
          this.versionDialogConf.visiable = false
          this.clearVersionForm()
          this.getApigwVersions()

          this.$bkMessage({
            theme: 'success',
            message: this.$t('更新成功！')
          })
        } catch (e) {
          catchErrorHandler(e, this)
        }
      },

      async removeVersion () {
        try {
          const apigwId = this.apigwId
          const versionId = this.curVersion.id
          await this.$store.dispatch('version/deleteApigwVersion', { apigwId, versionId })
          this.getApigwVersions()

          this.$bkMessage({
            theme: 'success',
            message: this.$t('删除成功！')
          })
        } catch (e) {
          catchErrorHandler(e, this)
        }
      },

      async getVersionDetail () {
        try {
          this.isDetailLoading = true
          const apigwId = this.apigwId
          const versionId = this.curVersion.id
          const res = await this.$store.dispatch('version/getApigwVersionDetail', { apigwId, versionId })
          this.curVersion = res.data
        } catch (e) {
          catchErrorHandler(e, this)
        } finally {
          setTimeout(() => {
            this.isDetailLoading = false
          }, 1000)
        }
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

      async getVersionByStage (stageId) {
        const apigwId = this.apigwId

        try {
          const res = await this.$store.dispatch('version/getApigwVersionByStage', { apigwId, stageId })
          this.curStageVersion = res.data
        } catch (e) {
          // catchErrorHandler(e, this)
          this.curStageVersion = {
            resource_version_name: '',
            comment: ''
          }
        }
      },

      async createRelease () {
        try {
          const data = {
            stage_id: this.releaseParams.stage_id,
            resource_version_id: this.curVersion.id,
            comment: this.releaseParams.comment
          }
          const apigwId = this.apigwId
          await this.$store.dispatch('version/createApigwRelease', { apigwId, data })
          this.releaseDialogConf.visiable = false
          this.clearReleaseForm()
          this.getApigwVersions()

          this.$bkMessage({
            theme: 'success',
            message: this.$t('发布成功！')
          })
        } catch (e) {
          catchErrorHandler(e, this)
        }
      },

      handleShowDetail (data) {
        // this.detailSidesliderConf.isShow = true
        // this.detailSidesliderConf.title = data.name
        // this.curVersion = data
        // this.getVersionDetail()
        this.$router.push({
          name: 'apigwVersionDetail',
          params: {
            id: this.apigwId,
            versionId: data.id
          }
        })
      },

      handleRelease (data) {
        this.$router.push({
          name: 'apigwVersionCreate',
          params: {
            id: this.apigwId
          },
          query: {
            versionId: data.id,
            from: 'apigwVersion'
          }
        })
      },

      handleStageSelect (stageId) {
        this.getVersionByStage(stageId)
      },

      handlePageSelect (selection, row) {
        this.selectedList = selection
      },

      handlePageSelectAll (selection, row) {
        this.selectedList = selection
      },

      handleSubmitRelease () {
        this.releaseDialogConf.isLoading = true
        this.$refs.releaseForm.validate().then(() => {
          this.createRelease()
        }).finally(() => {
          this.$nextTick(() => {
            this.releaseDialogConf.isLoading = false
          })
        })
      },

      handleCancelRelease () {
        this.releaseDialogConf.visiable = false
        this.clearReleaseForm()
      },

      clearReleaseForm () {
        this.releaseParams.comment = ''
        this.releaseParams.stage_id = ''
        this.curStageVersion = {
          resource_version_name: '',
          comment: ''
        }
        this.$refs.releaseForm.formItems.forEach(item => {
          item.validator = {
            state: '',
            content: ''
          }
        })
      },

      async handleBeforeClose () {
        return this.$isSidebarClosed(JSON.stringify(this.$refs.versionDiffRef.searchParams || {}))
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
