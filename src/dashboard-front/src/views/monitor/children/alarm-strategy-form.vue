<template>
  <div class="strategy-form" v-bkloading="{ isLoading: isDataLoading }">
    <bk-form ref="form" :label-width="160" :model="formData">
      <div class="form-bd">
        <dl class="form-content">
          <div class="content-panel single">
            <bk-form-item
              :label="$t('告警策略名称')"
              :required="true"
              :rules="rules.name"
              :property="'name'">
              <bk-input :placeholder="$t('请输入')" :maxlength="128" v-model="formData.name"></bk-input>
            </bk-form-item>
          </div>
          <div class="content-panel">
            <dt class="panel-title"> {{ $t('触发条件') }} </dt>
            <dd class="panel-content">
              <bk-form-item
                :label="$t('告警规则')"
                :required="true"
                :rules="rules.alarm_subtype"
                :property="'alarm_subtype'">
                <bk-select :clearable="false" v-model="formData.alarm_subtype">
                  <bk-option v-for="option in alarmStrategyOptions.alarmSubType"
                    :key="option.value"
                    :id="option.value"
                    :name="option.name">
                  </bk-option>
                </bk-select>
              </bk-form-item>
              <bk-form-item :label="$t('告警范围')">
                <div class="flex-group">
                  <span class="item label"> {{ $t('资源标签包含') }} </span>
                  <span class="item" style="flex: none; width: 328px;">
                    <bk-select v-model="formData.api_label_ids" searchable multiple>
                      <bk-option v-for="option in labelList"
                        :key="option.id"
                        :id="option.id"
                        :name="option.name">
                      </bk-option>
                    </bk-select>
                  </span>
                </div>
              </bk-form-item>
              <bk-form-item :label="$t('检测算法')">
                <div class="flex-groups">
                  <div class="flex-group" style="flex: 2;">
                    <span class="item">
                      <bk-select
                        readonly
                        :clearable="false"
                        :popover-min-width="120"
                        v-model="formData.config.detect_config.duration">
                        <bk-option v-for="option in alarmStrategyOptions.detectConfig.duration"
                          :key="option.value"
                          :id="option.value"
                          :name="option.name">
                        </bk-option>
                      </bk-select>
                    </span>
                    <span class="item label"> {{ $t('内命中规则次数') }} </span>
                    <span class="item" style="flex: none; width: 70px;">
                      <bk-select
                        readonly
                        :clearable="false"
                        v-model="formData.config.detect_config.method">
                        <bk-option v-for="option in alarmStrategyOptions.detectConfig.method"
                          :key="option.value"
                          :id="option.value"
                          :name="option.name">
                        </bk-option>
                      </bk-select>
                    </span>
                  </div>
                  <div class="flex-group" style="flex: 1;">
                    <span class="item">
                      <bk-input
                        readonly
                        :placeholder="$t('请输入')"
                        type="number"
                        :min="0"
                        v-model="formData.config.detect_config.count">
                      </bk-input>
                    </span>
                    <span class="item label"> {{ $t('时触发') }} </span>
                  </div>
                </div>
              </bk-form-item>
              <bk-form-item :label="$t('告警收敛')">
                <div class="flex-group">
                  <span class="item label"> {{ $t('告警产生后') }}， </span>
                  <span class="item" style="flex: none; width: 122px;">
                    <bk-select readonly :clearable="false" v-model="formData.config.converge_config.duration">
                      <bk-option v-for="option in alarmStrategyOptions.convergeConfig.duration"
                        :key="option.value"
                        :id="option.value"
                        :name="option.name">
                      </bk-option>
                    </bk-select>
                  </span>
                  <span class="item label" style="flex: 1;"> {{ $t('内不再发送告警') }} </span>
                </div>
              </bk-form-item>
            </dd>
          </div>
          <div class="content-panel">
            <dt class="panel-title"> {{ $t('通知方式') }} </dt>
            <dd class="panel-content">
              <bk-form-item :label="$t('通知方式')" :required="true">
                <bk-checkbox-group v-model="formData.config.notice_config.notice_way" class="checkbox-group">
                  <bk-checkbox :value="'wechat'">
                    <svg aria-hidden="true" class="apigateway-icon wechat">
                      <use xlink:href="#icon-ag-wechat-color"></use>
                    </svg> {{ $t('微信') }}
                  </bk-checkbox>
                  <bk-checkbox :value="'im'">
                    <svg aria-hidden="true" class="apigateway-icon">
                      <use xlink:href="#icon-ag-qw"></use>
                    </svg> {{ $t('企业微信') }}
                  </bk-checkbox>
                  <bk-checkbox :value="'mail'">
                    <svg aria-hidden="true" class="apigateway-icon">
                      <use xlink:href="#icon-ag-email-color"></use>
                    </svg> {{ $t('邮箱') }}
                  </bk-checkbox>
                </bk-checkbox-group>
              </bk-form-item>
              <bk-form-item :label="$t('通知对象')">
                <bk-checkbox-group v-model="formData.config.notice_config.notice_role" class="checkbox-group">
                  <bk-checkbox :value="'maintainer'"> {{ $t('网关维护者') }} </bk-checkbox>
                </bk-checkbox-group>
              </bk-form-item>
              <bk-form-item :label="$t('其他通知对象')">
                <user v-model="formData.config.notice_config.notice_extra_receiver"></user>
                <p class="ag-tip mt5">
                  <i class="apigateway-icon icon-ag-info"></i> {{ $t('通知对象、其他通知对象至少一个有效') }}
                </p>
              </bk-form-item>
            </dd>
          </div>
        </dl>
      </div>
      <div class="form-ft">
        <bk-button theme="primary" class="mr10" :loading="isSaveLoading" @click="handleSave"> {{ $t('保存') }} </bk-button>
        <bk-button @click="handleCancel"> {{ $t('取消') }} </bk-button>
      </div>
    </bk-form>
  </div>
