<template>
  <div class="app-content">
    <section style="width: 800px;">
      <bk-alert v-if="!curApigw.statusBoolean" type="warning" class="warning-alert" :title="$t('当前网关已停用，如需使用，请先启用')"></bk-alert>
      <bk-container class="ag-form-info" :col="12">
        <bk-row>
          <bk-col :span="2">
            <div class="ag-form-label"> {{ $t('名称') }} </div>
          </bk-col>
          <bk-col :span="4">
            <div class="ag-form-content">{{curApigw.name}}</div>
          </bk-col>
          <bk-col :span="2">
            <div class="ag-form-label"> {{ $t('创建者') }} </div>
          </bk-col>
          <bk-col :span="4">
            <div class="ag-form-content">{{curApigw.created_by || '--'}}</div>
          </bk-col>
        </bk-row>
        <bk-row>
          <bk-col :span="2">
            <div class="ag-form-label"> {{ $t('描述') }} </div>
          </bk-col>
          <bk-col :span="4">
            <div class="ag-form-content">
              <bk-popover placement="right">
                <p class="ag-field-text" style="max-width: 200px;">{{curApigw.description || '--'}}</p>
                <div slot="content" style="white-space: normal; max-width: 300px;">
                  {{curApigw.description || '--'}}
                </div>
              </bk-popover>
            </div>
          </bk-col>
          <bk-col :span="2">
            <div class="ag-form-label"> {{ $t('创建时间') }} </div>
          </bk-col>
          <bk-col :span="4">
            <div class="ag-form-content">{{curApigw.created_time || '--'}}</div>
          </bk-col>
        </bk-row>
        <bk-row>
          <bk-col :span="2">
            <div class="ag-form-label"> {{ $t('网关状态') }} </div>
          </bk-col>
          <bk-col :span="4">
            <div class="ag-form-content">
              <span :class="['status-dot', { 'success': curApigw.statusBoolean }]">
                {{ curApigw.statusBoolean ? $t('已启用') : $t('已停用') }}
              </span>
            </div>
          </bk-col>
          <bk-col :span="2">
            <div class="ag-form-label"> {{ $t('维护人员') }} </div>
          </bk-col>
          <bk-col :span="4">
            <div class="ag-form-content">
              <bk-popover placement="right">
                <p class="ag-field-text" style="max-width: 200px; margin-top: -3px;">{{curApigw.maintainers.join('; ')}}</p>
                <div slot="content" style="white-space: normal; max-width: 300px;">
                  {{curApigw.maintainers.join('; ')}}
                </div>
              </bk-popover>
            </div>
          </bk-col>
        </bk-row>
        <bk-row>
          <bk-col :span="2">
            <div class="ag-form-label"> {{ $t('是否公开') }} </div>
          </bk-col>
          <bk-col :span="4">
            <div class="ag-form-content">
              <span class="is-public">{{ curApigw.is_public ? $t('是') : $t('否') }}</span>
            </div>
          </bk-col>
          <template v-if="GLOBAL_CONFIG.PLATFORM_FEATURE.GATEWAY_DEVELOPERS_ENABLED">
            <bk-col :span="2">
              <div class="ag-form-label"> {{ $t('开发者') }} </div>
            </bk-col>
            <bk-col :span="4">
              <div class="ag-form-content">
                <bk-popover placement="right" v-if="curApigw.developers && curApigw.developers.length">
                  <p class="ag-field-text" style="max-width: 200px; margin-top: -3px;">{{curApigw.developers.join('; ')}}</p>
                  <div slot="content" style="white-space: normal; max-width: 300px;">
                    {{curApigw.developers.join('; ')}}
                  </div>
                </bk-popover>
                <span v-else>--</span>
              </div>
            </bk-col>
          </template>
        </bk-row>
        <bk-row>
          <bk-col :span="2">
            <div class="ag-form-label"> {{ $t('访问域名') }} </div>
          </bk-col>
          <bk-col :span="10">
            <div class="ag-form-content">
              {{curApigw.domain}}
              <i class="apigateway-icon icon-ag-document ml15 copy-btn" @click="handleCopy(curApigw.domain)"></i>
              <!-- <a :href="curApigw.domain" target="_blank"><i class="apigateway-icon icon-ag-jump ml5"></i></a> -->
            </div>
          </bk-col>
        </bk-row>
        <bk-row>
          <bk-col :span="2">
            <div class="ag-form-label"> {{ $t('文档地址') }} </div>
          </bk-col>
          <bk-col :span="10">
            <div class="ag-form-content">
              <template v-if="curApigw.is_public">
                {{curApigw.docs_url}}
                <i class="apigateway-icon icon-ag-document ml15 copy-btn" @click="handleCopy(curApigw.docs_url)"></i>
                <!-- <a :href="curApigw.docs_url" target="_blank"><i class="apigateway-icon icon-ag-jump ml5"></i></a> -->
              </template>
              <template v-else>
                <span style="color: #dcdee5;"> {{ $t('网关未公开，不提供在线 API 文档') }} </span>
              </template>
            </div>
          </bk-col>
        </bk-row>
      </bk-container>
      <div class="ag-span"></div>
      <bk-container class="ag-form-info" :col="12">
        <bk-row>
          <bk-col :span="2">
            <div class="ag-form-label"> {{ $t('API公钥(指纹)') }} </div>
          </bk-col>
          <bk-col :span="10">
            <div class="ag-form-content">
              <div class="ag-key-value">
                <div class="key">
                  <i class="apigateway-icon icon-ag-lock"></i>
                </div>
                <div class="value">
                  <span class="f14">{{curApigw.public_key_fingerprint}}</span>
                  <bk-button theme="primary" class="fr f12 ml10" :text="true" @click="download"> {{ $t('下载') }} </bk-button>
                  <bk-button theme="primary" class="fr f12 copy-btn" :text="true" @click="handleCopy(curApigw.public_key)"> {{ $t('复制') }} </bk-button>
                </div>
              </div>
            </div>
            <p class="ag-tip mt5">
              <i class="apigateway-icon icon-ag-info"></i>
              {{ $t('可用于解密传入后端接口的请求头 X-Bkapi-JWT') }}，
              <a :href="GLOBAL_CONFIG.DOC.JWT" target="_blank" class="ag-primary"> {{ $t('更多详情') }} </a>
            </p>
          </bk-col>
        </bk-row>
        <bk-row>
          <bk-col :span="10" :offset="2">
            <bk-button theme="primary" class="mr5" style="width: 108px;" @click="editApigw"> {{ $t('编辑') }} </bk-button>
            <template v-if="curApigw.status">
              <bk-button theme="default" class="mr5 stop-btn" @click="toggleApigwStatus"> {{ $t('停用') }} </bk-button>
            </template>
            <template v-else>
              <bk-button theme="default" class="mr5" @click="toggleApigwStatus"> {{ $t('启用') }} </bk-button>
            </template>
            <template v-if="curApigw.statusBoolean">
              <bk-popover :content="$t('请先停用才可删除')">
                <bk-button theme="default" class="mr5" :disabled="curApigw.statusBoolean"> {{ $t('删除') }} </bk-button>
              </bk-popover>
            </template>
            <template v-else>
              <bk-button theme="default" class="mr5" @click="removeApigw"> {{ $t('删除') }} </bk-button>
            </template>
          </bk-col>
        </bk-row>
      </bk-container>
    </section>

    <bk-dialog
      v-model="delApigwDialog.visiable"
      width="540"
      :title="$t(`确认删除网关【{name}】？`, { name: curApigw.name })"
      :theme="'primary'"
      :header-position="'left'"
      :mask-close="false"
      :loading="delApigwDialog.isLoading">
      <div class="ps-form">
        <div class="form-tips" v-html="delTips"></div>
        <div class="mt15">
          <bk-input v-model="formRemoveConfirmApigw"></bk-input>
        </div>
      </div>
      <template slot="footer">
        <bk-button
          theme="primary"
          :disabled="!formRemoveApigw"
          @click="deleteApigw">
          {{ $t('确定') }}
        </bk-button>
        <bk-button
          theme="default"
          @click="delApigwDialog.visiable = false">
          {{ $t('取消') }}
        </bk-button>
      </template>
    </bk-dialog>
  </div>
