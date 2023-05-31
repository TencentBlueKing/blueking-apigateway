<template>
  <div class="zan-box" :key="renderKey">
    <template v-if="isActived">
      <div class="tip-box">
        <i class="bk-icon icon-check-circle"></i> {{ $t('提交成功！非常感谢您的反馈，我们会继续努力做到更好！') }}
      </div>
    </template>
    <template v-else>
      <p class="tip"> {{ $t('文档对你是否有帮助？') }} </p>
      <bk-button class="zan-btn mr10" :class="{ actived: isActived }" theme="primary" :outline="true" @click="handleZan">
        <i class="ag-doc-icon doc-zan apigateway-icon icon-ag-zan"></i> {{ $t('点赞') }}
      </bk-button>
      <bk-button class="zan-btn flip" theme="primary" :outline="true" @click="handleFeedback">
        <i class="ag-doc-icon doc-zan flip apigateway-icon icon-ag-zan"></i> {{ $t('没帮助') }}
      </bk-button>
    </template>

    <bk-dialog
      width="680"
      v-model="rebackDialogConf.visible"
      theme="primary"
      :mask-close="false"
      :header-position="'left'"
      :loading="isFeedbackLoading"
      :title="$t('问题反馈')"
      @cancel="handleCancelFeedback"
      @confirm="feedback">
      <bk-form :label-width="100" :model="formData">
        <bk-form-item :label="$t('问题类型：')" :required="true">
          <bk-checkbox-group v-model="rebackParams.questionType">
            <bk-checkbox :label="$t('内容不完整')" class="mr40">
              {{ $t('内容不完整') }}
            </bk-checkbox>
            <bk-checkbox :label="$t('内容未更新')" class="mr40">
              {{ $t('内容未更新') }}
            </bk-checkbox>
            <bk-checkbox :label="$t('描述不清楚')" class="mr40">
              {{ $t('描述不清楚') }}
            </bk-checkbox>
            <bk-checkbox :label="$t('描述有错误')" class="mr40">
              {{ $t('描述有错误') }}
            </bk-checkbox>
          </bk-checkbox-group>
        </bk-form-item>
        <bk-form-item :label="$t('意见反馈：')" :required="true">
          <bk-input type="textarea" v-model="rebackParams.desc" :placeholder="$t('请输入您的建议或问题')"></bk-input>
        </bk-form-item>
      </bk-form>
    </bk-dialog>
  </div>
</template>

<script>
  import { catchErrorHandler } from '@/common/util'

  export default {
    data () {
      return {
        isActived: false,
        renderKey: 0,
        curSideNavId: '',
        isFeedbackLoading: false,
        rebackDialogConf: {
          visible: false
        },
        rebackParams: {
          questionType: '',
          desc: ''
        }
      }
    },
    watch: {
      '$route' () {
        this.renderKey++
        this.isActived = false
      }
    },
    methods: {
      handleFeedback () {
        this.rebackParams = {
          questionType: '',
          desc: ''
        }
        this.rebackDialogConf.visible = true
      },

      handleZan () {
        this.zan()
      },

      async zan () {
        try {
          const params = {
            doc_type: '',
            positive: true,
            link: location.href,
            labels: []
          }

          const routeName = this.$route.name
          const routeParams = this.$route.params
          this.isActived = true

          if (['ComponentAPIDetailDoc'].includes(routeName)) {
            // 组件文档详情页
            params.doc_type = 'component'
            params.related_component = {
              board: routeParams.version,
              system_name: routeParams.id,
              component_name: routeParams.componentId
            }
          } else if (['ComponentAPIDetailIntro'].includes(routeName)) {
            // 组件文档简介页
            params.doc_type = 'component'
            params.related_component = {
              board: routeParams.version,
              system_name: routeParams.id
            }
          } else if (['apigwAPIDetailDoc'].includes(routeName)) {
            // apigw文档详情页
            params.doc_type = 'apigateway'
            params.related_apigateway = {
              api_name: routeParams.apigwId,
              stage_name: routeParams.stage,
              resource_name: routeParams.resourceId
            }
          } else if (['apigwAPIDetailIntro'].includes(routeName)) {
            // apigw文档简介页
            params.doc_type = 'apigateway'
            params.related_apigateway = {
              api_name: routeParams.apigwId
            }
          } else {
            params.doc_type = 'platform'
          }
          await this.$store.dispatch('feedback', params)
        } catch (e) {
          catchErrorHandler(e, this)
        }
      },

      async feedback () {
        this.isFeedbackLoading = true
        if (!this.rebackParams.questionType.length) {
          this.$bkMessage({
            theme: 'error',
            message: this.$t('请选择问题类型')
          })
          this.$nextTick(() => {
            this.isFeedbackLoading = false
          })
          return false
        }
        if (!this.rebackParams.desc) {
          this.$bkMessage({
            theme: 'error',
            message: this.$t('请填写意见反馈')
          })
          this.$nextTick(() => {
            this.isFeedbackLoading = false
          })
          return false
        }
        try {
          const params = {
            doc_type: '',
            positive: true,
            link: location.href,
            labels: this.rebackParams.questionType,
            content: this.rebackParams.desc
          }

          const routeName = this.$route.name
          const routeParams = this.$route.params

          if (['ComponentAPIDetailDoc'].includes(routeName)) {
            // 组件文档详情页
            params.doc_type = 'component'
            params.related_component = {
              board: routeParams.version,
              system_name: routeParams.id,
              component_name: routeParams.componentId
            }
          } else if (['ComponentAPIDetailIntro'].includes(routeName)) {
            // 组件文档简介页
            params.doc_type = 'component'
            params.related_component = {
              board: routeParams.version,
              system_name: routeParams.id
            }
          } else if (['apigwAPIDetailDoc'].includes(routeName)) {
            // apigw文档详情页
            params.doc_type = 'apigateway'
            params.related_apigateway = {
              api_name: routeParams.apigwId,
              stage_name: routeParams.stage,
              resource_name: routeParams.resourceId
            }
          } else if (['apigwAPIDetailIntro'].includes(routeName)) {
            // apigw文档简介页
            params.doc_type = 'apigateway'
            params.related_apigateway = {
              api_name: routeParams.apigwId
            }
          } else {
            params.doc_type = 'platform'
          }
          await this.$store.dispatch('feedback', params)
          this.$bkMessage({
            theme: 'success',
            message: this.$t('反馈成功')
          })
          this.rebackDialogConf.visible = false
          this.isActived = true
        } catch (e) {
          catchErrorHandler(e, this)
        } finally {
          this.isFeedbackLoading = false
        }
      }
    }
  }
</script>

<style lang="postcss" scoped>
    .tip {
        color: #313238;
        font-size: 16px;
        margin-bottom: 20px;
    }

    .zan-btn {
        width: 110px;
        border-radius: 32px;

        .doc-zan {
            margin-right: 3px;
        }

        .flip {
            transform: rotateZ(180deg);
            display: inline-block;
        }
    }
    .bk-button {
        &.actived {
            background-color: #3a84ff;
            border-color: #3a84ff;
            color: #fff;
        }
    }
    .tip-box {
        background-color: #f7f8fa;
        padding: 24px;
        font-size: 14px;
        color: #63656e;
        text-align: center;

        .bk-icon {
            font-size: 40px;
            vertical-align: middle;
            margin-right: 10px;
            color: #2dcb56;
        }
    }
</style>
