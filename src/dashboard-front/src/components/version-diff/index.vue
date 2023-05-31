<template>
  <div class="ag-version-diff-box">
    <p class="summary-data">
      <strong class="ag-strong" style="color: #63656E;"> {{ $t('对比结果') }}： </strong>
      <template v-if="isDataLoading">
        <div class="bk-spin-loading bk-spin-loading-mini bk-spin-loading-primary">
          <div class="rotate rotate1"></div>
          <div class="rotate rotate2"></div>
          <div class="rotate rotate3"></div>
          <div class="rotate rotate4"></div>
          <div class="rotate rotate5"></div>
          <div class="rotate rotate6"></div>
          <div class="rotate rotate7"></div>
          <div class="rotate rotate8"></div>
        </div>
        {{ $t('正在努力对比中…') }}
      </template>
      <template v-else-if="localSourceId && localTargetId">
        <template> {{ $t('新增') }} <strong class="ag-strong success m5">{{diffData.add.length}}</strong> {{ $t('个资源') }}， </template>
        <template> {{ $t('删除') }} <strong class="ag-strong danger m5">{{diffData.delete.length}}</strong> {{ $t('个资源') }}， </template>
        <template> {{ $t('更新') }} <strong class="ag-strong warning m5">{{diffData.update.length}}</strong> {{ $t('个资源') }} </template>
      </template>
      <template v-else>
        --
      </template>
    </p>

    <div class="search-data mb15">
      <bk-input
        clearable
        class="fl mr10"
        style="width: 365px;"
        :placeholder="$t('请输入资源名称或请求路径，回车结束')"
        :right-icon="'bk-icon icon-search'"
        v-model="searchParams.keyword"
        @enter="handleSearch"
        @clear="handleClear">
      </bk-input>
      <bk-select
        class="fl mr10"
        v-model="searchParams.diffType"
        style="width: 240px;"
        :clearable="true"
        :placeholder="$t('全部差异类型')">
        <bk-option v-for="option in diffTypeList"
          :key="option.id"
          :id="option.id"
          :name="option.name">
        </bk-option>
      </bk-select>
      <bk-checkbox
        class="fl"
        style="margin-top: 6px;"
        :true-value="true"
        :false-value="false"
        v-model="searchParams.onlyUpdated">
        {{ $t('仅显示有差异的资源属性') }}
      </bk-checkbox>

      <ul class="tag-list fr">
        <li>
          <span class="tag success"></span> {{ $t('新增') }}
        </li>
        <li>
          <span class="tag danger"></span> {{ $t('删除') }}
        </li>
        <li>
          <span class="tag warning"></span> {{ $t('更新') }}
        </li>
      </ul>
    </div>

    <div :class="['diff-wrapper', { 'no-result': !hasResult }]">
      <div class="diff-header">
        <div class="source-header">
          <div class="marked">{{sourceTag}}</div>
          <div class="version">
            <bk-select
              class="fl mr10"
              v-model="localSourceId"
              v-if="sourceSwitch"
              :placeholder="$t('请选择源版本')"
              :clearable="false"
              :searchable="true"
              style="width: 320px;"
              @change="handleVersionChange">
              <bk-option v-for="option in localVersionList"
                :key="option.id"
                :id="option.id"
                :disabled="option.id === localTargetId"
                :name="option.resource_version_display">
              </bk-option>
            </bk-select>
            <strong class="title" v-else>{{sourceVersion.title}} ({{sourceVersion.name}})</strong>
          </div>
        </div>
        <div class="target-header">
          <div class="version">
            <template>
              <bk-select
                class="fl mr10"
                v-model="localTargetId"
                v-if="targetSwitch"
                :placeholder="$t('请选择源版本')"
                :clearable="false"
                :searchable="true"
                style="width: 320px;"
                @change="handleVersionChange">
                <bk-option v-for="option in localVersionList"
                  :key="option.id"
                  :id="option.id"
                  :disabled="option.id === localSourceId"
                  :name="option.resource_version_display">
                </bk-option>
              </bk-select>
              <strong class="title" v-else>{{targetVersion.title}} ({{targetVersion.name}})</strong>
            </template>
            <!-- <strong class="title" v-else>当前资源列表</strong> -->
          </div>
          <div class="marked">{{targetTag}}</div>
        </div>
        <button class="switch-btn" @click="handleSwitch" v-if="targetSwitch && sourceSwitch && localSourceId">
          <i class="apigateway-icon icon-ag-exchange-line"></i>
        </button>
      </div>
            
      <div class="diff-main">
        <ag-loader
          :is-loading="isDataLoading"
          :offset-top="0"
          :offset-left="12"
          :width="width"
          :height="240"
          loader="diff-loader"
          style="margin-top: 12px;"
          background-color="#FFF">
          <!-- 新增 -->
          <div class="diff-item" v-for="(addItem) of diffData.add" :key="addItem.id" v-if="checkMatch(addItem, 'add')">
            <div class="source-box">
              <div class="metadata pl10" @click="handleToggle(addItem)">
                <i :class="['bk-icon icon-right-shape', { 'active': addItem.isExpanded }]"></i>
                <span v-bk-overflow-tips class="vm resource-title ml10">--</span>
              </div>
              <div class="resource-box pl15 pr15">
                <bk-transition :name="animation">
                  <bk-exception class="exception-part" type="empty" scene="part" v-show="addItem.isExpanded"> {{ $t('此版本无该资源') }} </bk-exception>
                </bk-transition>
              </div>
            </div>
            <div class="target-box">
              <div class="metadata success" @click="handleToggle(addItem)">
                <i :class="['bk-icon icon-right-shape', { 'active': addItem.isExpanded }]"></i>
                <span v-bk-overflow-tips class="vm resource-title" v-html="renderTitle(addItem)"></span>
              </div>
              <div class="resource-box pl15 pr15">
                <bk-transition :name="animation">
                  <resource-detail :cur-resource="addItem" v-show="addItem.isExpanded"></resource-detail>
                </bk-transition>
              </div>
            </div>
          </div>

          <!-- 删除 -->
          <div class="diff-item" v-for="(deleteItem) of diffData.delete" :key="deleteItem.id" v-if="checkMatch(deleteItem, 'delete')">
            <div class="source-box">
              <div class="metadata" @click="handleToggle(deleteItem)">
                <i :class="['bk-icon icon-right-shape', { 'active': deleteItem.isExpanded }]"></i>
                <span v-bk-overflow-tips class="vm resource-title" v-html="renderTitle(deleteItem)"></span>
              </div>
              <div class="resource-box pl15 pr15">
                <bk-transition :name="animation">
                  <resource-detail :cur-resource="deleteItem" v-show="deleteItem.isExpanded"></resource-detail>
                </bk-transition>
              </div>
            </div>
            <div class="target-box">
              <div class="metadata danger" @click="handleToggle(deleteItem)">
                <i :class="['bk-icon icon-right-shape', { 'active': deleteItem.isExpanded }]"></i>
                <span v-bk-overflow-tips class="vm resource-title" v-html="renderTitle(deleteItem)"></span>
              </div>
              <div class="resource-box pl15 pr15">
                <!-- <bk-transition :name="animation">
                                    <svg class="delete-icon" aria-hidden="true" v-show="deleteItem.isExpanded">
                                        <use xlink:href="#icon-ag-yishanchu"></use>
                                    </svg>
                                </bk-transition> -->
                                
                <bk-transition :name="animation">
                  <resource-detail style="opacity: 0.35;" :cur-resource="deleteItem" v-show="deleteItem.isExpanded"></resource-detail>
                </bk-transition>
              </div>
            </div>
          </div>

          <!-- 更新 -->
          <div class="diff-item" v-for="(updateItem) of diffData.update" :key="`${updateItem.source.id}:${updateItem.target.id}`" v-if="checkMatch(updateItem.source, 'update') || checkMatch(updateItem.target, 'update')">
            <div class="source-box">
              <div class="metadata" @click="handleToggle(updateItem)">
                <i :class="['bk-icon icon-right-shape', { 'active': updateItem.isExpanded }]"></i>
                <span v-bk-overflow-tips class="vm resource-title" v-html="renderTitle(updateItem.source)"></span>
              </div>
              <div class="resource-box pl15 pr15">
                <bk-transition :name="animation">
                  <resource-detail class="source-version" :cur-resource="updateItem.source" v-show="updateItem.isExpanded" :diff-data="updateItem.target.diff" :only-show-diff="searchParams.onlyUpdated"></resource-detail>
                </bk-transition>
              </div>
            </div>
            <div class="target-box">
              <div class="metadata warning" @click="handleToggle(updateItem)">
                <i :class="['bk-icon icon-right-shape', { 'active': updateItem.isExpanded }]"></i>
                <span v-bk-overflow-tips class="vm resource-title" v-html="renderTitle(updateItem.target)"></span>
              </div>
              <!-- {{updateItem.source.diff}} -->

              <div class="resource-box pl15 pr15">
                <bk-transition :name="animation">
                  <resource-detail :cur-resource="updateItem.target" v-show="updateItem.isExpanded" :diff-data="updateItem.source.diff" :only-show-diff="searchParams.onlyUpdated"></resource-detail>
                </bk-transition>
              </div>
            </div>
          </div>

          <!-- 无数据 -->
          <bk-exception class="mt50" type="search-empty" scene="part" v-if="!hasResult">
            {{ !localSourceId ? $t('请选择源版本') : (!localTargetId ? $t('请选择目标版本') : (hasFilter ? $t('无匹配内容') : $t('版本资源配置无差异'))) }}
          </bk-exception>
        </ag-loader>
      </div>
    </div>
  </div>
