<template>
  <div class="ag-resource-item" v-if="curResource" :class="{ 'show-diff': onlyShowDiff }">
    <p class="title" :class="{ 'ag-diff': checkDiff('localData.name') || checkDiff('localData.description') || checkDiff('localData.is_public') }"> {{ $t('基本信息') }} </p>
    <bk-container class="ag-kv-box" :col="14" :margin="6">
      <bk-row :class="{ 'ag-diff': checkDiff('localData.name') }">
        <bk-col :span="4">
          <label class="ag-key">{{ $t('资源名称') }}:</label>
        </bk-col>
        <bk-col :span="10">
          <div class="ag-value">{{localData.name || '--'}}</div>
        </bk-col>
      </bk-row>

      <bk-row :class="{ 'ag-diff': checkDiff('localData.description') }">
        <bk-col :span="4">
          <label class="ag-key">{{ $t('资源描述') }}:</label>
        </bk-col>
        <bk-col :span="10">
          <div class="ag-value">{{localData.description || '--'}}</div>
        </bk-col>
      </bk-row>

      <bk-row :class="{ 'ag-diff': checkDiff('localData.is_public') }">
        <bk-col :span="4">
          <label class="ag-key">{{ $t('是否公开') }}:</label>
        </bk-col>
        <bk-col :span="10">
          <div class="ag-value">{{localData.is_public ? $t('是') : $t('否')}}</div>
        </bk-col>
      </bk-row>
    </bk-container>

    <p class="title mt15" :class="{ 'ag-diff': checkDiff('localData.method') || checkDiff('localData.path') || checkDiff('localData.match_subpath') }"> {{ $t('前端配置') }} </p>
    <bk-container class="ag-kv-box" :col="14" :margin="6">
      <bk-row :class="{ 'ag-diff': checkDiff('localData.method') }">
        <bk-col :span="4">
          <label class="ag-key">{{ $t('请求方法') }}:</label>
        </bk-col>
        <bk-col :span="10">
          <div class="ag-value">{{localData.method}}</div>
        </bk-col>
      </bk-row>

      <bk-row :class="{ 'ag-diff': checkDiff('localData.path') }">
        <bk-col :span="4">
          <label class="ag-key">{{ $t('请求路径') }}:</label>
        </bk-col>
        <bk-col :span="10">
          <div class="ag-value">{{localData.path}}</div>
        </bk-col>
      </bk-row>

      <bk-row :class="{ 'ag-diff': checkDiff('localData.match_subpath') }">
        <bk-col :span="4">
          <label class="ag-key">{{ $t('匹配所有子路径') }}:</label>
        </bk-col>
        <bk-col :span="10">
          <div class="ag-value">{{localData.match_subpath ? $t('是') : $t('否')}}</div>
        </bk-col>
      </bk-row>
    </bk-container>

    <p class="title mt15" :class="{ 'ag-diff': checkDiff('localData.proxy') }"> {{ $t('后端配置') }} </p>
    <bk-container class="ag-kv-box" :col="14" :margin="6" :class="{ 'box-diff': checkDiff('localData.proxy.type') }">
      <bk-row :class="{ 'ag-diff': checkDiff('localData.proxy.type') }">
        <bk-col :span="4">
          <label class="ag-key">{{ $t('后端类型:') }}</label>
        </bk-col>
        <bk-col :span="10">
          <div class="ag-value">{{localData.proxy.type.toUpperCase()}}</div>
        </bk-col>
      </bk-row>

      <template v-if="localData.proxy.type === 'http'">
        <bk-row :class="{ 'ag-diff': checkDiff('localData.proxy.config.method') }">
          <bk-col :span="4">
            <label class="ag-key">Method:</label>
          </bk-col>
          <bk-col :span="10">
            <div class="ag-value">{{localData.proxy.config.method || '--'}}</div>
          </bk-col>
        </bk-row>

        <bk-row :class="{ 'ag-diff': checkDiff('localData.proxy.config.path') }">
          <bk-col :span="4">
            <label class="ag-key">Path:</label>
          </bk-col>
          <bk-col :span="10">
            <div class="ag-value">{{localData.proxy.config.path || '--'}}</div>
          </bk-col>
        </bk-row>

        <bk-row :class="{ 'ag-diff': checkDiff('localData.proxy.config.match_subpath') }">
          <bk-col :span="4">
            <label class="ag-key">{{ $t('追加匹配子路径:') }}</label>
          </bk-col>
          <bk-col :span="10">
            <div class="ag-value">{{localData.proxy.config.match_subpath ? $t('是') : $t('否')}}</div>
          </bk-col>
        </bk-row>

        <bk-row :class="{ 'ag-diff': checkDiff('localData.proxy.config.upstreams') }">
          <bk-col :span="4">
            <label class="ag-key" style="line-height: 32px;">Hosts:</label>
          </bk-col>
          <bk-col :span="10">
            <div class="bk-button-group" :class="{ 'button-diff': checkDiff('localData.proxy.config.upstreams') }" style="display: flex;">
              <div class="readonly-value">{{ localData.useDefaultHost ? $t('使用环境配置') : $t('覆盖环境配置') }}</div>
            </div>
            <div class="detail-wrapper" v-if="!localData.useDefaultHost" :class="{ 'wrapper-diff': checkDiff('localData.proxy.config.upstreams') }">
              <div class="content-item">
                <span class="key"> {{ $t('负载均衡类型') }}： </span>
                <span class="value">{{weightMap[localData.proxy.config.upstreams.loadbalance]}}</span>
              </div>
              <div class="content-item">
                <span class="key">Hosts：</span>
                <div class="value">
                  <bk-table
                    class="bk-host-table f14"
                    :show-header="false"
                    :data="localData.proxy.config.upstreams.hosts"
                    size="small"
                    :border="true"
                    v-if="localData.proxy.config.upstreams.loadbalance === 'weighted-roundrobin'">
                    <div slot="empty">
                      <table-empty empty />
                    </div>
                    <bk-table-column :show-overflow-tooltip="true" label="Host" prop="host"></bk-table-column>
                    <bk-table-column :width="60" label="weight" prop="weight"></bk-table-column>
                  </bk-table>
                  <ul class="ag-list" v-else>
                    <li v-for="hostItem of localData.proxy.config.upstreams.hosts" :key="hostItem.host">
                      {{hostItem.host}}
                    </li>
                  </ul>
                </div>
              </div>
            </div>
          </bk-col>
        </bk-row>

        <bk-row :class="{ 'ag-diff': checkDiff('localData.proxy.config.timeout') }">
          <bk-col :span="4">
            <label class="ag-key" style="line-height: 32px;">{{ $t('超时时间') }}:</label>
          </bk-col>
          <bk-col :span="10">
            <div class="bk-button-group" :class="{ 'button-diff': checkDiff('localData.proxy.config.timeout') }" style="display: flex;">
              <div class="readonly-value">{{ localData.useDefaultTimeout ? $t('使用环境配置') : $t('覆盖环境配置') }}</div>
            </div>

            <div class="detail-wrapper" v-if="!localData.useDefaultTimeout" :class="{ 'wrapper-diff': checkDiff('localData.proxy.config.timeout') }">
              <div class="content-item">
                <span class="key"> {{ $t('超时时间') }}： </span>
                <span class="value">{{localData.proxy.config.timeout}} {{ $t('秒') }}</span>
              </div>
            </div>
          </bk-col>
        </bk-row>

        <bk-row :class="{ 'ag-diff': checkDiff('localData.proxy.config.transform_headers') }">
          <bk-col :span="4">
            <label class="ag-key" style="line-height: 32px;">{{ $t('Header转换') }}:</label>
          </bk-col>
          <bk-col :span="10">
            <div class="bk-button-group" :class="{ 'button-diff': checkDiff('localData.proxy.config.transform_headers') }" style="display: flex;">
              <div class="readonly-value">{{ localData.useDefaultHeader ? $t('使用环境配置') : $t('追加环境配置') }}</div>
            </div>
            <div class="detail-wrapper" v-if="!localData.useDefaultHeader" :class="{ 'wrapper-diff': checkDiff('localData.proxy.config.transform_headers') }">
              <div class="content-item mb5">
                <span class="key"> {{ $t('设置') }}： </span>
                <div class="value">
                  <ul class="ag-list" v-if="isEmptyObject(localData.proxy.config.transform_headers.set)">
                    <li v-for="(addItem, index) in localData.proxy.config.transform_headers.set" :key="index">
                      <div class="ds-key">{{index}} : </div>
                      <div class="ds-value">{{addItem}}</div>
                    </li>
                  </ul>
                                    
                  <span v-else>--</span>
                </div>
              </div>
              <div class="content-item">
                <span class="key"> {{ $t('删除') }}： </span>
                <div class="value">
                  <ul class="ag-list" v-if="localData.proxy.config.transform_headers.delete && localData.proxy.config.transform_headers.delete.length">
                    <li v-for="deleteItem of localData.proxy.config.transform_headers.delete" :key="deleteItem">
                      {{deleteItem}}
                    </li>
                  </ul>
                  <span v-else>--</span>
                </div>
              </div>
            </div>
          </bk-col>
        </bk-row>
      </template>

      <template v-if="localData.proxy.type === 'mock'">
        <bk-row :class="{ 'ag-diff': checkDiff('localData.proxy.config.code') }">
          <bk-col :span="4">
            <label class="ag-key">Status Code:</label>
          </bk-col>
          <bk-col :span="10">
            <div class="ag-value">{{localData.proxy.config.code || '--'}}</div>
          </bk-col>
        </bk-row>

        <bk-row :class="{ 'ag-diff': checkDiff('localData.proxy.config.body') }">
          <bk-col :span="4">
            <label class="ag-key">Response Body:</label>
          </bk-col>
          <bk-col :span="10">
            <div class="ag-value">
              <pre class="ag-pre mt0" v-if="localData.proxy.config.body">{{localData.proxy.config.body || '--'}}</pre>
              <span v-else>--</span>
            </div>
          </bk-col>
        </bk-row>

        <bk-row :class="{ 'ag-diff': checkDiff('localData.proxy.config.headers') }">
          <bk-col :span="4">
            <label class="ag-key">Headers:</label>
          </bk-col>
          <bk-col :span="10">
            <div v-if="isEmptyObject(localData.proxy.config.headers)">
              <ul class="ag-list">
                <li v-for="(headerItem, index) in localData.proxy.config.headers" :key="index">
                  {{index}} : {{headerItem}}
                </li>
              </ul>
            </div>
            <span v-else>--</span>
          </bk-col>
        </bk-row>
      </template>
    </bk-container>

    <p class="title mt15" :class="{ 'ag-diff': checkAuthConfigDiff() }"> {{ $t('安全设置') }} </p>
    <bk-container class="ag-kv-box" :col="14" :margin="6" v-if="localData.contexts.resource_auth.config">
      <bk-row
        :class="{ 'ag-diff': checkDiff('localData.contexts.resource_auth.config.app_verified_required') }"
        v-if="localData.contexts.resource_auth.config.hasOwnProperty('app_verified_required')">
        <bk-col :span="4">
          <label class="ag-key">{{ $t('应用认证') }}:</label>
        </bk-col>
        <bk-col :span="10">
          <div class="ag-value">{{localData.contexts.resource_auth.config.app_verified_required ? $t('是') : $t('否')}}</div>
        </bk-col>
      </bk-row>

      <bk-row
        :class="{ 'ag-diff': checkDiff('localData.contexts.resource_auth.config.resource_perm_required') }"
        v-if="localData.contexts.resource_auth.config.hasOwnProperty('resource_perm_required')">
        <bk-col :span="4">
          <label class="ag-key">{{ $t('校验访问权限') }}:</label>
        </bk-col>
        <bk-col :span="10">
          <div class="ag-value">{{localData.contexts.resource_auth.config.resource_perm_required ? $t('是') : $t('否')}}</div>
        </bk-col>
      </bk-row>

      <bk-row
        :class="{ 'ag-diff': checkDiff('localData.contexts.resource_auth.config.auth_verified_required') }"
        v-if="localData.contexts.resource_auth.config.hasOwnProperty('auth_verified_required')">
        <bk-col :span="4">
          <label class="ag-key">{{ $t('用户认证') }}:</label>
        </bk-col>
        <bk-col :span="10">
          <div class="ag-value">{{localData.contexts.resource_auth.config.auth_verified_required ? $t('是') : $t('否')}}</div>
        </bk-col>
      </bk-row>

      <bk-row :class="{ 'ag-diff': checkDiff('localData.disabled_stages') }">
        <bk-col :span="4">
          <label class="ag-key">{{ $t('禁用环境') }}:</label>
        </bk-col>
        <bk-col :span="10">
          <div class="ag-value">{{localData.disabled_stages.join('; ') || '--'}}</div>
        </bk-col>
      </bk-row>
    </bk-container>

    <p class="title mt15" :class="{ 'ag-diff': checkAuthConfigDiff() }"> {{ $t('资源文档') }} </p>
    <bk-container class="ag-kv-box" :col="14" :margin="6">
      <bk-row :class="{ 'ag-diff': checkDiff('localData.doc_updated_time') }">
        <bk-col :span="4">
          <label class="ag-key">{{ $t('文档更新时间') }}:</label>
        </bk-col>
        <bk-col :span="10">
          <div class="ag-value">
            <template v-if="localLanguage === 'en'">
              {{ localData.doc_updated_time.en || '--' }}
            </template>
            <template v-else>
              {{ localData.doc_updated_time.zh || '--' }}
            </template>
          </div>
        </bk-col>
      </bk-row>
    </bk-container>
  </div>
