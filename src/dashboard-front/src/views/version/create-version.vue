<template>
  <div class="app-content">
    <div v-if="latestRelease.status" class="bk-alert mb10" :class="{ 'bk-alert-info': latestRelease.status !== 'failure', 'bk-alert-error': latestRelease.status === 'failure' }">
      <div class="bk-alert-wraper">
        <i class="bk-icon icon-info"></i>
        <div class="bk-alert-content">
          <div class="bk-alert-title">
            <strong> {{ $t('最近发布：') }} </strong>
            {{ $t('环境') }}【{{latestRelease.stage_names.join(', ')}}】，
            {{ $t('版本') }} <strong>{{latestRelease.resource_version_display}}</strong> ，
            <!-- {{ $t('由') }} {{latestRelease.created_by}} {{ $t('于') }} {{latestRelease.created_time}} {{ $t('发布') }}， -->
            {{ latestReleaseText }}
            <template v-if="latestRelease.status === 'success'">
              <span class="ag-success"> {{ $t('发布成功') }} </span>，
            </template>
            <template v-else-if="latestRelease.status === 'pending'">
              <span class="ag-primary"> {{ $t('待发布') }} </span>，
            </template>
            <template v-else-if="latestRelease.status === 'releasing'">
              <span class="ag-primary"> {{ $t('发布中') }} </span>，
            </template>
            <template v-else>
              <span class="ag-danger"> {{ $t('发布失败') }} </span>，
            </template>
            <router-link class="ag-link primary" :to="{ name: 'apigwReleaseHistory', params: { id: apigwId } }"> {{ $t('查看详情') }} </router-link>
          </div>
          <div class="bk-alert-description"></div>
        </div>
      </div>
    </div>
    <bk-form
      style="width: 750px;"
      class="mt20 mb10"
      :label-width="160"
      :model="releaseParams"
      :rules="rules"
      ref="releaseForm">
      <bk-form-item :label="$t('环境')" :property="'stage_ids'" :required="true" :error-display-type="'normal'">
        <bk-select
          v-model="releaseParams.stage_ids"
          :searchable="true"
          :show-select-all="true"
          :clearable="false"
          :multiple="true"
          :disabled="isFromStage">
          <bk-option v-for="option in stageList"
            :key="option.id"
            :id="option.id"
            :name="option.name">
          </bk-option>
        </bk-select>
        <span slot="tip" class="ag-tip f12 vm" style="margin-bottom: -10px;">
          <i class="apigateway-icon icon-ag-info"></i>
          {{ $t('发布前，可在') }}
          <router-link class="ag-text-link" target="_blank" :to="{ name: 'apigwStage', params: { id: apigwId } }"> {{ $t('环境管理') }} </router-link>
          {{ $t('检查网关环境的环境变量、代理配置是否正确') }}
        </span>
      </bk-form-item>

      <bk-form-item :label="$t('当前版本')">
        <template v-if="releaseParams.stage_ids.length">
          <template v-if="stageReleases.length">
            <bk-table
              :data="stageReleases"
              :size="'small'">
              <div slot="empty">
                <table-empty empty />
              </div>
              <bk-table-column width="120" :label="$t('环境')" prop="name"></bk-table-column>
              <bk-table-column :label="$t('当前版本')" prop="resource_version_name" :render-header="$renderHeader">
                <template slot-scope="props">
                  <span v-if="props.row.resource_version_name">
                    {{props.row.resource_version_display || '--'}}
                  </span>
                  <span v-else>--</span>
                </template>
              </bk-table-column>
              <bk-table-column width="170" :label="$t('发布时间')" prop="release_time" :render-header="$renderHeader">
                <template slot-scope="props">
                  {{props.row.release_time || '--'}}
                </template>
              </bk-table-column>
              <bk-table-column width="80" :label="$t('操作')">
                <template slot-scope="props">
                  <bk-popover :content="!props.row.resource_version_name ? $t('当前环境未发布') : (releaseParams.resource_version_id ? $t('默认与发布版本对比') : $t('请先选择发布版本'))">
                    <bk-button :text="true" theme="primary" :disabled="!props.row.resource_version_name || !releaseParams.resource_version_id" @click="handleShowDiff(props.row)"> {{ $t('对比') }} </bk-button>
                  </bk-popover>
                </template>
              </bk-table-column>
            </bk-table>
          </template>
          <template v-else>
            <span class="ag-tip f12 vm" style="line-height: 30px;">
              <i class="apigateway-icon icon-ag-info"></i> {{ $t('当前环境未发布') }} </span>
          </template>
        </template>
        <template v-else>
          <span class="ag-tip f12 vm" style="line-height: 30px;">
            <i class="apigateway-icon icon-ag-info"></i> {{ $t('请选择环境') }} </span>
        </template>
      </bk-form-item>

      <bk-form-item :label="$t('发布版本')" :property="'resource_version_id'" :required="true" :error-display-type="'normal'">
        <bk-select
          v-model="releaseParams.resource_version_id"
          searchable
          :disabled="$route.query.versionId"
          @selected="handleVersionSelect">
          <bk-option v-for="option in versionList"
            :key="option.id"
            :id="option.id"
            :name="option.displayName">
          </bk-option>
        </bk-select>
        <bk-button theme="primary" class="create-btn" @click="handleCreate" :disabled="$route.query.versionId"> {{ $t('生成版本') }} </bk-button>
        <span slot="tip" class="ag-tip f12 vm" style="margin-bottom: -10px;">
          <i class="apigateway-icon icon-ag-info"></i>
          {{ $t('版本发布到环境后，版本中的资源及资源文档更新才会生效') }}
        </span>
      </bk-form-item>

      <bk-form-item :label="$t('发布日志')" :required="true" :property="'comment'" :error-display-type="'normal'">
        <bk-input type="textarea" v-model="releaseParams.comment"></bk-input>
      </bk-form-item>

      <bk-form-item>
        <template v-if="curApigw.status === 1">
          <bk-button
            class="mr10"
            theme="primary"
            type="button"
            :title="$t('提交')"
            @click.stop.prevent="handleSubmitRelease">
            {{ $t('发布') }}
          </bk-button>
        </template>
        <template v-else>
          <bk-popover :content="$t('网关已停用，不可发布')">
            <bk-button
              class="mr10"
              theme="primary"
              type="button"
              :title="$t('提交')"
              :disabled="true">
              {{ $t('发布') }}
            </bk-button>
          </bk-popover>
        </template>

        <bk-button
          theme="default"
          type="button"
          :title="$t('重置')"
          @click="handleReset">
          {{ $t('重置') }}
        </bk-button>
      </bk-form-item>
    </bk-form>

    <bk-dialog
      v-model="confirmConf.isShow"
      ext-cls="bk-info-box"
      theme="primary"
      :name="'bk-info-box'"
      :width="600"
      :title="confirmConf.title"
      :loading="isDataLoading"
      :mask-close="true"
      :confirm-fn="createRelease">
      <p class="pb15" style="line-height: 24px;" v-html="bodyInfo">
      </p>
    </bk-dialog>

    <bk-dialog
      v-model="statusDialogConf.isShow"
      ext-cls="bk-info-box"
      theme="primary"
      :name="'bk-info-box'"
      :show-footer="false"
      :mask-close="true"
      :width="600">
      <template>
        <div class="status-box">
          <template v-if="statusDialogConf.code === 0">
            <div class="icon-wrapper">
              <i v-if="statusDialogConf.params.status === 'success'" class="bk-icon bk-dialog-mark success icon-check-1 icon"></i>
              <i v-else class="bk-icon bk-dialog-mark primary icon-check-1 icon"></i>
            </div>
            <div class="title">{{$t(statusDialogConf.params.message)}}</div>
          </template>
          <template v-else>
            <div class="icon-wrapper">
              <i class="bk-icon bk-dialog-mark danger icon-close icon"></i>
            </div>
            <div class="title"> {{ $t('发布失败') }} </div>
          </template>
          <div class="detail">
            <template v-if="statusDialogConf.code === 0">
              <p> {{ $t('环境') }} <strong style="color: #63656E;">{{statusDialogConf.params.stage_names.join(', ') || '--'}}</strong>
                {{statusDialogConf.params.message}}，
                <span v-if="statusDialogConf.params.status === 'success'"> {{ $t('环境下资源已经可以访问') }} </span>
                <span v-else> {{ $t('待发布成功后，环境下资源可访问') }} </span>
              </p>
              <p>
                <strong> {{ $t('发布版本：') }} </strong>{{statusDialogConf.params.resource_version_display || '--'}}
              </p>
              <p>
                <strong> {{ $t('发布时间：') }} </strong>{{statusDialogConf.params.created_time}}
              </p>
              <div class="links">
                <p> {{ $t('你可能想进行以下操作：') }} </p>
                <ul>
                  <li>
                    <router-link target="_blank" :to="{ name: 'apigwTest', params: { id: apigwId } }"> {{ $t('在线调试 API 资源') }} </router-link>
                  </li>
                  <li>
                    <a v-if="curApigw.is_public" :href="curApigw.docs_url" target="_blank;"> {{ $t('查看 API 文档') }} </a>
                    <span v-else v-bk-tooltips.top="$t('网关未公开，不提供在线 API 文档')">
                      <bk-button text :disabled="true"> {{ $t('查看 API 文档') }} </bk-button>
                    </span>
                  </li>
                  <li>
                    <router-link target="_blank" :to="{ name: 'apigwPermission', params: { id: apigwId } }"> {{ $t('为蓝鲸应用主动授权') }} </router-link>
                  </li>
                  <li>
                    <router-link target="_blank" :to="{ name: 'apigwSdk', params: { id: apigwId } }"> {{ $t('生成 API 资源 SDK') }} </router-link>
                  </li>
                </ul>
              </div>
            </template>
            <template v-else>
              <p>
                {{statusDialogConf.message}}
              </p>
            </template>
          </div>
        </div>
      </template>
    </bk-dialog>

    <version-create-dialog
      ref="versionCreateDialog"
      :is-new="false"
      @success="handleCreateSuccess">
    </version-create-dialog>

    <bk-sideslider
      :is-show.sync="diffSidesliderConf.isShow"
      :title="diffSidesliderConf.title"
      :width="diffSidesliderConf.width"
      :quick-close="true">
      <div slot="content" class="p20">
        <version-diff
          ref="versionDiffRef"
          :apigw-id="apigwId"
          :source-id="diffSourceId"
          :target-id="releaseParams.resource_version_id"
          :source-tag="diffSidesliderConf.sourceTag"
          :target-tag="diffSidesliderConf.targetTag"
          :source-switch="false"
          :cur-diff-enabled="false">
        </version-diff>
      </div>
    </bk-sideslider>
  </div>
  <!-- <div class="app-container">
        <div :class="['app-header', { 'center': !apigwId }]">
            <div class="wrapper">
                <i class="apigateway-icon icon-ag-return-small" @click="goBack" v-if="$route.query.from"></i>
                版本发布
            </div>
        </div>
    </div> -->
