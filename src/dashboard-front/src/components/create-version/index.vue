<template>
  <bk-dialog
    v-model="versionDialogConf.visiable"
    theme="primary"
    :width="620"
    :mask-close="false"
    :header-position="'left'"
    :title="versionDialogConf.title"
    :loading="versionDialogConf.isLoading"
    @confirm="handleSubmitVersion"
    @cancel="handleCancel">
    <bk-form
      class="mt20 mb10"
      style="width: 540px;"
      :label-width="100"
      :model="versionParams"
      :rules="rules"
      ref="versionForm">
      <p v-if="versionInfo.version" class="ag-alert primary mb10" style="margin-left: 100px;">
        <i class="apigateway-icon icon-ag-info"></i>
        <span>
          <span>{{ $t('最新版本号:') }}</span>
          <span>{{ versionInfo.version || '--' }}</span>,
          {{ versionText }}
        </span>
      </p>
      <bk-form-item
        :label="$t('版本号')"
        :required="true"
        :property="'version'">
        <bk-input :placeholder="$t('由数字、字母、中折线（-）、点号（.）组成，长度小于64个字符')" :readonly="isReadonly" v-model="versionParams.version"></bk-input>
        <template>
          <div class="ag-alert" style="line-height: 1;">
            <i class="apigateway-icon icon-ag-info"></i>
            &nbsp;{{ $t('版本号需符合 Semver 规范') }}
          </div>
        </template>
      </bk-form-item>
      <bk-form-item :label="$t('版本标题')" :required="true" :property="'title'">
        <bk-input :placeholder="$t('请输入版本标题')" v-model="versionParams.title"></bk-input>
      </bk-form-item>
      <bk-form-item :label="$t('版本说明')">
        <bk-input type="textarea" :placeholder="$t('请输入版本说明')" v-model="versionParams.comment"></bk-input>
        <template v-if="isNew && message">
          <p class="ag-alert warning mt10">
            <i class="apigateway-icon icon-ag-info"></i>
            {{message}}
          </p>
        </template>
        <template v-else>
          <div class="ag-alert primary mt10">
            <i class="apigateway-icon icon-ag-info"></i>
            {{ $t('资源版本，将存储网关当前所有资源的配置，版本需发布到指定环境，才能访问该环境下的资源') }}
          </div>
        </template>
      </bk-form-item>
    </bk-form>
    <div slot="footer">
      <bk-button class="mr5 fl" @click="handleSkip" v-if="isNew"> {{ $t('不生成') }} </bk-button>
      <bk-button class="mr5" theme="primary" @click="handleSubmitVersion" :loading="isDataLoading">{{okText ? okText : $t('生成')}}</bk-button>
      <bk-button @click="handleCancel"> {{ $t('取消') }} </bk-button>
    </div>
  </bk-dialog>
</template>

<script>
  import { catchErrorHandler } from '@/common/util'
  import { bkForm, bkFormItem, bkInput, bkButton, bkDialog } from 'bk-magic-vue'

  export default {
    components: {
      bkDialog,
      bkForm,
      bkFormItem,
      bkInput,
      bkButton
    },
    props: {
      isNew: {
        type: Boolean,
        default: false
      },
      isAutoDirect: {
        type: Boolean,
        default: false
      },
      message: {
        type: String,
        default: ''
      },
      params: {
        type: Object
      },
      title: {
        type: String,
        default: ''
      },
      okText: {
        type: String,
        default: ''
      }
    },
    data () {
      return {
        isDataLoading: false,
        versionParams: {
          title: '',
          comment: '',
          version: ''
        },
        versionDialogConf: {
          isLoading: false,
          visiable: false,
          title: this.$t('生成版本')
        },
        isReadonly: false,
        versionInfo: {},
        rules: {
          title: [
            {
              required: true,
              message: this.$t('请填写版本标题'),
              trigger: 'blur'
            }
          ],
          version: [
            {
              required: true,
              message: this.$t('必填项'),
              trigger: 'blur'
            },
            {
              max: 64,
              message: this.$t('不能多于64个字符'),
              trigger: 'blur'
            },
            {
              validator (value) {
                const reg = /^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:-((?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?(?:\+([0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?$/
                return reg.test(value)
              },
              message: this.$t('由数字、字母、中折线（-）、点号（.）组成，长度小于64个字符，符合 Semver 规范'),
              trigger: 'blur'
            }
          ]
        }
      }
    },
    computed: {
      apigwId () {
        return this.$route.params.id
      },
      versionText () {
        return this.$t(`于 {createdTime} 创建`, { createdTime: this.versionInfo.created_time })
      }
    },

    created () {
      this.getNewVersonInfo()
    },

    methods: {
      handleSubmitVersion () {
        if (this.isDataLoading) {
          return false
        }
        this.versionDialogConf.isLoading = true
        this.$refs.versionForm.validate().then(() => {
          if (this.params) {
            this.updateVersion()
          } else {
            this.createVersion()
          }
        }).finally(() => {
          this.$nextTick(() => {
            this.versionDialogConf.isLoading = false
          })
        })
      },

      async createVersion () {
        this.isDataLoading = true
        try {
          const data = this.versionParams
          const apigwId = this.apigwId
          const res = await this.$store.dispatch('version/createApigwVersion', { apigwId, data })
          this.versionDialogConf.visiable = false
          this.$bkMessage({
            theme: 'success',
            message: this.$t('版本生成成功！')
          })
          this.$emit('success', res.data)
          this.clearVersionForm()
          if (this.isAutoDirect) {
            this.goVersionCreate()
          }
        } catch (e) {
          catchErrorHandler(e, this)
        } finally {
          this.isDataLoading = false
        }
      },

      async updateVersion () {
        this.isDataLoading = true
        try {
          const data = this.versionParams
          const apigwId = this.apigwId
          const versionId = this.versionParams.id
          await this.$store.dispatch('version/updateApigwVersion', { apigwId, versionId, data })
          this.versionDialogConf.visiable = false
          this.$bkMessage({
            theme: 'success',
            message: this.$t('版本更新成功！')
          })
          this.$emit('success')
          this.clearVersionForm()
          if (this.isAutoDirect) {
            this.goVersionCreate()
          }
        } catch (e) {
          catchErrorHandler(e, this)
        } finally {
          this.isDataLoading = false
        }
      },

      async getNewVersonInfo () {
        const apigwId = this.apigwId
        try {
          const res = await this.$store.dispatch('version/getNewVersonInfo', { apigwId })
          this.versionInfo = res.data.results[0] || {}
        } catch (e) {
          catchErrorHandler(e, this)
        }
      },

      show () {
        if (this.params) {
          this.versionParams = this.params
          this.versionDialogConf.title = this.$t('编辑版本')
          this.isReadonly = true
        } else {
          this.versionDialogConf.title = this.title || this.$t('生成版本')
          this.isReadonly = false
        }
        this.versionDialogConf.visiable = true
      },

      goVersionCreate () {
        this.$router.push({
          name: 'apigwVersionCreate',
          params: {
            id: this.apigwId
          },
          query: {
            from: 'apigwResource'
          }
        })
      },

      handleSkip () {
        this.goVersionCreate()
      },

      handleCancel () {
        this.clearVersionForm()
      },

      clearVersionForm () {
        this.versionParams = {
          title: '',
          comment: ''
        }
        this.$refs.versionForm.clearError()
        this.versionDialogConf.visiable = false
      }
    }
  }
</script>

<style scoped lang="postcss">
    @import '../../css/variable.css';
</style>