</template>

<script>
  import { mapGetters } from 'vuex'
  import { catchErrorHandler } from '@/common/util'
  import User from '@/components/user'

  export default {
    components: {
      User
    },
    props: {
      strategy: {
        type: Object,
        default: () => ({})
      }
    },
    data () {
      return {
        keyword: '',
        labelList: [],
        formData: {
          name: '',
          alarm_type: 'resource_backend',
          alarm_subtype: '',
          api_label_ids: [],
          config: {
            detect_config: {
              duration: 5 * 60,
              method: 'gte',
              count: 3
            },
            converge_config: {
              duration: 24 * 60 * 60
            },
            notice_config: {
              notice_way: ['wechat', 'im'],
              notice_role: ['maintainer'],
              notice_extra_receiver: []
            }
          }
        },
        rules: {
          name: [
            {
              required: true,
              message: this.$t('必填项'),
              trigger: 'blur'
            },
            {
              max: 128,
              message: this.$t('不能多于128个字符'),
              trigger: 'blur'
            }
          ],
          alarm_subtype: [
            {
              required: true,
              message: this.$t('必填项'),
              trigger: 'blur'
            }
          ]
        },
        isDataLoading: false,
        isSaveLoading: false
      }
    },
    computed: {
      ...mapGetters('options', ['alarmStrategyOptions']),
      apigwId () {
        return this.$route.params.id
      },
      isEdit () {
        return Boolean(this.strategy.id)
      }
    },
    async created () {
      await this.getApigwLabels()

      if (this.isEdit) {
        this.getApigwAlarmStrategy()
      }
    },
    methods: {
      async getApigwLabels () {
        const apigwId = this.apigwId
        const pageParams = {
          no_page: true,
          order_by: 'name'
        }

        try {
          const res = await this.$store.dispatch('label/getApigwLabels', { apigwId, pageParams })
          this.labelList = res.data.results
        } catch (e) {
          catchErrorHandler(e, this)
        }
      },

      async getApigwAlarmStrategy () {
        const apigwId = this.apigwId
        const { id } = this.strategy

        this.isDataLoading = true
        try {
          const res = await this.$store.dispatch('monitor/getApigwAlarmStrategy', { apigwId, id })

          const sortedLabelIds = []
          const labelIds = res.data.api_label_ids || []
          this.labelList.forEach((label, index) => {
            if (labelIds.includes(label.id)) {
              sortedLabelIds.push(label.id)
            }
          })
          this.formData = { ...this.formData, ...res.data, api_label_ids: sortedLabelIds }
          // 初始化编辑依赖
          this.$emit('init-data', this.formData)
        } catch (e) {
          catchErrorHandler(e, this)
        } finally {
          this.isDataLoading = false
        }
      },

      checkFormData (data) {
        if (!data.name) {
          this.$bkMessage({
            theme: 'error',
            message: this.$t('请输入告警策略名称')
          })
          this.$refs.form.validate()
          return false
        }

        if (!data.config.notice_config.notice_way.length) {
          this.$bkMessage({
            theme: 'error',
            message: this.$t('请选择通知方式')
          })
          this.$refs.form.validate()
          return false
        }

        if (!data.config.notice_config.notice_role.length
          && !data.config.notice_config.notice_extra_receiver.length) {
          this.$bkMessage({
            theme: 'error',
            message: this.$t('通知对象、其他通知对象至少设置一个')
          })
          this.$refs.form.validate()
          return false
        }

        return true
      },

      async saveApigwAlarmStrategy (data) {
        const action = this.isEdit ? 'monitor/updateApigwAlarmStrategy' : 'monitor/addApigwAlarmStrategy'
        this.isSaveLoading = true
        try {
          const apigwId = this.apigwId
          await this.$store.dispatch(action, { apigwId, data })

          this.$bkMessage({
            theme: 'success',
            message: this.isEdit ? this.$t('编辑成功！') : this.$t('新建成功！')
          })

          this.$emit('save-success', data)
        } catch (e) {
          catchErrorHandler(e, this)
        } finally {
          this.isSaveLoading = false
        }
      },

      async handleSave () {
        const data = this.formData
        try {
          await this.$refs.form.validate()

          if (this.checkFormData(data)) {
            this.saveApigwAlarmStrategy(data)
          }
        } catch (e) {
          console.error(e)
        }
      },

      handleCancel () {
        this.$emit('cancel')
      }
    }
  }