</template>

<script>
  import dayjs from 'dayjs'

  export default {
    props: {
      curResource: {
        type: Object,
        default () {
          return null
        }
      },
      diffData: {
        type: Object,
        default: () => {}
      },
      onlyShowDiff: {
        type: Boolean,
        default: false
      }
    },
    data () {
      return {
        weightMap: {
          'roundrobin': this.$t('轮询(Round-Robin)'),
          'weighted-roundrobin': this.$t('加权轮询(Weighted Round-Robin)')
        },
        diffMap: {},
        localData: {
          name: '',
          disabled_stages: [],
          config: {},
          proxy: {
            type: '',
            config: {
              transform_headers: {
                add: []
              }
            }
          },
          useDefaultTimeout: true,
          useDefaultHeader: true,
          useDefaultHost: true,
          contexts: {
            resource_auth: {
              config: {}
            }
          }
        }
      }
    },
    computed: {
      localLanguage () {
        return this.$store.state.localLanguage
      }
    },
    watch: {
      curResource () {
        this.initDiff()
        this.initLocalData()
      }
    },
    created () {
      this.initDiff()
      this.initLocalData()
    },
    methods: {
      formatDate (value) {
        if (value) {
          return dayjs(value).format('YYYY-MM-DD HH:mm:ss')
        }
        return '--'
      },
      isEmptyObject (data) {
        if (data) {
          const keys = Object.keys(data)
          return !!keys.length
        } else {
          return false
        }
      },
      isString (str) {
        return typeof str === 'string'
      },
      initLocalData () {
        const data = JSON.parse(JSON.stringify(this.curResource))

        if (data.contexts.resource_auth.config) {
          if (this.isString(data.contexts.resource_auth.config)) {
            data.contexts.resource_auth.config = JSON.parse(data.contexts.resource_auth.config)
          }
        } else {
          data.config = {}
        }

        if (data.proxy.config) {
          if (this.isString(data.proxy.config)) {
            data.proxy.config = JSON.parse(data.proxy.config)
          }
        } else {
          data.proxy.config = {}
        }

        if (data.proxy.type === 'http') {
          data.useDefaultTimeout = !data.proxy.config.timeout

          if (JSON.stringify(data.proxy.config.upstreams) === '{}') {
            data.useDefaultHost = true
          } else {
            data.useDefaultHost = false
          }

          if (JSON.stringify(data.proxy.config.transform_headers) === '{}') {
            data.useDefaultHeader = true
          } else {
            data.useDefaultHeader = false
          }
        }
        this.localData = data
      },

      initDiff () {
        this.diffMap = {}
        if (!this.diffData) {
          return false
        }
        this.findAllDiff(this.diffData)

        // 处理后端配置使用默认配置情况
        if (this.diffMap.hasOwnProperty('localData.proxy.config.timeout')) {
          this.diffMap['localData.useDefaultTimeout'] = true
        }

        if (this.diffMap['localData.proxy.config.upstreams'] === '{}') {
          this.diffMap['localData.useDefaultHost'] = true
        }

        if (this.diffMap['localData.proxy.config.transform_headers'] === '{}') {
          this.diffMap['localData.useDefaultHeader'] = true
        }

        // 处理安全设置禁用环境
        const keys = Object.keys(this.diffMap)
        if (keys.some(item => item.startsWith('localData.disabled_stages'))) {
          this.diffMap['localData.disabled_stages'] = true
        }
      },

      findAllDiff (value, prePath = 'localData', index) {
        if (Array.isArray(value)) {
          if (value.length) {
            value.forEach((item, index) => {
              const path = `${prePath}`
              this.findAllDiff(item, path, index)
            })
          } else {
            this.diffMap[prePath] = '[]'
          }
        } else if (typeof value === 'object') {
          if (JSON.stringify(value) === '{}') {
            this.diffMap[prePath] = '{}'
          } else {
            for (const key in value) {
              const path = `${prePath}.${key}`
              this.findAllDiff(value[key], path)
            }
          }
        } else {
          this.diffMap[prePath] = value
        }
      },

      checkDiff (path) {
        const keys = Object.keys(this.diffMap)
        return keys.some(item => item.startsWith(path))
      },

      checkAuthConfigDiff () {
        return this.checkDiff('localData.contexts.resource_auth.config.app_verified_required')
          || this.checkDiff('localData.contexts.resource_auth.config.auth_verified_required')
          || this.checkDiff('localData.contexts.resource_auth.config.resource_perm_required')
          || this.checkDiff('localData.disabled_stages')
      }
    }
  }
