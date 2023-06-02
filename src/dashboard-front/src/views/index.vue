<template>
  <div class="index-container mt30">
    <ag-loader
      :class="['ap-content', { 'gateway-wrapper': apigwList.length > 10 }]"
      :is-loading="isDataLoading"
      :loader="'index-loader'"
      :offset-top="0"
      :offset-left="0"
      :height="500">
      <section class="header clearfix">
        <!-- 不跟随页面滚动 -->
        <div class="content">
          <h3 class="title fl"> {{ $t('我的网关') }} ({{apigwList.length}})</h3>
          <bk-select
            v-model="filterKey"
            class="fr filter-selected"
            :class="{ 'en-wd': localLanguage === 'en' }"
            ext-popover-cls="filter-selected-options"
            prefix-icon="bk-icon icon-sort"
            :clearable="false"
            @change="gatewaySort"
          >
            <bk-option id="created_time" :name="$t('创建时间')"></bk-option>
            <bk-option id="updated_time" :name="$t('更新时间')"></bk-option>
            <bk-option id="name" :name="$t('字母 A-Z')"></bk-option>
          </bk-select>
          <bk-input
            class="fr mr8"
            style="width: 300px; display: inline-block;"
            :placeholder="$t('请输入网关名，按Enter搜索')"
            :clearable="true"
            :right-icon="'bk-icon icon-search'"
            v-model="keyword"
            @enter="handleSearch">
          </bk-input>
          <bk-button theme="primary" class="fr mr8" @click="goCreateApigw"> {{ $t('创建网关') }} </bk-button>
        </div>
      </section>
      <table class="data-table" v-bkloading="{ isLoading: isLoading, zIndex: 10 }">
        <thead class="apigw-table-thead">
          <tr>
            <th class="name"> {{ $t('网关名') }} </th>
            <th class="desc"> {{ $t('描述') }} </th>
            <th class="creator"> {{ $t('创建者') }} </th>
            <th class="env"> {{ $t('环境列表') }} </th>
            <th class="resource"> {{ $t('资源数量') }} </th>
            <th class="action"> {{ $t('操作') }} </th>
          </tr>
        </thead>
        <tbody>
          <template v-if="apigwList.length">
            <tr v-for="apigw of apigwList" :key="apigw.id" :class="{ 'apigw-disabled': apigw.status === 0 }">
              <td colspan="6">
                <div :class="['data-item', { 'new-created': apigw.isNewCreated }]">
                  <div class="name info-wrapper" @click="handleGoPage('apigwResource', apigw)">
                    <div>
                      <span class="logo">{{apigw.name[0].toUpperCase()}}</span>
                    </div>
                    <div class="text-wrapper">
                      <span v-bk-tooltips.top="apigw.name" class="mr5" :class="[`${filtersOne(apigw)}`]">{{apigw.name}}</span>
                      <span class="ag-tag disabled" v-if="apigw.status === 0"> {{ $t('已停用') }} </span>
                      <span v-if="apigw.is_official" class="official-tips"> {{ $t('官方') }} </span>
                      <span v-if="apigw.hosting_type === 1" class="tips" v-bk-tooltips="$t('该网关使用专享实例托管资源')"> {{ $t('专享') }} </span>
                    </div>
                  </div>
                  <div class="desc" style="text-align: left;">
                    <template v-if="apigw.description">
                      <p class="ag-text" style="max-width: 180px;" v-bk-overflow-tips>
                        {{apigw.description}}
                      </p>
                    </template>
                    <template v-else>
                      --
                    </template>
                  </div>
                  <div class="creator">{{apigw.created_by || '--'}}</div>
                  <div class="env">
                    <bk-dropdown-menu ref="dropdown">
                      <template slot="dropdown-trigger">
                        <i :class="['ag-dot mr5',{ 'success': apigw.status !== 0 && apigw.stages[0].stage_release_status }]"></i>
                        <span class="text">{{apigw.stages[0].stage_name}} {{apigw.stages[0].stage_release_status ? (apigw.status === 0 ? $t('已停用') : $t('已发布')) : $t('未发布')}}</span>
                        <i :class="['apigateway-icon icon-ag-down-shape']"></i>
                      </template>
                      <div class="ag-detail-panel" slot="dropdown-content">
                        <p class="panel-title"> {{ $t('列表详情') }} </p>
                        <ul class="panel-list">
                          <li v-for="stage of apigw.stages" :key="stage.id">
                            <i :class="['ag-dot', { 'success': apigw.status !== 0 && stage.stage_release_status }]"></i>{{stage.stage_name}} {{stage.stage_release_status ? (apigw.status === 0 ? $t('已停用') : $t('已发布')) : $t('未发布')}}
                          </li>
                        </ul>
                      </div>
                    </bk-dropdown-menu>
                  </div>
                  <div class="resource">{{apigw.resource_count}}</div>
                  <div class="action">
                    <bk-button class="mr10" :text="true" @click="handleGoPage('apigwStage', apigw)"> {{ $t('环境管理') }} </bk-button>
                    <bk-button class="mr10" :text="true" @click="handleGoPage('apigwResource', apigw)"> {{ $t('资源管理') }} </bk-button>
                    <bk-button class="mr10" :text="true" @click="handleGoPage('apigwVersion', apigw)"> {{ $t('版本管理') }} </bk-button>
                    <bk-button class="mr10" :text="true" @click="handleGoPage('apigwAccessLog', apigw)"> {{ $t('流水日志') }} </bk-button>
                  </div>
                </div>
              </td>
            </tr>
          </template>
          <template v-else>
            <tr>
              <td colspan="6">
                <div class="ap-nodata">
                  <table-empty
                    :keyword="tableEmptyConf.keyword"
                    @clear-filter="clearFilterKey"
                  />
                </div>
              </td>
            </tr>
          </template>
        </tbody>
      </table>
    </ag-loader>
  </div>
