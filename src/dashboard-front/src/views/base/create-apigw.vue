<template>
  <div class="app-content">
    <div class="ag-create-header" v-if="!apigwId"> {{ $t('创建网关') }} </div>
    <bk-form ref="form" :label-width="labelWidth" :model="curApigw" :rules="rules" style="width: 800px;" v-show="!isPageLoading">
      <bk-form-item :label="$t('名称')" :required="true" :property="'name'" :error-display-type="'normal'">
        <bk-input
          v-model="curApigw.name"
          :placeholder="$t('由小写字母、数字、连接符（-）组成，首字符必须是字母，长度大于3小于30个字符')"
          :disabled="!!apigwId">
        </bk-input>
        <p slot="tip" class="ag-tip mt5">
          <i class="apigateway-icon icon-ag-info"></i> {{ $t('网关唯一标识，创建后不可修改') }}
        </p>
      </bk-form-item>
      <bk-form-item :label="$t('描述')" :required="true" :property="'description'" :error-display-type="'normal'">
        <bk-input v-model="curApigw.description" :placeholder="$t('请输入描述')"></bk-input>
      </bk-form-item>
      <bk-form-item
        :label="$t('网关状态')"
        :desc="$t('启用，则网关资源可被访问；停用，则网关所有资源不可被访问')"
        :desc-type="'icon'">
        <div class="gateway-wrapper" v-if="!!apigwId">
          <span :class="['status-dot', { 'success': curApigw.statusBoolean }]">
            {{ curApigw.statusBoolean ? $t('已启用') : $t('已停用') }}
          </span>
        </div>
        <bk-switcher theme="primary" v-model="curApigw.statusBoolean" v-else></bk-switcher>
      </bk-form-item>
      <bk-form-item
        :label="$t('是否公开')"
        :desc="$t('公开，则用户可查看资源文档、申请资源权限；不公开，则网关对用户隐藏')"
        :desc-type="'icon'">
        <bk-switcher v-model="curApigw.is_public" theme="primary"></bk-switcher>
      </bk-form-item>
      <bk-form-item :label="$t('维护人员')" :required="true" :property="'maintainers'" :error-display-type="'normal'">
        <user v-model="curApigw.maintainers"></user>
        <p slot="tip" class="ag-tip mt10">
          <i class="apigateway-icon icon-ag-info"></i> {{ $t('仅维护人员有管理网关的权限') }}
        </p>
      </bk-form-item>
      <div class="ag-span"></div>
      <!-- 去除用户类型 -->
      <bk-form-item>
        <bk-button
          class="mr10"
          theme="primary"
          type="button"
          :title="$t('创建')"
          @click.stop.prevent="submitData" :loading="isDataLoading">
          {{apigwId ? $t('保存') : $t('创建')}}
        </bk-button>
        <bk-button
          theme="default"
          type="button"
          :title="$t('取消')"
          @click="goBack">
          {{ $t('取消') }}
        </bk-button>
      </bk-form-item>
    </bk-form>
  </div>
</template>

