<template>
  <div class="app-content">
    <section class="ag-panel">
      <div class="panel-key">
        <strong> {{ $t('基本信息') }} </strong>
      </div>
      <div class="panel-content">
        <div class="panel-wrapper">
          <bk-form ref="nameForm" :label-width="180" :model="curStage">
            <bk-form-item
              :label="$t('名称')"
              :required="true"
              :rules="rules.name"
              :property="'name'"
              :error-display-type="'normal'">
              <bk-input
                :placeholder="$t('由字母、数字、连接符（-）、下划线（_）组成，首字符必须是字母，长度小于20个字符')"
                v-model="curStage.name"
                :disabled="stageId !== undefined">
              </bk-input>
              <p slot="tip" class="ag-tip mt5">
                <i class="apigateway-icon icon-ag-info"></i> {{ $t('环境唯一标识，创建后不可修改') }}
              </p>
            </bk-form-item>
            <bk-form-item :label="$t('访问地址')">
              <bk-input v-model="curStageUrl" :disabled="true"></bk-input>
            </bk-form-item>
            <bk-form-item :label="$t('描述')">
              <bk-input v-model="curStage.description" :placeholder="$t('不超过512个字符')"></bk-input>
            </bk-form-item>
          </bk-form>
        </div>
      </div>
    </section>

    <section class="ag-panel" v-if="microGatewayEnabledFlag">
      <div class="panel-key">
        <strong> {{ $t('微网关') }} </strong>
      </div>
      <div class="panel-content">
        <div class="panel-wrapper">
          <bk-form ref="microForm" :label-width="180" :model="curStage">
            <bk-form-item
              :label="$t('微网关实例')">
              <bk-select
                :clearable="true"
                :disabled="!microList.length"
                :placeholder="microList.length ? $t('请选择微网关实例') : $t('无未绑定的实例')"
                v-model="curStage.micro_gateway_id">
                <bk-option v-for="option in microList"
                  :key="option.id"
                  :id="option.id"
                  :name="option.name">
                </bk-option>
              </bk-select>
              <p class="ag-tip mt5">
                <i class="apigateway-icon icon-ag-info"></i> {{ $t('发布资源版本时，会将版本发布到环境绑定的微网关实例中，并由此实例提供网关服务；如果未选择微网关实例，即为解绑当前环境的微网关实例') }}
              </p>
            </bk-form-item>
          </bk-form>
        </div>
      </div>
    </section>

    <section class="ag-panel">
      <div class="panel-key">
        <strong> {{ $t('环境变量') }} </strong>
      </div>
      <div class="panel-content">
        <div class="panel-wrapper">
          <bk-form :label-width="180">
            <bk-form-item :label="$t('数据列表')">
              <bk-table
                :data="curStage.varList"
                :size="'small'">
                <div slot="empty">
                  <table-empty empty />
                </div>
                <bk-table-column :label="$t('变量名')">
                  <template slot-scope="props">
                    <template v-if="props.row.isEdited">
                      <bk-form :label-width="1" class="ag-inner-form" :model="props.row" :ref="`var-key-${props.row.id}`">
                        <bk-form-item :rules="varRules.key" :property="'editKey'">
                          <bk-input v-model="props.row.editKey"></bk-input>
                        </bk-form-item>
                      </bk-form>
                    </template>
                    <template v-else>
                      {{props.row.key}}
                    </template>
                  </template>
                </bk-table-column>
                <bk-table-column :label="$t('值')">
                  <template slot-scope="props">
                    <template v-if="props.row.isEdited">
                      <bk-form :label-width="1" class="ag-inner-form" :model="props.row" :ref="`var-value-${props.row.id}`">
                        <bk-form-item :property="'editValue'">
                          <bk-input v-model="props.row.editValue"></bk-input>
                        </bk-form-item>
                      </bk-form>
                    </template>
                    <template v-else>
                      {{props.row.value}}
                    </template>
                  </template>
                </bk-table-column>
                <bk-table-column :label="$t('操作')" width="150">
                  <template slot-scope="props">
                    <template v-if="props.row.isEdited">
                      <bk-button class="mr5" theme="primary" text @click="handleEditConfirm(props.row)"> {{ $t('确定') }} </bk-button>
                      <bk-button theme="primary" text @click="handleEditCancel(props.row, props.$index)"> {{ $t('取消') }} </bk-button>
                    </template>
                    <template v-else>
                      <bk-button class="mr5" theme="primary" text @click="handleEditVar(props.row)"> {{ $t('编辑') }} </bk-button>
                      <bk-button theme="primary" text @click="handleRemoveVar(props.row, props.$index)"> {{ $t('删除') }} </bk-button>
                    </template>
                  </template>
                </bk-table-column>
              </bk-table>
              <p class="ag-tip mt10" style="line-height: 32px;">
                <i class="apigateway-icon icon-ag-info"></i> {{ $t('变量名由字母、数字、下划线（_） 组成，首字符必须是字母，长度小于50个字符') }}
                <bk-button
                  theme="primary"
                  style="width: 110px; float: right;"
                  @click="handleAddVar">
                  {{ $t('新增') }}
                </bk-button>
              </p>
            </bk-form-item>
          </bk-form>
        </div>
      </div>
    </section>

    <section class="ag-panel">
      <div class="panel-key">
        <strong> {{ $t('代理配置') }} </strong>
      </div>
      <div class="panel-content">
        <div class="panel-wrapper">
          <bk-form ref="proxyForm" :label-width="180" :model="curStage">
            <bk-form-item :label="$t('负载均衡类型')" :required="true" :error-display-type="'normal'">
              <bk-select
                :clearable="false"
                :placeholder="$t('负载均衡类型')"
                v-model="curStage.proxy_http.upstreams.loadbalance">
                <bk-option v-for="option in loadbalanceList"
                  :key="option.id"
                  :id="option.id"
                  :name="option.name">
                </bk-option>
              </bk-select>
            </bk-form-item>
            
            <bk-form-item
              label="Hosts"
              v-for="(hostItem, index) of curStage.proxy_http.upstreams.hosts"
              :required="true"
              :rules="rules.host"
              :property="'proxy_http.upstreams.hosts.' + index + '.host'"
              :icon-offset="curStage.proxy_http.upstreams.loadbalance === 'weighted-roundrobin' ? 90 : 10"
              :key="index"
              :class="{ 'form-item-special': index !== 0 }"
              :error-display-type="'normal'">
              <div class="host-item mb10">
                <bk-input
                  :placeholder="$t('格式: http(s)://host:port')"
                  v-model="hostItem.host"
                  v-if="curStage.proxy_http.upstreams.loadbalance === 'weighted-roundrobin'"
                  :key="curStage.proxy_http.upstreams.loadbalance">
                  <div class="append-wrapper" slot="append">
                    <bk-input
                      :class="['ag-host-input', 'weights-input', { 'is-error': hostItem.isRoles }]"
                      type="number"
                      :placeholder="$t('权重')"
                      style="border: none !important;"
                      :min="1"
                      :max="10000"
                      :show-controls="false"
                      v-model="hostItem.weight"
                      @input="weightValidate(hostItem)">
                    </bk-input>
                    <i v-if="hostItem.isRoles" class="bk-icon icon-exclamation-circle-shape tooltips-icon" v-bk-tooltips="hostItem.message"></i>
                  </div>
                </bk-input>

                <bk-input
                  :placeholder="$t('格式: http(s)://host:port')"
                  v-model="hostItem.host"
                  v-else :key="curStage.proxy_http.upstreams.loadbalance">
                </bk-input>

                <i class="add-host-btn apigateway-icon icon-ag-plus-circle-shape" @click="handleAddHost"></i>
                <i class="delete-host-btn apigateway-icon icon-ag-minus-circle-shape" @click="handleDeleteHost(hostItem, index)" v-if="curStage.proxy_http.upstreams.hosts.length >= 2"></i>
              </div>
            </bk-form-item>
            <p class="ag-tip mt5" style="margin-left: 120px;">
              <i class="apigateway-icon icon-ag-info"></i>{{ $t('该环境下，网关调用后端服务的默认域名或IP，不包含Path，比如：https://example.com') }}
            </p>
          </bk-form>

          <div class="ag-span"></div>

          <bk-form ref="timeoutForm" :label-width="180" :model="curStage">
            <bk-form-item
              :label="$t('超时时间')"
              :required="true"
              :rules="rules.timeout"
              :property="'proxy_http.timeout'"
              :icon-offset="220"
              style="width: 500px;"
              :error-display-type="'normal'">
              <bk-input
                type="number"
                :min="1"
                :show-controls="false"
                v-model="curStage.proxy_http.timeout"
                class="time-input">
                <template slot="append">
                  <div class="group-text group-text-style">{{ $t('秒') }}</div>
                </template>
              </bk-input>
              <span class="ag-text" style="line-height: 32px;"> {{ $t('最大300秒') }} </span>
            </bk-form-item>
            <p class="ag-tip mt5" style="margin-left: 120px;">
              <i class="apigateway-icon icon-ag-info"></i> {{ $t('该环境下，网关调用后端服务的默认超时时间') }}
            </p>
          </bk-form>

          <div class="ag-span"></div>

          <bk-form :label-width="180">
            <bk-form-item :label="$t('Header转换')">
              <apigw-key-valuer
                ref="setKeyValuer"
                class="mb10"
                :label="$t('设置')"
                :value="curStage.proxy_http.transform_headers.set">
              </apigw-key-valuer>
              <!-- <apigw-key-valuer
                                ref="appendKeyValuer"
                                class="mb10"
                                :label="'追加'"
                                :value="curStage.proxy_http.transform_headers.append">
                            </apigw-key-valuer>
                            <apigw-key-valuer
                                ref="replaceKeyValuer"
                                class="mb10"
                                :label="'替换'"
                                :value="curStage.proxy_http.transform_headers.replace">
                            </apigw-key-valuer> -->
              <apigw-item
                ref="deleteKeyValuer"
                :label="$t('删除')"
                :value="curStage.proxy_http.transform_headers.delete">
              </apigw-item>
            </bk-form-item>
            <p class="ag-tip mt5" style="margin-left: 120px;">
              <i class="apigateway-icon icon-ag-info"></i> {{ $t('该环境下，网关调用后端服务时，请求头处理默认配置。设置，表示将请求头设置为指定值；删除，表示删除指定的请求头') }} </p>
          </bk-form>
        </div>
      </div>
    </section>

    <section class="ag-panel" v-if="stageRateLimitEnabledFlag">
      <div class="panel-key">
        <strong> {{ $t('流量控制') }} </strong>
      </div>
      <div class="panel-content">
        <div class="panel-wrapper">
          <bk-form :label-width="180">
            <bk-form-item>
              <div style="overflow: hidden;">
                <bk-radio-group v-model="curStage.rate_limit.enabled">
                  <bk-radio class="mb10" :value="false" style="display: block; width: 90px;"> {{ $t('不限制') }} </bk-radio>
                  <bk-radio :value="true" style="line-height: 32px;">
                    {{ $t('限制') }}
                  </bk-radio>
                </bk-radio-group>
                <div class="tokens-wrapper">
                  <bk-input
                    type="number"
                    :placeholder="$t('输入')"
                    :min="1"
                    :clearable="true"
                    :show-controls="false"
                    :disabled="!curStage.rate_limit.enabled"
                    v-model="curStage.rate_limit.rate.tokens"
                    style="width: 64px; float: left;">
                  </bk-input>
                  <span class="fl ag-text mr10 ml10">次/</span>
                  <bk-select
                    v-model="curStage.rate_limit.rate.period"
                    :placeholder="$t('单位')"
                    style="width: 65px; float: left; margin-right: 10px;"
                    :clearable="false"
                    :disabled="!curStage.rate_limit.enabled">
                    <bk-option v-for="option in unitList"
                      :key="option.id"
                      :id="option.id"
                      :name="option.name">
                    </bk-option>
                  </bk-select>
                </div>
              </div>
              <div class="ag-alert primary mt10">
                <i class="apigateway-icon icon-ag-info"></i>
                <p>
                  <span> {{ $t('环境全局流量控制，保护后端服务，防止过载。还可以通过访问策略，配置基于应用维度的精细化流量控制。') }} </span>
                  <a :href="GLOBAL_CONFIG.DOC.RATELIMIT" target="_blank" class="ag-primary"> {{ $t('详情文档') }} </a>
                </p>
              </div>
            </bk-form-item>
          </bk-form>
        </div>
      </div>
    </section>

    <section class="ag-panel-action mt20">
      <div class="panel-content" style="margin-left: 270px;">
        <div class="panel-wrapper tc">
          <bk-button class="mr5" theme="primary" style="width: 120px;" @click="submitApigwStage" :loading="isDataLoading"> {{ $t('提交') }} </bk-button>
          <bk-button style="width: 120px;" @click="handleApigwStageCancel"> {{ $t('取消') }} </bk-button>
        </div>
      </div>
    </section>
  </div>
