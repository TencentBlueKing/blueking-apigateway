<template>
  <div class="help-doc">
    <ul class="apigw-tool-box">
      <li v-if="GLOBAL_CONFIG.DOC.USER_API">
        <a :href="GLOBAL_CONFIG.DOC.USER_API" target="_blank">
          <div class="icon-wrapper">
            <i class="apigateway-icon icon-ag-help-document-fill doc-help-style icon"></i>
          </div>
          <span class="text"> {{ $t('帮助文档') }} </span>
        </a>
      </li>
      <li v-if="GLOBAL_CONFIG.PLATFORM_FEATURE.ENABLE_FEEDBACK" class="feedback" @click="handleShowReback">
        <a href="javascript: void(0);">
          <i class="apigateway-icon icon-ag-message-fill icon"></i>
          <span class="text"> {{ $t('问题反馈') }} </span>
        </a>
      </li>
    </ul>
    <bk-dialog
      width="680"
      v-model="rebackDialogConf.visible"
      theme="primary"
      :mask-close="false"
      :header-position="'left'"
      :loading="isFeedbackLoading"
      :title="$t('问题反馈')"
      @confirm="handleFeedback">
      <bk-form :label-width="100">
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
        rebackParams: {
          questionType: [],
          desc: ''
        },
        isFeedbackLoading: false,
        rebackDialogConf: {
          visible: false
        }
      }
    },
    methods: {
      handleShowReback () {
        this.rebackParams = {
          questionType: [],
          desc: ''
        }
        this.rebackDialogConf.visible = true
      },
      async handleFeedback () {
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
    .apigw-tool-box {
        width: 44px;
        text-align: center;
        position: fixed;
        right: 0;
        z-index: 1000;
        top: 50%;
        transform: translateY(-50%);

        > li {
            /* margin-bottom: 13px; */
            cursor: pointer;
            background: #ffffff;
            border-radius: 18px 0 0 18px;
            box-shadow: 0px 2px 6px 0px rgb(0 0 0 / 10%);

            > a {
                padding: 18px 0 14px;
                display: block;
                font-size: 14px;
                color: #63656E;

                .icon-wrapper {
                    margin-bottom: 6px;
                }

                .text {
                    margin: 0 auto;
                    writing-mode: vertical-lr;
                    letter-spacing: 3px;
                }

                .doc-help-style {
                    font-size: 14px;
                }
            }

            &:hover {
                .icon, .text {
                    color: #3A84FF;
                }
            }

            i {
                margin-bottom: 3px;
                color: #979BA5;
            }
        }
        .feedback > a {
            writing-mode: vertical-lr;
            letter-spacing: 3px;
            margin: 0 auto;
            .text {
                margin-top: -3px;
            }
            &:hover {
                color: #3A84FF;
                .icon {
                    color: #3A84FF;
                }
            }
        }
    }
</style>