</template>

<script>
  import { catchErrorHandler } from '@/common/util'
  import versionCreateDialog from '@/components/create-version'
  import versionDiff from '@/components/version-diff'

  export default {
    components: {
      versionCreateDialog,
      versionDiff
    },
    data () {
      return {
        isPageLoading: false,
        isDataLoading: false,
        isFromResource: false,
        curStage: [],
        releaseVersion: '',
        releaseParams: {
          stage_ids: [],
          resource_version_id: '',
          comment: ''
        },
        diffSourceId: '',
        diffSidesliderConf: {
          isShow: false,
          width: 1040,
          title: this.$t('版本资源对比'),
          sourceTag: this.$t('当前版本'),
          targetTag: this.$t('可发布版本')
        },
        isFromStage: false,
        isFromVersion: false,
        stageList: [],
        versionList: [],
        curStageVersion: {
          resource_version_name: '',
          comment: ''
        },
        stageReleases: [],
        curVersion: {
          title: '',
          name: '',
          comment: ''
        },
        confirmConf: {
          isShow: false,
          title: this.$t('版本发布')
        },
        statusDialogConf: {
          code: 0,
          isShow: false,
          params: {
            stage_names: [],
            resource_version_name: '',
            resource_version_title: '',
            created_time: ''
          },
          message: ''
        },
        rules: {
          stage_ids: [
            {
              required: true,
              message: this.$t('请选择环境'),
              trigger: 'blur'
            }
          ],
          resource_version_id: [
            {
              required: true,
              message: this.$t('请选择版本'),
              trigger: 'blur'
            }
          ],
          comment: [
            {
              required: true,
              message: this.$t('请填写发布日志'),
              trigger: 'blur'
            }
          ]
        },
        latestRelease: {
          comment: '',
          created_by: '',
          created_time: '',
          message: '',
          resource_version_comment: '',
          resource_version_name: '',
          resource_version_title: '',
          stage_name: '',
          stage_names: [],
          status: ''
        }
      }
    },
    computed: {
      apigwId () {
        if (this.$route.params.id !== undefined) {
          return this.$route.params.id
        } else {
          return undefined
        }
      },
      curApigw () {
        return this.$store.state.curApigw
      },
      curVersionName () {
        return `${this.curStageVersion.resource_version_title || '--'} (${this.curStageVersion.resource_version_name || '--'})`
      },
      stageReleaseIds () {
        return this.stageReleases.map(item => item.resource_version_name)
      },
      latestReleaseText () {
        return this.$t(`由 {createdBy} 于 {createdTime} 发布`, { createdBy: this.latestRelease.created_by, createdTime: this.latestRelease.created_time })
      },
      bodyInfo () {
        return this.$t(`环境【{curStage}】将发布版本 {releaseVersion}，当前版本将被覆盖，发布后，环境下新版本的资源可被访问。`, { curStage: this.curStage.join(', '), releaseVersion: this.releaseVersion })
      }
    },
    watch: {
      '$route' () {
        this.init()
      },
      'releaseParams.stage_ids' (ids) {
        this.curStage = this.stageList.filter(item => ids.includes(item.id)).map(item => item.name)
        if (ids && ids.length) {
          this.getVersionByStage(ids)
        }
      }
    },
    created () {
      this.init()
    },
    methods: {
      init () {
        this.getApigwStages()
        this.getApigwVersions()
        this.getApigwLatestRelease()

        // 从环境列表过来
        if (this.$route.query.stageId) {
          const stageId = this.$route.query.stageId
          this.releaseParams.stage_ids = [stageId]
          this.isFromStage = true
          this.getVersionByStage([stageId])
        }

        // 从版本列表过来
        if (this.$route.query.versionId) {
          this.releaseParams.resource_version_id = this.$route.query.versionId
          this.isFromVersion = true
        }
        // 从资源列表过来
        this.$route.meta.parentRoute = this.$route.query.from
        if (this.$route.query.from === 'apigwResource') {
          this.isFromResource = true
          this.$route.meta.parentRoute = 'apigwResource'
        }
      },

      goBack () {
        history.go(-1)
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

          // 从环境列表过来
          if (this.$route.query.stageId && this.stageList.length) {
            const result = this.stageList.find(item => String(item.id) === String(this.$route.query.stageId))
            if (result) {
              this.curStage = [result.name]
            }
          }
        } catch (e) {
          catchErrorHandler(e, this)
        }
      },

      async getApigwLatestRelease (page) {
        const apigwId = this.apigwId

        try {
          const res = await this.$store.dispatch('version/getApigwVersionLatest', { apigwId })
          this.latestRelease = res.data
        } catch (e) {
          catchErrorHandler(e, this)
        }
      },

      async getApigwVersions (page) {
        const apigwId = this.apigwId
        const pageParams = {
          no_page: true
        }

        try {
          const res = await this.$store.dispatch('version/getApigwVersions', { apigwId, pageParams })
          res.data.results.forEach(item => {
            item.displayName = `${item.resource_version_display || '--'}`
          })
          this.versionList = res.data.results

          // 如果从资源跳过来，默认选中最新
          if (this.$route.query.from === 'apigwResource' && this.versionList.length) {
            this.releaseParams.resource_version_id = this.versionList[0].id
            this.releaseVersion = this.versionList[0].displayName
          }

          // 从版本过来
          if (this.$route.query.versionId && this.versionList.length) {
            const result = this.versionList.find(item => String(item.id) === String(this.$route.query.versionId))
            if (result) {
              this.releaseVersion = result.displayName
            }
          }
        } catch (e) {
          catchErrorHandler(e, this)
        } finally {
          this.isPageLoading = false
          this.$store.commit('setMainContentLoading', false)
        }
      },

      async getVersionByStage (stageIds) {
        const apigwId = this.apigwId
        try {
          const res = await this.$store.dispatch('version/getApigwVersionByStages', { apigwId, stageIds })
          this.stageReleases = res.data
        } catch (e) {
          this.stageReleases = []
        }
      },

      handleVersionSelect (versionId, data) {
        this.releaseVersion = data.name
        this.curVersion = this.versionList.find(item => {
          return item.id === versionId
        })
      },

      handleSubmitRelease () {
        const release = this.stageReleases.find(item => {
          const name = `${item.resource_version_title || '--'} (${item.resource_version_name || '--'})`
          return name === this.releaseVersion
        })
        if (release) {
          this.$bkMessage({
            theme: 'error',
            message: this.$t('当前版本与发布版本一致，不可重复发布')
          })
          return false
        }
        this.$refs.releaseForm.validate().then(() => {
          this.confirmConf.isShow = true
        })
      },

      handleCancelRelease () {
        this.clearReleaseForm()
      },

      clearReleaseForm () {
        this.releaseParams.comment = ''
        this.releaseVersion = ''

        if (!this.isFromStage) {
          this.releaseParams.stage_ids = []
          this.stageReleases = []
        }

        if (!this.isFromVersion) {
          this.releaseParams.resource_version_id = ''
        }
        this.$refs.releaseForm.formItems.forEach(item => {
          item.validator = {
            state: '',
            content: ''
          }
        })
      },

      async createRelease () {
        if (this.isDataLoading) {
          return false
        }
        this.isDataLoading = true
        try {
          const data = this.releaseParams
          const apigwId = this.apigwId
          const res = await this.$store.dispatch('version/createApigwReleases', { apigwId, data })
          this.refresh()

          this.statusDialogConf.code = res.code
          this.statusDialogConf.params = res.data
        } catch (e) {
          this.statusDialogConf.code = 400
          this.statusDialogConf.message = e.message
        } finally {
          this.isDataLoading = false
          this.confirmConf.isShow = false
          setTimeout(() => {
            this.statusDialogConf.isShow = true
          }, 500)
          this.getApigwLatestRelease()
        }
      },

      refresh () {
        this.clearReleaseForm()
        if (this.isFromStage) {
          const stageId = this.$route.query.stageId
          this.getVersionByStage([stageId])
        }
      },

      handleCreate () {
        this.$refs.versionCreateDialog.show()
      },

      async handleCreateSuccess () {
        this.$refs.releaseForm.clearError()
        await this.getApigwVersions()
        // 默认选中最新
        if (this.versionList.length) {
          this.releaseParams.resource_version_id = this.versionList[0].id
          this.releaseVersion = this.versionList[0].displayName
        }
      },

      handleReset () {
        this.clearReleaseForm()
      },

      handleShowDiff (data) {
        this.diffSidesliderConf.width = window.innerWidth <= 1280 ? 1040 : 1280
        this.diffSidesliderConf.sourceTag = `${this.$t('环境 ')}${data.name}${this.$t('当前版本')}`
        this.diffSidesliderConf.isShow = true
        this.diffSourceId = data.resource_version_id
      }
    }
  }