</template>

<script>
  import { catchErrorHandler } from '@/common/util'
  import ApigwKeyValuer from '@/components/key-valuer'
  import ApigwItem from '@/components/item'

  export default {
    components: {
      ApigwKeyValuer,
      ApigwItem
    },
    data () {
      return {
        varIndex: 0,
        isPageLoading: true,
        isDataLoading: false,
        curLabelList: [
          {
            key: '',
            value: ''
          }
        ],
        curStage: {
          'name': '',
          'description': '',
          'varList': [],
          'vars': {},
          'micro_gateway_id': '',
          'proxy_http': {
            'timeout': 30,
            'upstreams': {
              'loadbalance': 'roundrobin',
              'hosts': [
                {
                  'host': '',
                  'weight': 100
                }
              ]
            },
            'transform_headers': {
              'add': {},
              'append': {},
              'replace': {},
              'delete': []
            }
          },
          'rate_limit': {
            'enabled': false,
            'rate': {
              'tokens': 5000,
              'period': 60
            }
          }
        },
        unitList: [
          {
            id: 1,
            name: this.$t('秒')
          },
          {
            id: 60,
            name: this.$t('分')
          },
          {
            id: 3600,
            name: this.$t('时')
          }
        ],
        varRules: {
          key: [
            {
              required: true,
              message: this.$t('必填项'),
              trigger: 'blur'
            },
            {
              max: 50,
              message: this.$t('不能多于50个字符'),
              trigger: 'blur'
            },
            {
              validator (value) {
                const reg = /^[a-zA-Z][a-zA-Z0-9_]{0,49}$/
                return reg.test(value)
              },
              message: this.$t('由字母、数字、下划线（_） 组成，首字符必须是字母，长度小于50个字符'),
              trigger: 'blur'
            }
          ],

          value: [
            {
              required: true,
              message: this.$t('必填项'),
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
              max: 20,
              message: this.$t('不能多于20个字符'),
              trigger: 'blur'
            },
            {
              validator (value) {
                const reg = /^[a-zA-Z][a-zA-Z0-9_-]{0,19}$/
                return reg.test(value)
              },
              message: this.$t('由字母、数字、连接符（-）、下划线（_）组成，首字符必须是字母，长度小于20个字符'),
              trigger: 'blur'
            }
          ],

          host: [
            {
              required: true,
              message: this.$t('必填项'),
              trigger: 'blur'
            },
            {
              regex: /^(?=^.{3,255}$)http(s)?:\/\/[a-zA-Z0-9][-a-zA-Z0-9]{0,62}(\.[a-zA-Z0-9][-a-zA-Z0-9]{0,62})*(:\d+)?(\/)?$|^http(s)?:\/\/\[([0-9a-fA-F]{0,4}:){2,7}[0-9a-fA-F]{0,4}\](:\d+)?\/?$/,
              message: this.$t('请输入合法Host，如：http://example.com'),
              trigger: 'blur'
            }
          ],

          timeout: [
            {
              required: true,
              message: this.$t('必填项'),
              trigger: 'blur'
            },
            {
              validator: function (val) {
                if (val < 0 || val > 300) {
                  return false
                }
                return true
              },
              message: this.$t('超时时间不能小于1且不能大于300'),
              trigger: 'blur'
            }
          ]

        },
        microList: []
      }
    },
    computed: {
      apigwId () {
        return this.$route.params.id
      },
      stageId () {
        return this.$route.params.stageId || undefined
      },
      curApigwName () {
        const apigwList = this.$store.state.apis.apigwList
        const apigw = apigwList.find(apigw => {
          return String(apigw.id) === String(this.apigwId)
        })
        return apigw ? apigw.name : ''
      },
      curStageUrl () {
        const keys = {
          'api_name': this.curApigwName,
          'stage_name': this.curStage.name,
          'resource_path': ''
        }
        let url = this.GLOBAL_CONFIG.STAGE_DOMAIN
        for (const name in keys) {
          const reg = new RegExp(`{${name}}`)
          url = url.replace(reg, keys[name])
        }
        return url
      },
      curApigw () {
        return this.$store.state.curApigw
      },
      stageRateLimitEnabledFlag () {
        if (!this.curApigw.feature_flags) return false
        return this.curApigw.feature_flags.STAGE_RATE_LIMIT_ENABLED
      },
      microGatewayEnabledFlag () {
        if (!this.curApigw.feature_flags) return false
        return this.curApigw.feature_flags.MICRO_GATEWAY_ENABLED
      },
      loadbalanceList () {
        return [
          {
            id: 'roundrobin',
            name: this.$t('轮询(Round-Robin)')
          },
          {
            id: 'weighted-roundrobin',
            name: this.$t('加权轮询(Weighted Round-Robin)')
          }
        ]
      }
    },
    created () {
      this.getMicroApigwList()
      this.init()
      this.getMicroApigwList()
    },
    methods: {
      init () {
        if (this.stageId !== undefined) {
          this.getStageDetail()
        } else {
          setTimeout(() => {
            this.isPageLoading = false
            this.$store.commit('setMainContentLoading', false)
          }, 500)
        }
      },

      goBack () {
        this.goStageIndex()
      },

      async getStageDetail () {
        try {
          const apigwId = this.apigwId
          const stageId = this.stageId
          const res = await this.$store.dispatch('stage/getApigwStageDetail', { apigwId, stageId })
          const data = res.data
          const varList = []
          if (data.vars) {
            for (const key in data.vars) {
              varList.push({
                id: this.varIndex,
                key: key,
                value: data.vars[key],
                editKey: key,
                editValue: data.vars[key],
                isEdited: false
              })
              this.varIndex++
            }
          }
          data.varList = varList
          this.curStage = data
        } catch (e) {
          catchErrorHandler(e, this)
        } finally {
          setTimeout(() => {
            this.isPageLoading = false
            this.$store.commit('setMainContentLoading', false)
          }, 500)
        }
      },

      handleAddVar () {
        this.curStage.varList.push({
          id: this.varIndex,
          key: '',
          value: '',
          editKey: '',
          editValue: '',
          isEdited: true
        })
        this.varIndex++
      },

      handleEditConfirm (data) {
        const keyReg = /^[a-zA-Z0-9_]{1,50}$/
        if (!data.editKey || !keyReg.test(data.editKey)) {
          this.$refs[`var-key-${data.id}`].validate()
          return false
        }

        // if (!data.editValue) {
        //     this.$refs[`var-value-${data.id}`].validate()
        //     return false
        // }

        let hasOtherKey = false
        this.curStage.varList.forEach(item => {
          if (!item.isEdited && item.key === data.editKey) {
            hasOtherKey = true
          }
        })

        if (hasOtherKey) {
          this.$bkMessage({
            theme: 'error',
            message: this.$t('变量key不能重复')
          })
          return false
        }
        data.key = data.editKey
        data.value = data.editValue
        data.isEdited = false
      },

      handleEditCancel (data, index) {
        if (!data.key && !data.value) {
          this.curStage.varList.splice(index, 1)
        } else {
          data.editKey = data.key
          data.editValue = data.value
          data.isEdited = false
        }
      },

      handleEditVar (data) {
        data.isEdited = true
      },

      handleRemoveVar (data, index) {
        this.curStage.varList.splice(index, 1)
      },

      handleAddHost () {
        this.curStage.proxy_http.upstreams.hosts.push({
          host: '',
          weight: 100,
          isRoles: false,
          message: ''
        })
      },

      handleDeleteHost (host, index) {
        this.curStage.proxy_http.upstreams.hosts.splice(index, 1)
      },

      handleApigwStageCancel () {
        this.goStageIndex()
      },

      goStageIndex () {
        this.$router.push({
          name: 'apigwStage',
          params: {
            id: this.apigwId
          }
        })
      },

      checkHeader (params, headerKey) {
        const varReg = /^[a-zA-Z0-9-]+$/
        const header = params.proxy_http.transform_headers[headerKey]
        for (const key in header) {
          if (!key) {
            this.$bkMessage({
              theme: 'error',
              message: this.$t('请输入Header转换中的键')
            })
            this.$refs[`${headerKey}KeyValuer`].validate()
            return false
          }
          if (!varReg.test(key)) {
            this.$bkMessage({
              theme: 'error',
              message: this.$t('请输入合法的Header转换键')
            })
            this.$refs[`${headerKey}KeyValuer`].validate()
            return false
          }

          if (!header[key]) {
            this.$bkMessage({
              theme: 'error',
              message: this.$t('请输入Header转换值')
            })
            this.$refs[`${headerKey}KeyValuer`].validate()
            return false
          }
        }
        return true
      },

      checkData (params) {
        const hostReg = /^(?=^.{3,255}$)http(s)?:\/\/[a-zA-Z0-9][-a-zA-Z0-9]{0,62}(\.[a-zA-Z0-9][-a-zA-Z0-9]{0,62})*(:\d+)?(\/)?$|^http(s)?:\/\/\[([0-9a-fA-F]{0,4}:){2,7}[0-9a-fA-F]{0,4}\](:\d+)?\/?$/
        const nameReg = /^[a-zA-Z][a-zA-Z0-9_-]{0,19}$/
        if (!params.name) {
          this.$bkMessage({
            theme: 'error',
            message: this.$t('请输入名称')
          })
          this.$refs.nameForm.validate()
          return false
        }

        if (!nameReg.test(params.name)) {
          this.$bkMessage({
            theme: 'error',
            message: this.$t('由字母、数字、连接符（-）、下划线（_）组成，首字符必须是字母，长度小于20个字符')
          })
          this.$refs.nameForm.validate()
          return false
        }

        // if (params.varList.length) {
        //     const keyReg = /^[a-zA-Z0-9_]{1,10}$/

        //     for (let i = 0; i < params.varList.length; i++) {
        //         const varItem = params.varList[i]
        //         if (!varItem.editKey) {
        //             this.$bkMessage({
        //                 theme: 'error',
        //                 message: '请输入数据列表中的变量名'
        //             })
        //             this.$refs[`var-key-${varItem.id}`].validate()
        //             return false
        //         }

        //         if (!keyReg.test(varItem.editKey)) {
        //             this.$bkMessage({
        //                 theme: 'error',
        //                 message: '请输入合法的变量名'
        //             })
        //             this.$refs[`var-key-${varItem.id}`].validate()
        //             return false
        //         }
        //     }
        // }

        for (let i = 0; i < params.proxy_http.upstreams.hosts.length; i++) {
          const hostItem = params.proxy_http.upstreams.hosts[i]
          if (!hostItem.host) {
            this.$bkMessage({
              theme: 'error',
              message: this.$t('请输入Host值')
            })
            this.$refs.proxyForm.validate()
            return false
          }

          if (hostItem.isRoles) {
            this.$bkMessage({
              theme: 'error',
              message: this.$t('请输入Host权重值')
            })
            return false
          }

          if (!hostReg.test(hostItem.host)) {
            this.$bkMessage({
              theme: 'error',
              message: this.$t('请输入合法Host，如：http://example.com')
            })
            this.$refs.proxyForm.validate()
            return false
          }
        }

        if (params.proxy_http.timeout < 1 || params.proxy_http.timeout > 300) {
          this.$bkMessage({
            theme: 'error',
            message: this.$t('超时时间不能小于1且不能大于300')
          })
          this.$refs.timeoutForm.validate()
          return false
        }

        if (!this.$refs.setKeyValuer.checkRepeat()) {
          this.$bkMessage({
            theme: 'error',
            message: this.$t('代理配置Header转换中不允许重复值')
          })
          return false
        }

        if (!this.checkHeader(params, 'set')) {
          return false
        }

        // if (!this.checkHeader(params, 'append')) {
        //     return false
        // }

        if (!this.checkHeader(params, 'delete')) {
          return false
        }

        if (params.proxy_http.transform_headers['delete']) {
          const keyReg = /^[a-zA-Z0-9-]+$/
          const deleteHeaders = this.$refs.deleteKeyValuer.getValue()
          const uniqueList = [...new Set(deleteHeaders)]

          if (deleteHeaders.length && !keyReg.test(deleteHeaders.join(''))) {
            this.$bkMessage({
              theme: 'error',
              message: this.$t('请输入合法的Header转换键')
            })
            this.$refs.deleteKeyValuer.validate()
            return false
          }

          if (uniqueList.length < deleteHeaders.length) {
            this.$bkMessage({
              theme: 'error',
              message: this.$t('代理配置Header转换中不允许重复值')
            })
            this.$refs.deleteKeyValuer.validate()
            return false
          }
        }
        if (params.rate_limit.enabled && !params.rate_limit.rate.tokens) {
          this.$bkMessage({
            theme: 'error',
            message: this.$t('请输入限制的次数')
          })
          return false
        }

        for (let i = 0; i < params.proxy_http.upstreams.hosts.length; i++) {
          if (params.proxy_http.upstreams.hosts[i]) {
            delete params.proxy_http.upstreams.hosts[i].isRoles
            delete params.proxy_http.upstreams.hosts[i].message
          }
        }

        return true
      },
      submitApigwStage () {
        if (this.isDataLoading) {
          return false
        }
        const params = this.formatData()

        if (this.checkData(params)) {
          if (this.stageId !== undefined) {
            this.updateApigwStage(params)
          } else {
            this.addApigwStage(params)
          }
        }
      },

      formatData () {
        const params = JSON.parse(JSON.stringify(this.curStage))
        const vars = {}
        const header = params.proxy_http.transform_headers

        params.varList.forEach(item => {
          if (item.key) {
            vars[item.key] = item.value
          }
        })
        params.vars = vars
        header.set = this.$refs.setKeyValuer.getValue()
        // header.append = this.$refs.appendKeyValuer.getValue()
        // header.replace = this.$refs.replaceKeyValuer.getValue()
        header.delete = this.$refs.deleteKeyValuer.getValue()

        if (params.micro_gateway_id === '') {
          params.micro_gateway_id = null
        }

        return params
      },

      async addApigwStage (data) {
        this.isDataLoading = true
        try {
          const apigwId = this.apigwId
          await this.$store.dispatch('stage/addApigwStage', { apigwId, data })

          this.$bkMessage({
            theme: 'success',
            message: this.$t('新建成功！')
          })
          this.goStageIndex()
        } catch (e) {
          catchErrorHandler(e, this)
        } finally {
          this.isDataLoading = false
        }
      },

      async updateApigwStage (data) {
        this.isDataLoading = true
        try {
          const apigwId = this.apigwId
          const stageId = this.stageId
          await this.$store.dispatch('stage/updateApigwStage', { apigwId, stageId, data })

          this.$bkMessage({
            theme: 'success',
            message: this.$t('更新成功！')
          })
          this.goStageIndex()
        } catch (e) {
          catchErrorHandler(e, this)
        } finally {
          this.isDataLoading = false
        }
      },

      async getMicroApigwList () {
        const apigwId = this.apigwId
        const pageParams = {
          no_page: true
        }

        this.isDataLoading = true
        try {
          const res = await this.$store.dispatch('microGateway/getMicroApigwList', { apigwId, pageParams })
          this.microList = res.data.results
          // stage_name 非空且与当前 stage_name不同，说明微网关实例已被绑定，不能选择
          this.microList = [...res.data.results].filter(e => e.stage_name === '' || e.stage_name === this.curStage.name)
        } catch (e) {
          catchErrorHandler(e, this)
        } finally {
          this.isPageLoading = false
          this.isDataLoading = false
          this.$store.commit('setMainContentLoading', false)
        }
      },

      weightValidate (hostItem) {
        if (!hostItem.weight) {
          hostItem.isRoles = true
          hostItem.message = this.$t('请输入合法的整数值')
        } else {
          hostItem.isRoles = false
        }
      }
    }
  }