</template>

<script>
  import { catchErrorHandler } from '@/common/util'

  export default {
    data () {
      return {
        isPageLoading: true,
        curApigw: {
          name: '',
          description: '',
          status: 0,
          statusBoolean: false,
          statusForFe: false,
          is_public: true,
          maintainers: [],
          maintainersForFe: [],
          developers: []
        },
        delApigwDialog: {
          visiable: false,
          isLoading: false
        },
        formRemoveConfirmApigw: ''
      }
    },
    computed: {
      formRemoveApigw () {
        return this.curApigw.name === this.formRemoveConfirmApigw
      },
      delTips () {
        return this.$t(`请完整输入 <code class="gateway-del-tips">{name}</code> 来确认删除网关！`, { name: this.curApigw.name })
      }
    },
    created () {
      this.init()
    },
    methods: {
      init () {
        this.getApigwDetail()
      },

      async getApigwDetail () {
        const apigwId = this.$route.params.id

        try {
          const res = await this.$store.dispatch('apis/getApisDetail', apigwId)
          this.curApigw = res.data
          this.curApigw.statusBoolean = Boolean(this.curApigw.status)
        } catch (e) {
          catchErrorHandler(e, this)
        } finally {
          this.isPageLoading = false
          this.$store.commit('setMainContentLoading', false)
        }
      },

      editApigw () {
        this.$router.push({
          name: 'apigwEdit',
          params: {
            id: this.curApigw.id
          }
        })
      },

      download () {
        const content = this.curApigw.public_key

        const elment = document.createElement('a')
        const blob = new Blob([content], {
          type: 'text/plain'
        })
        elment.download = `bk_apigw_public_key_${this.curApigw.name}.pub`
        elment.href = URL.createObjectURL(blob)
        elment.click()
        URL.revokeObjectURL(blob)
      },

      toggleApigwStatus () {
        const self = this
        let title = this.$t('确认要启用网关？')
        let subTitle = ''
        if (this.curApigw.status) {
          title = this.$t('确认是否停用网关？')
          subTitle = this.$t('网关停用后，网关下所有资源不可访问，请确认是否继续操作？')
        }

        this.$bkInfo({
          title: title,
          subTitle: subTitle,
          confirmFn () {
            self.changeApigwStatus()
          }
        })
      },

      removeApigw () {
        this.delApigwDialog.visiable = true
        this.formRemoveConfirmApigw = ''
      },

      async changeApigwStatus () {
        const apigwId = this.$route.params.id
        const status = this.curApigw.status === 1 ? 0 : 1
        try {
          await this.$store.dispatch('apis/toggleApisStatus', { apigwId, data: { status } })
          this.curApigw.status = status
          this.curApigw.statusBoolean = Boolean(status)
          this.$bkMessage({
            theme: 'success',
            message: this.$t('更新成功')
          })
          this.$store.commit('updateCurApigw', this.curApigw)
        } catch (e) {
          catchErrorHandler(e, this)
        } finally {
          this.isPageLoading = false
          this.$store.commit('setMainContentLoading', false)
        }
      },

      async deleteApigw () {
        const apigwId = this.$route.params.id
        try {
          await this.$store.dispatch('apis/deleteApis', { apigwId, status })
          this.$bkMessage({
            theme: 'success',
            message: this.$t('删除成功')
          })
          this.$router.push({
            name: 'index'
          })
        } catch (e) {
          catchErrorHandler(e, this)
        } finally {
          this.isPageLoading = false
          this.$store.commit('setMainContentLoading', false)
        }
      },

      handleCopy (text) {
        this.$copyText(text).then((e) => {
          this.$bkMessage({
            theme: 'success',
            limit: 1,
            message: this.$t('复制成功')
          })
        }, () => {
          this.$bkMessage({
            theme: 'error',
            limit: 1,
            message: this.$t('复制失败')
          })
        })
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
    .stop-btn {
        &:hover {
            background: $dangerColor;
            border-color: $dangerColor;
            color: #FFF;
        }
    }
    .ps-form {
        font-size: 14px;
        .form-tips code {
            color: #c7254e;
            padding: 3px 4px;
            margin: 0;
            background-color: rgba(0, 0, 0, 0.04);
            border-radius: 3px;
        }
    }
    .status-dot {
        padding: 2px 10px;
        font-size: 12px;
        border-radius: 2px;
        background: #F0F1F5;
        color: #63656E;
    }
    .status-dot.success {
        background: #E4FAF0;
        color: #14A568;
    }
    .is-public {
        color: #FF9C01;
    }
    .warning-alert {
        margin-bottom: 16px;
    }
</style>
<style>
    .gateway-del-tips {
        color: #c7254e;
        padding: 3px 4px;
        margin: 0;
        background-color: rgba(0, 0, 0, 0.04);
        border-radius: 3px;
    }
</style>