</script>

<style lang="postcss" scoped>
    @import '@/css/variable.css';

    .create-btn {
        position: absolute;
        right: -100px;
        top: 0;
    }
    .status-box {
        padding: 0 20px;
        .icon-wrapper {
            text-align: center;
            margin-bottom: 10px;
        }

        .icon {
            width: 58px;
            height: 58px;
            line-height: 58px;
            font-size: 30px;
            color: #fff;
            border-radius: 50%;
            display: inline-block;

            &.success {
                background-color: #2dcb56;
            }

            &.danger {
                background-color: #ea3636;
            }

            &.primary {
                background-color: #3c96ff;
            }
        }

        .title {
                display: inline-block;
                width: 100%;
                font-size: 24px;
                color: #313238;
                overflow: hidden;
                text-overflow: ellipsis;
                white-space: nowrap;
                line-height: 1.5;
                margin: 0;
                text-align: center;
        }

        p {
            font-size: 14px;
            margin-block: 10px;
        }

        .links {
            padding: 15px;
            background: #FAFBFD;
            margin-top: 20px;

            p {
                font-size: 13px;
                color: #63656E;
                margin-bottom: 15px;
            }

            ul {
                overflow: hidden;
                li {
                    float: left;
                    width: 220px;
                    text-align: left;
                    padding-left: 15px;
                    position: relative;
                    margin-bottom: 5px;

                    &:before {
                        content: '●';
                        font-size: 12px;
                        position: absolute;
                        left: 0;
                        transform: scale(0.4);
                        display: inline-block;
                        color: #3A84FF;
                    }

                    a {
                        color: #3A84FF;
                    }
                }
            }
        }
    }
    .ag-tip .apigateway-icon {
        margin-right: 0;
    }
</style>