</template>

<script>
  import _ from 'lodash'

  export default {
    data () {
      return {
        apigwListOrigin: [],
        apigwList: [],
        keyword: '',
        isDataLoading: true,
        tableEmptyConf: {
          keyword: ''
        },
        filterKey: 'updated_time',
        isLoading: false
      }
    },
    computed: {
      localLanguage () {
        return this.$store.state.localLanguage
      }
    },
    watch: {
      keyword (newVal, oldVal) {
        if (oldVal && !newVal) {
          this.handleSearch()
        }
      }
    },
    created () {
      this.init()
    },
    methods: {
      init () {
        this.getApisList()
      },

      async getApisList () {
        try {
          this.isDataLoading = true
          const res = await this.$store.dispatch('apis/getApisList')
          this.apigwListOrigin = [...res.data.results]
          this.apigwList = res.data.results
          this.updateTableEmptyConfig()
          this.highlightLatest()
          this.gatewaySort()
        } catch (e) {
          this.$bkMessage({
            theme: 'error',
            message: e.message || this.$t('接口异常')
          })
        } finally {
          this.isDataLoading = false
          this.$nextTick(() => {
            this.hasElemnetScrollbar('.container-content')
          })
        }
      },

      goCreateApigw () {
        this.$router.push({
          name: 'createApigw'
        })
      },

      handleSearch (event) {
        if (this.keyword) {
          this.apigwList = this.apigwListOrigin.filter(apigw => {
            return apigw.name.toLowerCase().indexOf(this.keyword.toLowerCase()) > -1
          })
        } else {
          this.apigwList = this.apigwListOrigin
        }
        this.updateTableEmptyConfig()
        this.gatewaySort()
      },

      handleApigwInfo (apigw) {
        this.$router.push({
          name: 'apigwInfo',
          params: {
            id: apigw.id
          }
        })
      },

      handleGoPage (routeName, apigw) {
        this.$router.push({
          name: routeName,
          params: {
            id: apigw.id
          }
        })
      },

      filtersOne (data) {
        const tipsArr = []
        if ('status' in data && data.status === 0) {
          tipsArr.push(data.status)
        }
        if (data.is_official) {
          tipsArr.push(data.is_official)
        }
        if (data.hosting_type) {
          tipsArr.push(data.hosting_type)
        }
        let tipsClass = ''
        switch (tipsArr.length) {
          case 1:
            tipsClass = 'name-wrapper-one'
            break
          case 2:
            tipsClass = 'name-wrapper-two'
            break
          case 3:
            tipsClass = 'name-wrapper-three'
            break
          default:
            break
        }
        return tipsClass
      },

      clearFilterKey () {
        this.keyword = ''
      },

      updateTableEmptyConfig () {
        this.tableEmptyConf.keyword = this.keyword
      },
      /**
       * 网关排序
       */
      gatewaySort () {
        if (this.apigwList.length < 2) {
          return
        }
        this.isLoading = true
        try {
          const deepApigwList = _.cloneDeep(this.apigwList)
          if (this.filterKey !== 'name') {
            deepApigwList.sort((a, b) => b[this.filterKey].localeCompare(a[this.filterKey]))
          } else {
            deepApigwList.sort((a, b) => ('' + a[this.filterKey]).localeCompare(b[this.filterKey]))
          }
          this.apigwList = deepApigwList
        } catch (e) {
          console.error(e)
        } finally {
          setTimeout(() => {
            this.isLoading = false
          }, 200)
        }
      },
            
      /**
       * 高亮不超过24小时创建的网关
       */
      highlightLatest () {
        this.apigwList.forEach(item => {
          const createdTime = new Date(item.created_time).getTime()
          const diffTimestamp = Date.now() - createdTime
          const hoursDifference = diffTimestamp / (1000 * 60 * 60)
          if (hoursDifference < 24) {
            item.isNewCreated = true
          }
        })
      },

      /**
       * 当前容器是否存在滚动条
       */
      hasElemnetScrollbar (elClassName) {
        const element = document.querySelector(elClassName)
        const hasVerticalScrollbar = element.scrollHeight > element.clientHeight
        hasVerticalScrollbar ? element.classList.add('content-scroll-cls') : element.classList.remove('content-scroll-cls')
      }
    }
  }