</script>

<style lang="postcss" scoped>
    @import '@/css/variable.css';

    .strategy-form {
        .form-content {
            .content-panel {
                overflow: hidden;
                border: 1px solid #DCDEE5;
                margin-bottom: 16px;
                border-radius: 2px;

                &.single {
                    border: none;
                    /deep/.bk-form-item {
                        .bk-label {
                            height: 40px;
                            line-height: 40px;
                            font-size: 14px;
                            font-weight: 700;
                            border: 1px solid #DCDEE5;
                            border-right: none;
                            background: #FAFBFD;
                        }
                        .bk-form-input {
                            height: 40px;
                            line-height: 40px;
                            border-bottom-left-radius: unset;
                            border-top-left-radius: unset;
                        }
                        .tooltips-icon {
                            top: 11px;
                        }
                    }
                }

                .panel-title {
                    height: 40px;
                    line-height: 40px;
                    padding-left: 20px;
                    font-size: 14px;
                    font-weight: 700;
                    color: #63656E;
                    background: #FAFBFD;
                }

                .panel-content {
                    padding: 30px 90px 30px 0;
                    border-top: 1px solid #DCDEE5;
                }
            }
        }
    }

    .flex-group {
        display: flex;
        .item {
            flex: 1;
            &.label {
                flex: none;
                font-size: 14px;
                color: #313238;
                padding: 0 12px;
                border: 1px solid #C4C6CC;
                background: #FAFBFD;
            }

            &+.item {
                margin-left: -1px;
            }
        }
    }

    .flex-groups {
        display: flex;

        .flex-group {
            &+.flex-group {
                margin-left: 8px;
            }
        }
    }

    .checkbox-group {
        .bk-form-checkbox {
            min-width: 122px;
            margin-right: 10px;

            .apigateway-icon {
                width: 24px;
                height: 24px;
                margin-right: 4px;
                vertical-align: middle;

                &.wechat {
                    margin-top: 1px;
                }
            }
        }
    }
</style>