</template>

<script>
  import resourceDetail from '@/components/resource-detail'
  import { catchErrorHandler } from '@/common/util'
  import i18n from '@/language/i18n.js'

  export default {
    components: {
      resourceDetail
    },
    props: {
      versionList: {
        type: Array,
        default: () => []
      },
      apigwId: {
        type: [Number, String],
        default: ''
      },
      sourceId: {
        type: [Number, String],
        default: ''
      },
      targetId: {
        type: [Number, String],
        default: ''
      },
      sourceSwitch: {
        type: Boolean,
        default: true
      },
      targetSwitch: {
        type: Boolean,
        default: true
      },
      curDiffEnabled: {
        type: Boolean,
        default: true
      },
      sourceTag: {
        type: String,
        default: i18n.t('源版本')
      },
      targetTag: {
        type: String,
        default: i18n.t('目标版本')
      }
    },
    data () {
      return {
        width: 1240,
        isDataLoading: false,
        localSourceId: this.sourceId,
        localTargetId: this.targetId || 'current',
        localVersionList: this.versionList,
        diffData: {
          add: [],
          delete: [],
          update: []
        },
        animation: 'collapse',
        searchKeyword: '',
        searchParams: {
          keyword: '',
          diffType: '',
          onlyUpdated: false
        },
        diffTypeList: [
          {
            id: 'add',
            name: this.$t('新增')
          },
          {
            id: 'delete',
            name: this.$t('删除')
          },
          {
            id: 'update',
            name: this.$t('更新')
          }

        ]
      }
    },
    computed: {
      hasResult () {
        const addItem = this.diffData.add.some(item => {
          return this.checkMatch(item, 'add')
        })

        const deleteItem = this.diffData.delete.some(item => {
          return this.checkMatch(item, 'delete')
        })

        const updateItem = this.diffData.update.some(item => {
          return this.checkMatch(item.source, 'update') || this.checkMatch(item.target, 'update')
        })

        return addItem || deleteItem || updateItem || this.isDataLoading
      },
      hasFilter () {
        return this.searchKeyword || this.searchParams.diffType
      },
      sourceVersion () {
        const match = this.localVersionList.find(item => item.id === this.localSourceId)
        if (match) {
          return match
        }
        return {
          id: '',
          title: '',
          name: ''
        }
      },
      targetVersion () {
        const match = this.localVersionList.find(item => item.id === this.localTargetId)
        if (match) {
          return match
        }
        return {
          id: '',
          title: '',
          name: ''
        }
      }
    },
    watch: {
      sourceId () {
        this.localSourceId = this.sourceId
      },
      targetId () {
        this.localTargetId = this.targetId
      }
    },
    created () {
      this.width = window.innerWidth <= 1280 ? 1000 : 1240
      this.init()
    },
    methods: {
      init () {
        this.getDiffData()
        this.getApigwVersions()
      },
      handleToggle (item) {
        item.isExpanded = !item.isExpanded
      },

      handleSearch () {
        this.searchKeyword = this.searchParams.keyword
      },

      handleClear () {
        this.searchKeyword = ''
      },

      handleSwitch () {
        [this.localSourceId, this.localTargetId] = [this.localTargetId, this.localSourceId]
        this.getDiffData()
      },

      checkMatch (item, type) {
        if (this.searchParams.diffType && this.searchParams.diffType !== type) {
          return false
        }
        const method = item.method.toLowerCase()
        const path = item.path.toLowerCase()
        const keyword = this.searchKeyword.toLowerCase()
        return method.indexOf(keyword) > -1 || path.indexOf(keyword) > -1
      },

      renderTitle (item) {
        let method = item.method
        let path = item.path
        if (this.searchKeyword) {
          const reg = new RegExp(`(${this.searchKeyword})`, 'ig')
          method = method.replace(reg, `<i class="keyword ag-strong primary">$1</i>`)
          path = path.replace(reg, `<i class="keyword ag-strong primary">$1</i>`)
        }
                
        return `【${method}】${path}`
      },

      handleVersionChange () {
        this.searchParams = {
          keyword: '',
          diffType: '',
          onlyUpdated: false
        }
        this.searchKeyword = ''
        this.getDiffData()
      },

      async getDiffData () {
        if (!this.localSourceId) {
          return false
        }

        if (this.isDataLoading) {
          return false
        }
        this.isDataLoading = true
        this.diffData = {
          add: [],
          delete: [],
          update: []
        }

        try {
          const res = await this.$store.dispatch('version/getVersionDiff', {
            apigwId: this.apigwId,
            sourceId: String(this.localSourceId).replace('current', ''),
            targetId: String(this.localTargetId).replace('current', '')
          })
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
        } finally {
          setTimeout(() => {
            this.isDataLoading = false
          }, 1000)
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
            item.stage_text = item.released_stages.map(item => {
              return item.name
            })
          })
                    
          if (this.curDiffEnabled) {
            this.localVersionList = [
              {
                id: 'current',
                name: this.$t('当前最新资源列表'),
                resource_version_display: this.$t('当前最新资源列表')
              },
              ...res.data.results
            ]
          } else {
            this.localVersionList = res.data.results
          }
        } catch (e) {
          catchErrorHandler(e, this)
        }
      }
    }
  }