</script>

<style lang="postcss" scoped>
    @import '@/css/variable.css';

    .ag-dl {
        padding: 15px 40px 5px 30px;
    }

    .ag-diff {
        .ag-value {
            color: #FE9C00 !important;
        }

        .ag-pre {
            background: #fbf4e9;
            color: #FE9C00;
        }

        .ag-list {
            background: #fbf4e9;
        }
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
            font-size: 13px;
            margin-bottom: 10px;
            line-height: 1;
            display: block;
        }

        p {
            font-size: 12px;
            color: #63656E;
        }
    }

    .detail-wrapper {
        padding: 10px 20px 10px 10px;
        background: #F0F1F5;
        margin-top: 6px;
        border-radius: 2px;

        &.wrapper-diff {
            background: #fbf4e9;
        }

        .content-item {
            display: flex;
            font-size: 13px;
            line-height: 26px;
        }

        .key {
            width: 100px;
            text-align: right;
            display: inline-block;
            vertical-align: middle;
            color: #63656E;
            line-height: 28px;
        }
        .value {
            color: #313238;
            flex: 1;
        }
    }

    .ag-list {
        border-radius: 2px;
        border: 1px solid #DCDEE5;
        background: #FFF;
        font-size: 13px;

        > li {
            line-height: 22px;
            padding: 0 15px;
            display: flex;
            padding: 5px 10px;
            background: #FFF;

            .ds-key {
                white-space: nowrap;
            }
            .ds-value {
                white-space: normal;
                word-break: break-all;
                padding-left: 5px;
            }

            & + li {
                border-top: 1px solid #DCDEE5;
            }
        }
    }

    .ag-tab-button {
        cursor: default;
        &:hover {
            border-color: #c4c6cc;
            color: #63656e;
        }
        &.is-selected {
            border-color: #3a84ff !important;
            color: #3a84ff !important;
            a {
                color: #3a84ff !important;
            }
        }
    }

    .ag-value {
        white-space: normal;
        word-break: break-all;
    }

    /deep/ .bk-host-table {
        tr {
            background: #FFF !important;
        }
        td,
        th {
            height: 36px;
            background: #FFF !important;
        }
    }

    .ag-kv-box {
        &.box-diff {
            background: #fbf4e9;
            border-radius: 2px;
            padding-top: 10px;
            padding-bottom: 10px;

            .ag-value,
            .ag-list {
                color: #FE9C00;
            }
        }

        .ag-key,
        .ag-value {
            font-size: 13px;
        }
    }

    .ag-resource-item {
        &.show-diff {
            .title {
                display: none;

                &.ag-diff {
                    display: block;
                }
            }
            
            /deep/ .bk-grid-row {
                display: none;

                &.ag-diff {
                    display: block;
                }
            }

            .box-diff {
                /deep/ .bk-grid-row {
                    display: block;
                }
            }
        }
    }
</style>

<style lang="postcss" scoped>
    .bk-button-group .readonly-value {
        height: 32px;
        line-height: 32px;
        font-size: 13px;
        color: #313238;
    }
</style>

<style lang="postcss">
    .source-version {
        .detail-wrapper.wrapper-diff {
            background: #F0F1F5;
        }

        .ag-diff .ag-pre {
            background: #313238;
            color: #FFF;
        }

        .ag-value,
        .ag-list {
            color: #313238 !important;
        }

        .ag-diff .ag-list {
            background: #FFF;
        }

        .ag-diff .ag-value {
            color: #313238 !important;
        }

        .ag-kv-box.box-diff {
            background: #FFF;
        }
    }
</style>