</script>

<style lang="postcss" scoped>
    @import '@/css/variable.css';

    .header {
        position: absolute;
        width: 100%;
        padding-top: 30px;
        top: 0;
        left: 0;
        height: 80px;
        background: #f5f7fa;
        z-index: 9;
        overflow: hidden;
        .content {
            width: 1280px;
            margin: 0 auto;
        }
        .mr8 {
            margin-right: 8px;
        }
    }

    .title {
        font-weight: normal;
        color: #313238;
        padding: 0;
        margin: 0;
        line-height: 32px;
        font-size: 20px;
    }

    .text {
        vertical-align: middle;
        font-size: 14px;
        max-width: 128px;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
        display: inline-block;
    }

    .apigateway-icon {
        font-size: 12px;
        vertical-align: middle;
        color: #63656E;
        position: absolute;
        right: -16px;
        top: 20px;
    }

    .data-table {
        width: 100%;
        margin-top: 118px;
        color: #313238;
        font-size: 14px;
        position: static !important;

        .apigw-disabled {
            color: #979BA5;

            .apigateway-icon,
            .ag-text {
                color: #979BA5;
            }
        }

        .name {
            width: 350px;
            text-align: left;
        }

        .desc {
            width: 190px;
        }

        .creator {
            width: 135px;
        }

        .env {
            width: 175px;
        }

        .resource {
            width: 105px;
        }

        .action {
            min-width: 300px;
            flex: 1;
        }

        > thead {
            th {
                color: #979BA5;
                font-size: 14px;
                padding: 10px 0;
                font-weight: normal;
                text-align: left;
            }
        }

        .apigw-table-thead {
            position: absolute;
            width: 100%;
            top: 80px;
            left: 0;
            overflow: hidden;
            z-index: 9;
            background: #f5f7fa;
            tr {
                display: block;
                width: 1280px;
                margin: 0 auto;
            }
        }

        > tbody {
            tr {
                td {
                    padding-bottom: 10px;
                }
            }
        }

        .ag-text {
            font-size: 14px;
        }

        .data-item {
            width: 100%;
            background: #FFF;
            border-radius: 2px;
            display: flex;
            box-shadow: 0 2px 4px 0 rgba(25,25,41,0.05);

            &:hover {
                box-shadow: 0px 1px 3px 0px rgba(0 ,0 ,0 , 0.15);
            }

            > div {
                padding: 14px 14px 14px 0;
                text-align: left;
                line-height: 50px;
            }

            .logo {
                width: 50px;
                height: 50px;
                text-align: center;
                line-height: 50px;
                background: #AAC8EF;
                color: #FFF;
                font-size: 26px;
                font-weight: bold;
                border-radius: 4px;
                display: inline-block;
                margin-right: 10px;
                vertical-align: middle;
                margin-left: 14px;
            }

            .name {
                font-weight: bold;
                text-align: left;
                cursor: pointer;

                &:hover {
                    color: $primaryColor;
                }
            }
        }

        .data-item.new-created {
            background: #f1fcf5;
        }
    }

    .ag-detail-panel {
        width: 180px;
        border-radius: 2px 2px 2px 2px;
        padding: 10px 15px;

        .panel-title {
            font-size: 14px;
            color: #63656E;
            padding-bottom: 10px;
            border-bottom: 1px solid #F0F1F5;
            line-height: 1;
        }

        .panel-list {
            padding-top: 10px;
            max-height: 200px;
            overflow: auto;
            li {
                font-size: 14px;
                margin-bottom: 12px;
                line-height: 21px;
            }

            .ag-dot {
                margin-right: 8px;
            }
        }

    }
    .ap-nodata {
        background: #FFF;
        border: 1px solid #DCDEE5;
        height: 280px;
        padding: 0;
        border-radius: 2px;
        display: flex;
        justify-content: center;
        align-items: center;
    }
    .tips {
        padding: 0 3px;
        font-size: 12px;
        font-weight: 400;
        color: #3a84ff;
        background-color: #edf4ff;
        border-radius: 3px;
    }
    .official-tips {
        padding: 0 3px;
        font-size: 12px;
        font-weight: 400;
        color: #3fc06d;
        background-color: #e5f6ea;
        border-radius: 3px;
    }

    .name-wrapper{
        display: inline-block;
        max-width: 245px;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
        vertical-align: top;
    }
    .name-wrapper-one {
        max-width: 220px;
    }
    .name-wrapper-two {
        max-width: 172px;
    }
    .name-wrapper-three {
        /* max-width: 138px; */
        white-space: nowrap;
    }
    .info-wrapper {
        display: flex;
    }
    .text-wrapper {
        display: flex;
        align-items:center;
        flex-wrap: wrap;
        overflow: hidden;
        text-overflow: ellipsis;
        line-height: 24px;
        span {
            line-height: 20px;
            margin: 0 3px;
        }
    }
    .filter-selected {
        width: 120px;
        border: 1px solid #C4C6CC;
        color: #979ba5;

        /deep/ .bk-select-prefix-icon {
            top: calc(50% - 7px) !important;
        }
    }
    .en-wd {
        width: 140px;
    }
    .gateway-wrapper /deep/ .bk-loading .bk-loading-wrapper {
        top: 260px;
    }

    .container-content.content-scroll-cls {
      .header {
        width: calc(100% - 6px);
      }
      .apigw-table-thead {
        width: calc(100% - 6px);
      }
    }
</style>