</script>

<style lang="postcss" scoped>
    .summary-data {
        margin-bottom: 15px;
        font-size: 14px;
        color: #63656E;
    }

    .search-data {
        &::after {
            content: '';
            display: table;
            clear: both;
        }
    }

    .tag-list {
        height: 32px;
        line-height: 32px;

        li {
            display: inline-block;
            margin-left: 10px;
            font-size: 13px;
            color: #63656E;

            .tag {
                width: 10px;
                height: 10px;
                display: inline-block;
                margin-right: 5px;

                &.success {
                    background: #dcffe2;
                    border: 1px solid #94f5a4;
                }

                &.danger {
                    background: #ffe9e8;
                    border: 1px solid #ffbdbd;
                }

                &.warning {
                    background: #ffefd6;
                    border: 1px solid #ffe3b5;
                }
            }
        }
    }

    .diff-wrapper {
        border: 1px solid #DCDEE5;
        border-radius: 2px;
        min-height: 300px;
        position: relative;

        &.no-result {
            &::after {
                display: none;
            }
        }

        &::after {
            content: '';
            display: inline-block;
            position: absolute;
            width: 2px;
            background: #dbdee4;
            left: 50%;
            top: 0;
            height: 100%;
            z-index: 100;
            margin-left: -1px;
        }
    }

    .diff-main {
        /* padding-bottom: 12px; */
    }

    .diff-item {
        &:not(:first-child) {
            margin-top: -12px;
        }
        .source-box,
        .target-box {
            padding: 12px 12px 12px 12px;

            .metadata {
                height: 36px;
                line-height: 36px;
                border-radius: 2px;
                background: #F0F1F5;
                border: 1px solid #F0F1F5;
                font-size: 12px;
                font-weight: bold;
                color: #63656E;
                padding-left: 10px;
                cursor: pointer;

                .resource-title {
                    position: relative;
                    max-width: 550px;
                    overflow: hidden;
                    text-overflow: ellipsis;
                    white-space: nowrap;
                    display: inline-block;
                }

                .bk-icon {
                    display: inline-block;
                    transform-origin: center;
                    transition: all ease 0.3s;

                    &.active {
                        transform: rotate(90deg);
                    }
                }

                &.danger {
                    background: #FEDDDC;
                    border-color: #FE9C9C;

                    .resource-title {
                        &::after {
                            content: '';
                            width: 100%;
                            height: 1px;
                            background: #63656E;
                            position: absolute;
                            left: 0;
                            top: 50%;
                        }
                    }
                }

                &.success {
                    background: #DCFFE2;
                    border-color: #94F5A4;
                }

                &.warning {
                    background: #FFE8C3;
                    border-color: #FFD694;
                }
            }
        }

        .source-box {
            border-right: 1px solid #DCDEE5;
        }

        .target-box {
            border-left: 1px solid #DCDEE5;
        }

        .resource-box {
            height: calc(100% - 36px);
            position: relative;

            .exception-part {
                position: absolute;
                left: 0;
                top: calc(50% - 40px);
                transform: translateY(-50%);
            }
        }

        .delete-icon {
            width: 68px;
            height: 68px;
            position: absolute;
            right: 20px;
            top: 20px;
            z-index: 10;
        }
    }

    .diff-header {
        display: flex;
        position: relative;

        .switch-btn {
            position: absolute;
            left: 50%;
            top: 50%;
            width: 27px;
            height: 27px;
            background: #FFF;
            box-shadow: 0px 2px 4px 0px rgba(0,0,0,0.1);
            transform: translateY(-50%) translateX(-50%);
            border: none;
            border-radius: 50%;
            color: #63656E;
            z-index: 110;

            &:hover {
                color: #3A84FF;
            }

            i {
                margin-top: -4px;
                display: inline-block;
                vertical-align: middle;
            }
        }

        .source-header,
        .target-header {
            width: 50%;
            height: 42px;
            background: #F0F1F5;
            line-height: 42px;
            display: flex;

            .marked {
                width: 130px;
                text-align: center;
                font-size: 13px;
                color: #63656E;
            }

            .version {
                flex: 1;
                text-align: center;
                position: relative;

                /deep/ .bk-select {
                    margin: 5px 0 0 0;
                    background: transparent;
                    border: none;
                    position: absolute;
                    left: 50%;
                    transform: translateX(-50%);

                    &.is-focus {
                        box-shadow: none;
                    }

                    &.is-default-trigger.is-unselected:before {
                        width: 280px;
                        font-weight: bold;
                        color: #63656E;
                        font-size: 13px;
                        text-align: center;
                    }

                    .bk-select-name {
                        font-size: 13px;
                        font-weight: bold;
                        color: #63656E;
                        text-align: center;
                    }
                }
            }

            .title {
                flex: 1;
                font-size: 13px;
                color: #63656E;
                text-align: center;
            }
        }

        .source-header {
            border-right: 1px solid #DCDEE5;
            border-bottom: 1px solid #DCDEE5;

            .marked {
                border-right: 1px solid #DCDEE5;
            }
        }

        .target-header {
            background: #DCDEE5;
            border-left: 1px solid #C4C6CC;
            border-bottom: 1px solid #C4C6CC;

            .marked {
                border-left: 1px solid #C4C6CC;
            }
        }
    }
    .diff-item {
        display: flex;

        .source-box,
        .target-box {
            width: 50%;
        }
    }
</style>