</script>

<style lang="postcss" scoped>
    @import '@/css/variable.css';

    .panel-wrapper {
        padding-left: 50px;
    }

    .host-item {
        position: relative;
    }

    .add-host-btn,
    .delete-host-btn {
        color: #979BA5;
        font-size: 16px;
        display: inline-block;
        cursor: pointer;
        margin-right: 5px;
    }

    .add-host-btn {
        position: absolute;
        right: -28px;
        top: 8px;
    }

    .delete-host-btn {
        position: absolute;
        right: -50px;
        top: 8px;
    }

    .ag-host-input {
        width: 80px;
        line-height: 30px;
        font-size: 12px;
        color: #63656E;
        outline: none;
        padding: 0 10px;
        text-align: center;
    }

    .tokens-wrapper {
        position: absolute;
        left: 65px;
        top: 32px;
    }
    .time-input {
        float: left;
        width: 180px;
        margin-right: 10px;
    }
    .group-text-style {
        width: 74px;
        text-align: center;
    }
    .append-wrapper {
        i {
            position: absolute;
            right: 4px;
            top: 7px;
            font-size: 16px;
        }
    }
    .weights-input /deep/  input {
        color: #63656e !important;
    }
    .weights-input.is-error /deep/ input[type=text] {
        color: #ff5656 !important;
    }
</style>