<script>
  import { catchErrorHandler } from '@/common/util'
  import User from '@/components/user'

  export default {
    components: {
      User
    },
    data () {
      return {
        isPageLoading: true,
        isDataLoading: false,
        curApigw: {
          name: '',
          description: '',
          status: 1,
          statusBoolean: true,
          is_public: true,
          maintainers: []
        },
        rules: {
          name: [
            {
              required: true,
              message: this.$t('请填写名称'),
              trigger: 'blur'
            },
            {
              min: 3,
              message: this.$t('不能小于3个字符'),
              trigger: 'blur'
            },
            {
              max: 30,
              message: this.$t('不能多于30个字符'),
              trigger: 'blur'
            },
            {
              regex: /^[a-z][a-z0-9-]*$/,
              message: this.$t('由小写字母、数字、连接符（-）组成，首字符必须是字母，长度大于3小于30个字符'),
              trigger: 'blur'
            }
          ],
          description: [
            {
              required: true,
              message: this.$t('请填写描述'),
              trigger: 'blur'
            }
          ],
          maintainers: [
            {
              validator (val) {
                return val.length >= 1
              },
              message: this.$t('请选择维护人员'),
              trigger: 'blur'
            }
          ]
        },
        MICRO_GATEWAY_ENABLED: false

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
      curUser () {
        return this.$store.state.user
      },
      localLanguage () {
        return this.$store.state.localLanguage
      },
      labelWidth () {
        return this.localLanguage === 'en' ? 150 : 120
      }
    },
    created () {
      this.init()
      this.getFeature()
    },
    methods: {
      init () {
        this.initCurapigw()
      },

      async getFeature () {
        const res = await this.$store.dispatch('apis/getFeature')
        if (res.code === 0 && res.message === 'OK') {
          this.MICRO_GATEWAY_ENABLED = res.data.MICRO_GATEWAY_ENABLED
        }
      },

      async initCurapigw () {
        if (this.apigwId !== undefined) {
          try {
            const res = await this.$store.dispatch('apis/getApisDetail', this.apigwId)
            this.curApigw = res.data
            this.curApigw.statusBoolean = Boolean(this.curApigw.status)
          } catch (e) {
            catchErrorHandler(e, this)
          } finally {
            this.isPageLoading = false
            this.$store.commit('setMainContentLoading', false)
          }
        } else {
          this.curApigw = {
            name: '',
            description: '',
            status: 1,
            statusBoolean: true,
            is_public: true,
            maintainers: [this.curUser.username]
          }
          this.isPageLoading = false
          this.$store.commit('setMainContentLoading', false)
        }
      },

      goBack () {
        if (this.apigwId !== undefined) {
          this.$router.push({
            name: 'apigwInfo',
            params: {
              id: this.apigwId
            }
          })
        } else {
          this.$router.push({
            name: 'index'
          })
        }
      },

      submitData () {
        if (this.isDataLoading) {
          return false
        }

        this.$refs.form.validate().then(validator => {
          if (this.apigwId !== undefined) {
            this.updateApigw()
          } else {
            this.addApigw()
          }
        }, error => {
          this.$bkMessage({
            theme: 'error',
            message: error.content
          })
        })
      },

      async addApigw () {
        this.isDataLoading = true
        try {
          const params = this.curApigw
          const self = this

          params.status = Number(this.curApigw.statusBoolean)

          const res = await this.$store.dispatch('apis/addApis', params)
          this.$bkMessage({
            theme: 'success',
            message: this.$t('创建成功'),
            delay: 2000,
            async onClose () {
              await self.$store.dispatch('apis/getApisList')
              self.$router.push({
                name: 'apigwResource',
                params: {
                  id: res.data.id
                }
              })
            }
          })
        } catch (e) {
          catchErrorHandler(e, this)
        } finally {
          this.isDataLoading = false
        }
      },

      async updateApigw () {
        this.isDataLoading = true
        try {
          const params = {
            apigwId: this.apigwId,
            data: this.curApigw
          }
          params.data.status = Number(this.curApigw.statusBoolean)

          const self = this
          await this.$store.dispatch('apis/updateApis', params)
          this.$bkMessage({
            theme: 'success',
            message: this.$t('更新成功！'),
            delay: 2000,
            onClose () {
              self.$router.push({
                name: 'apigwInfo',
                params: {
                  id: self.apigwId
                }
              })
            }
          })
        } catch (e) {
          catchErrorHandler(e, this)
        } finally {
          this.isDataLoading = false
        }
      }
    }
  }
</script>

<style lang="postcss" scoped>
    @import '@/css/variable.css';

    .ag-dl {
        padding: 15px 40px 5px 30px;
    }

    .ag-accordion-header {
        .apigateway-icon {
            font-size: 13px;
            color: #c4c6cc;
            vertical-align: middle;
            float: left;
            line-height: 40px;
            margin-right: 12px;
        }
    }
    .ag-create-header {
        margin: 5px auto 25px;
        width: 800px;
        text-align: center;
        font-size: 20px;
        color: #63656e;
        position: relative;
        &:after,
        &:before {
            content: "";
            position: absolute;
            top: 50%;
            background-color: #c4c6cc;
            height: 1px;
            width: 39%;
        }
        &:after {
            left: 0;
        }
        &:before {
            right: 0;
        }
    }
    .en-blank {
        padding-left: 8px;
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
    .gateway-wrapper {
        line-height: 30px;
    }
</style>
