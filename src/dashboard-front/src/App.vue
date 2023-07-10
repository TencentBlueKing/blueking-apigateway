<template>
  <div id="app" :class="[systemCls, { 'apigw-doc': $route.meta.isDocRouter }]">
    <bk-navigation
      :header-title="nav.id"
      :side-title="nav.title"
      :navigation-type="curNav.nav"
      :need-menu="curNav.needMenu"
      :default-open="menuOpened"
      :hover-width="240"
      :unique-opened="false"
      @toggle="handleToggle"
      @toggle-click="handleToggleClick">
      <template slot="side-header">
        <img v-if="localLanguage === 'en'" src="@/images/APIgataway-en.png" class="ps-logo" @click="goPage('index')">
        <img v-else src="@/images/APIgataway-c.png" class="ps-logo" @click="goPage('index')">
      </template>
      <template slot="header">
        <div class="ag-navigation-header">
          <ol class="header-nav" v-if="curNav.nav === 'top-bottom'">
            <li
              v-for="(item, index) in header.list"
              :key="item.id"
              v-if="item.enabled"
              :class="{ 'item-active': index === header.active }"
              class="header-nav-item"
            >
              <span v-if="!isExternalLink(item.url)" @click="handleToPage(item.url, index, item.link)">{{item.name}}</span>
              <a :href="item.url" target="_blank" v-else>{{item.name}}</a>
            </li>
          </ol>
          <div v-else class="header-title">
            <span class="ml5">{{nav.id}}</span>
          </div>
          <bk-select
            class="header-select"
            v-model="header.bizId"
            searchable
            style="opacity: 0; cursor: default;"
            :clearable="false"
            :class="{ 'is-left': curNav.nav === 'left-right' }"
            :disabled="true">
            <bk-option v-for="option in header.selectList"
              :key="option.id"
              :id="option.id"
              :name="option.name">
            </bk-option>
          </bk-select>
          <bk-popover theme="light navigation-message" placement="bottom" :arrow="false" offset="0, 5" trigger="mouseenter" :tippy-options="{ 'hideOnClick': false }">
            <div class="header-mind header-language" :class="{ 'is-left': curNav.nav === 'left-right' }">
              <span :class="['bk-icon', localLanguage === 'en' ? 'icon-english' : 'icon-chinese', 'lang-icon']"></span>
            </div>
            <template slot="content">
              <ul class="monitor-navigation-admin">
                <li :class="['nav-item', { 'active-language-item': languageMap[langItem.id] === curLanguage }]" v-for="langItem in lang.list" :key="langItem.id" @click="changeLanguage(langItem.id)">
                  <i :class="`bk-icon icon-${langItem.id} lang-icon`"></i>{{langItem.name}}
                </li>
              </ul>
            </template>
          </bk-popover>
          <div
            class="my-monitor"
            v-bk-tooltips.top="$t('我的告警')"
            v-if="GLOBAL_CONFIG.PLATFORM_FEATURE.ENABLE_MONITOR"
            @click="$router.push({ name: 'myMonitor' })">
            <i class="apigateway-icon icon-ag-monitor-fill"></i>
          </div>
          <div class="header-help" :class="{ 'is-left': curNav.nav === 'left-right' }" v-if="GLOBAL_CONFIG.PLATFORM_FEATURE.MENU_ITEM_HELP">
            <bk-popover theme="light navigation-message" placement="bottom" :arrow="false" offset="0, 5" trigger="mouseenter" :tippy-options="{ 'hideOnClick': false }">
              <div class="header-mind feedback" :class="{ 'is-left': curNav.nav === 'left-right' }">
                <svg class="bk-icon menu-icon" style="fill: currentColor;overflow: hidden;" viewBox="0 0 64 64" version="1.1" xmlns="http://www.w3.org/2000/svg">
                  <path d="M32,4C16.5,4,4,16.5,4,32c0,3.6,0.7,7.1,2,10.4V56c0,1.1,0.9,2,2,2h13.6C36,63.7,52.3,56.8,58,42.4S56.8,11.7,42.4,6C39.1,4.7,35.6,4,32,4z M31.3,45.1c-1.7,0-3-1.3-3-3s1.3-3,3-3c1.7,0,3,1.3,3,3S33,45.1,31.3,45.1z M36.7,31.7c-2.3,1.3-3,2.2-3,3.9v0.9H29v-1c-0.2-2.8,0.7-4.4,3.2-5.8c2.3-1.4,3-2.2,3-3.8s-1.3-2.8-3.3-2.8c-1.8-0.1-3.3,1.2-3.5,3c0,0.1,0,0.1,0,0.2h-4.8c0.1-4.4,3.1-7.4,8.5-7.4c5,0,8.3,2.8,8.3,6.9C40.5,28.4,39.2,30.3,36.7,31.7z"></path>
                </svg>
              </div>
              <template slot="content">
                <ul class="monitor-navigation-admin">
                  <li class="nav-item" v-if="GLOBAL_CONFIG.HELPER.name && GLOBAL_CONFIG.HELPER.href"><a :href="GLOBAL_CONFIG.HELPER.href">{{GLOBAL_CONFIG.HELPER.name}}</a></li>
                  <li class="nav-item" v-if="GLOBAL_CONFIG.FEED_BACK_LINK"><a :href="GLOBAL_CONFIG.FEED_BACK_LINK" target="_blank"> {{ $t('问题反馈') }} </a></li>
                  <li class="nav-item" v-if="GLOBAL_CONFIG.MARKER"><a :href="GLOBAL_CONFIG.MARKER" target="_blank"> {{ $t('加入圈子') }} </a></li>
                </ul>
              </template>
            </bk-popover>
          </div>
          <!-- <div class="header-help" :class="{ 'is-left': curNav.nav === 'left-right' }" v-if="GLOBAL_CONFIG.PLATFORM_FEATURE.MENU_ITEM_HELP">
                        <bk-popover placement="bottom" theme="light" :delay="0" :distance="16" ext-cls="header-help-popover">
                            <svg class="bk-icon menu-icon" style="fill: currentColor;overflow: hidden;" viewBox="0 0 64 64" version="1.1" xmlns="http://www.w3.org/2000/svg">
                                <path d="M32,4C16.5,4,4,16.5,4,32c0,3.6,0.7,7.1,2,10.4V56c0,1.1,0.9,2,2,2h13.6C36,63.7,52.3,56.8,58,42.4S56.8,11.7,42.4,6C39.1,4.7,35.6,4,32,4z M31.3,45.1c-1.7,0-3-1.3-3-3s1.3-3,3-3c1.7,0,3,1.3,3,3S33,45.1,31.3,45.1z M36.7,31.7c-2.3,1.3-3,2.2-3,3.9v0.9H29v-1c-0.2-2.8,0.7-4.4,3.2-5.8c2.3-1.4,3-2.2,3-3.8s-1.3-2.8-3.3-2.8c-1.8-0.1-3.3,1.2-3.5,3c0,0.1,0,0.1,0,0.2h-4.8c0.1-4.4,3.1-7.4,8.5-7.4c5,0,8.3,2.8,8.3,6.9C40.5,28.4,39.2,30.3,36.7,31.7z"></path>
                            </svg>
                            <ul class="menu-list" slot="content">
                                <li v-if="GLOBAL_CONFIG.HELPER.name && GLOBAL_CONFIG.HELPER.href"><a :href="GLOBAL_CONFIG.HELPER.href">{{GLOBAL_CONFIG.HELPER.name}}</a></li>
                                <li v-if="GLOBAL_CONFIG.FEED_BACK_LINK"><a :href="GLOBAL_CONFIG.FEED_BACK_LINK" target="_blank"> {{ $t('问题反馈') }} </a></li>
                                <li v-if="GLOBAL_CONFIG.MARKER"><a :href="GLOBAL_CONFIG.MARKER" target="_blank"> {{ $t('加入圈子') }} </a></li>
                            </ul>
                        </bk-popover>
                    </div> -->
          <bk-popover theme="light navigation-message" :arrow="false" offset="-20, 10" placement="bottom-start" :tippy-options="{ 'hideOnClick': false }">
            <div class="header-user" :class="{ 'is-left': curNav.nav === 'left-right' }">
              {{user.username}}
              <i class="bk-icon icon-down-shape"></i>
            </div>
            <template slot="content">
              <ul class="monitor-navigation-admin">
                <!-- <li class="nav-item avatar">
                                    <img :src="user.avatar_url || avatarUrl" width="30px">
                                    <span class="fright">{{ user.username }}</span>
                                </li> -->
                <li class="nav-item" @click="logout">
                  {{ $t('退出登录') }}
                </li>
              </ul>
            </template>
          </bk-popover>
        </div>
      </template>
      <template slot="menu">
        <div class="ag-side-title" v-if="isShowSelect">
          <bk-popover ext-cls="side-title-popover-cls" :disabled="!tagCount">
            <div slot="content" class="side-title-popover-content">
              {{ curApigwName }}
              <div class="ml15">
                <span v-if="curApigwData.status === 0" class="option-tips terminated mr2"> {{ $t('已停用') }} </span>
                <span v-if="curApigwData.is_official" class="option-tips official mr2"> {{ $t('官方') }} </span>
                <span v-if="curApigwData.hosting_type === 1" class="option-tips" v-bk-tooltips="$t('该网关使用专享实例托管资源')"> {{ $t('专享') }} </span>
              </div>
            </div>
            <div class="tag-select-warpper">
              <bk-select
                v-model="selectApigwId"
                ext-cls="ag-select-apigw"
                :clearable="false"
                :searchable="true"
                :search-placeholder="$t('请输入关键字搜索')"
                :style="{ 'min-width': '240px', 'opacity': menuOpened ? 1 : 0 }"
                @toggle="handleApigwToggle"
                @selected="handleApigwSelect">
                <template #trigger>
                  <div class="select-apigw-wrapper">
                    <div class="apigw-name" :style="{ 'max-width': apigwTitleWidth + 'px' }">{{ curApigwName }}</div>
                    <div class="tag-tips-wrapper">
                      <span v-if="curApigwData.status === 0" class="option-tips terminated title-tips"> {{ $t('已停用') }} </span>
                      <span v-else-if="curApigwData.is_official" class="option-tips official title-tips"> {{ $t('官方') }} </span>
                      <span v-else-if="curApigwData.hosting_type === 1" class="option-tips title-tips" v-bk-tooltips="$t('该网关使用专享实例托管资源')"> {{ $t('专享') }} </span>
                      <span class="option-tips cur-quantity title-quantity" v-if="tagCount > 1">+{{tagCount - 1}}</span>
                    </div>
                  </div>
                </template>
                <bk-option v-for="(option, index) in apigwList"
                  :key="option.id"
                  :id="option.id"
                  :name="option.name"
                  class="apigw-option-cls"
                  :data-index="option.id === selectApigwId ? index : -1"
                  :data-id="option.id">
                  <div style="overflow: hidden; display: flex;">
                    <span style="flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">{{option.name}}</span>
                    <span v-if="option.status === 0" :class="['option-tips', 'terminated', { 'mr5': option.is_official || option.hosting_type === 1 }]"> {{ $t('已停用') }} </span>
                    <span v-if="option.is_official" :class="['option-tips', 'official', { 'mr5': option.hosting_type === 1 }]"> {{ $t('官方') }} </span>
                    <span v-if="option.hosting_type === 1" class="option-tips" v-bk-tooltips="$t('该网关使用专享实例托管资源')"> {{ $t('专享') }} </span>
                  </div>
                </bk-option>
              </bk-select>
              <i :class="['apigateway-icon icon-ag-down-shape', { 'up': isUp }]"></i>
            </div>
          </bk-popover>
        </div>
        <bk-navigation-menu
          ref="menu"
          :default-active="nav.id"
          :unique-opened="true"
          :toggle-active="nav.toggle"
          v-bind="themeColor">
          <template>
            <bk-navigation-menu-item
              v-for="item in nav.list"
              v-if="item.enabled"
              :key="item.url"
              :has-child="item.children && !!item.children.length"
              :group="item.group"
              :icon="item.icon"
              :disabled="item.disabled"
              :url="item.url"
              :id="item.url"
              :class="{ 'navigation-item-wrapper': isNavigation }"
              @open="handleOpen"
              @close="handleClose"
              @click="handleSelect">
              <span :id="item.url">{{item.name}}</span>
              <span v-if="getFlag(item)" class="bk-badge-wrapper" style="vertical-align: middle; margin-left: 5px; margin-top: -10px;">
                <span class="bk-badge bk-danger top-right pinned dot"></span>
              </span>
              <div slot="child">
                <bk-navigation-menu-item
                  :key="child.url"
                  v-for="child in item.children"
                  v-if="!child.hidden"
                  :id="child.url"
                  :disabled="child.disabled"
                  :icon="child.icon"
                  :url="child.url"
                  :default-active="child.active"
                  @click="handleSelect">
                  <span :id="child.url">
                    <template v-if="child.url === 'apigwPermissionApply'">
                      {{child.name}}
                      <span v-if="applyCount" class="bk-badge-wrapper" style="vertical-align: middle; margin-left: 5px; margin-top: -10px; transform: scale(0.8);">
                        <span class="bk-badge bk-danger top-right pinned">
                          {{applyCount}}
                        </span>
                      </span>
                    </template>
                    <template v-else-if="child.url === 'apigwComPermissionApply'">
                      {{child.name}}
                      <span v-if="applyEsbCount" class="bk-badge-wrapper" style="vertical-align: middle; margin-left: 5px; margin-top: -10px; transform: scale(0.8);">
                        <span class="bk-badge bk-danger top-right pinned">
                          {{applyEsbCount}}
                        </span>
                      </span>
                    </template>
                    <template v-else>
                      {{child.name}}
                    </template>
                  </span>
                </bk-navigation-menu-item>
              </div>
            </bk-navigation-menu-item>
          </template>
        </bk-navigation-menu>
      </template>
      <div :class="['ag-navigation-content', { 'is-index': isIndex || $route.meta.isDocRouter }]">
        <router-view :key="routerKey" />
      </div>
      <!-- 首页显示 -->
      <template slot="footer" v-if="$route.meta.showFooter">
        <div class="ag-navigation-footer monitor-navigation-footer" style="margin-top: 10px;flex-direction: column;">
          <div class="info">
            <a :href="GLOBAL_CONFIG.FOOT_INFO.NAMEHREF" target="_blank">{{ $t(GLOBAL_CONFIG.FOOT_INFO.NAME) }}</a>
            <span>|</span>
            <a :href="GLOBAL_CONFIG.FOOT_INFO.COMMUNITYHREF" target="_blank">{{ $t(GLOBAL_CONFIG.FOOT_INFO.COMMUNITY) }}</a>
            <span v-if="GLOBAL_CONFIG.FOOT_INFO.PRODUCT">|</span>
            <a v-if="GLOBAL_CONFIG.FOOT_INFO.PRODUCT" :href="GLOBAL_CONFIG.FOOT_INFO.PRODUCTHREF" target="_blank">{{ $t(GLOBAL_CONFIG.FOOT_INFO.PRODUCT) }}</a>
          </div>
          Copyright © 2012-{{curYear}} Tencent BlueKing. All Rights Reserved. V{{GLOBAL_CONFIG.FOOT_INFO.VERSION}}
        </div>
      </template>
    </bk-navigation>
    <app-auth ref="bkAuth"></app-auth>
    <!-- 帮助文档 -->
    <help-doc></help-doc>
  </div>
</template>
<script>
  import { mapGetters } from 'vuex'
  import { sortByKey, jsonpRequest } from '@/common/util'
  import { bus } from '@/common/bus'
  import { bk_logout as bkLogout } from '../static/js/bklogout'
  import i18n from '@/language/i18n.js'
  import defaultAvatarUrl from '@/images/default-user.png'
  import jsCookie from 'js-cookie'
  import cookie from 'cookie'
  import axios from 'axios'
  import help from '@/views/component-doc/help'

  const COMPONENT_API_ROUTER = [
    {
      name: i18n.t('简介'),
      enabled: true,
      icon: 'apigateway-icon icon-ag-component-intro',
      url: 'apigwApi'
    },
    {
      name: i18n.t('系统管理'),
      enabled: true,
      icon: 'apigateway-icon icon-ag-system-mgr',
      url: 'apigwSystem'
    },
    {
      name: i18n.t('组件管理'),
      enabled: true,
      icon: 'apigateway-icon icon-ag-components',
      url: 'apigwAccess'
    },
    {
      name: i18n.t('同步组件配置到 API 网关'),
      enabled: false,
      url: 'syncApigwAccess'
    },
    {
      name: i18n.t('组件同步历史'),
      enabled: false,
      url: 'syncHistory'
    },
    {
      name: i18n.t('同步组件版本'),
      enabled: false,
      url: 'syncVersion'
    },
    {
      name: i18n.t('文档分类'),
      enabled: true,
      icon: 'apigateway-icon icon-ag-doc-mgr',
      url: 'apigwDocCategory'
    },
    {
      name: i18n.t('权限管理'),
      enabled: true,
      icon: 'apigateway-icon icon-ag-my-perm',
      indexUrl: 'apigwSystem',
      url: 'esbPermManager',
      children: [
        {
          name: i18n.t('权限审批'),
          url: 'apigwComPermissionApply'
        },
        {
          name: i18n.t('应用权限'),
          url: 'apigwComPermission'
        },
        {
          name: i18n.t('审批历史'),
          url: 'apigwComPermissionRecord'
        }
      ]
    },
    {
      name: i18n.t('实时运行数据'),
      enabled: true,
      icon: 'apigateway-icon icon-ag-runtime',
      url: 'runtimeData'
    }
  ]
    
  const LANGUAGE_MAP = {
    'chinese': 'zh-hans',
    'english': 'en'
  }

  export default {
    name: 'app',
    components: {
      helpDoc: help
    },
    data () {
      return {
        routerKey: +new Date(),
        systemCls: 'mac',
        curYear: '2019',
        isDropdownShow: false,
        menuOpened: true,
        nav: {
          list: [
            {
              name: i18n.t('基本设置'),
              enabled: true,
              icon: 'apigateway-icon icon-ag-cog',
              open: true,
              url: 'basicConfig',
              children: []
            },
            {
              name: i18n.t('微网关实例'),
              enabled: true,
              icon: 'apigateway-icon icon-ag-clipboard',
              url: 'microGateway'
            },
            {
              name: i18n.t('发布变更'),
              enabled: true,
              icon: 'apigateway-icon icon-ag-order',
              url: 'pulishChange',
              children: [
                {
                  name: i18n.t('版本发布'),
                  url: 'apigwVersionCreate'
                },
                {
                  name: i18n.t('版本管理'),
                  url: 'apigwVersion'
                },
                {
                  name: i18n.t('发布历史'),
                  url: 'apigwReleaseHistory'
                }
              ]
            },
            {
              name: i18n.t('权限管理'),
              enabled: true,
              icon: 'apigateway-icon icon-ag-apply',
              url: 'permManager',
              children: [
                {
                  name: i18n.t('权限审批'),
                  url: 'apigwPermissionApply'
                },
                {
                  name: i18n.t('应用权限'),
                  url: 'apigwPermission'
                },
                {
                  name: i18n.t('审批历史'),
                  url: 'apigwPermissionRecord'
                }
              ]
            },
            {
              name: i18n.t('运行数据'),
              enabled: this.GLOBAL_CONFIG.PLATFORM_FEATURE.ENABLE_RUN_DATA,
              icon: 'apigateway-icon icon-ag-bar-chart',
              url: 'runData',
              children: [
                {
                  name: i18n.t('流水日志'),
                  url: 'apigwAccessLog'
                },
                {
                  name: i18n.t('统计报表'),
                  hidden: !this.GLOBAL_CONFIG.PLATFORM_FEATURE.ENABLE_RUN_DATA_METRICS,
                  url: 'apigwReport'
                }
              ]
            },
            {
              name: i18n.t('监控告警'),
              enabled: this.GLOBAL_CONFIG.PLATFORM_FEATURE.ENABLE_MONITOR,
              icon: 'apigateway-icon icon-ag-monitor',
              url: 'monitorAlarm',
              children: [
                {
                  name: i18n.t('告警策略'),
                  url: 'apigwMonitorAlarmStrategy'
                },
                {
                  name: i18n.t('告警历史'),
                  url: 'apigwMonitorAlarmHistory'
                }
              ]
            },
            {
              name: i18n.t('在线调试'),
              enabled: true,
              icon: 'apigateway-icon icon-ag-debug',
              url: 'apigwTest'
            },
            {
              name: i18n.t('资源SDK'),
              enabled: true,
              icon: 'apigateway-icon icon-ag-log-collection',
              url: 'apigwSdk'
            },
            {
              name: i18n.t('操作审计'),
              enabled: true,
              icon: 'apigateway-icon icon-ag-audit',
              url: 'apigwAudit'
            }
          ],
          id: 'apigwInfo',
          toggle: true,
          submenuActive: false,
          title: 'APIGateway'
        },
        header: {
          list: [
            {
              name: i18n.t('我的网关'),
              id: 1,
              url: 'index',
              enabled: true
            },
            {
              name: i18n.t('组件管理'),
              id: 4,
              url: BK_PAAS2_ESB_URL || 'apigwAccess',
              enabled: true
            },
            {
              name: i18n.t('网关API文档'),
              id: 2,
              url: 'apigwDoc',
              enabled: true
            },
            {
              name: i18n.t('组件API文档'),
              id: 5,
              url: 'componentAPI',
              enabled: this.GLOBAL_CONFIG.PLATFORM_FEATURE.MENU_ITEM_ESB_API_DOC
            },
            {
              name: this.$t('网关API SDK'),
              id: 6,
              params: {
                type: 'apigateway'
              },
              url: 'apigwSDK',
              enabled: this.GLOBAL_CONFIG.PLATFORM_FEATURE.ENABLE_SDK
            },
            {
              name: this.$t('组件API SDK'),
              id: 7,
              params: {
                type: 'esb'
              },
              url: 'esbSDK',
              enabled: this.GLOBAL_CONFIG.PLATFORM_FEATURE.ENABLE_SDK
            },
            {
              name: this.$t('常用工具'),
              id: 8,
              url: this.GLOBAL_CONFIG.TOOLS,
              link: this.GLOBAL_CONFIG.TOOLS || '',
              enabled: this.GLOBAL_CONFIG.PLATFORM_FEATURE.MENU_ITEM_TOOLS
            },
            {
              name: i18n.t('使用指南'),
              id: 3,
              url: this.GLOBAL_CONFIG.DOC.GUIDE,
              enabled: true
            }
          ],
          selectList: [
          ],
          active: 0,
          bizId: 1
        },
        message: {
          list: []
        },
        lang: {
          list: [
            {
              name: '中文',
              id: 'chinese'
            },
            {
              name: 'English',
              id: 'english'
            }
          ]
        },
        avatarUrl: defaultAvatarUrl,
        isNavigation: true,
        languageMap: LANGUAGE_MAP,
        isUp: false,
        selectIndex: -1,
        options: [],
        activeApigwId: '',
        selectApigwId: '',
        activeRouterData: {
          0: ['index'],
          2: ['apigwDoc', 'apigwAPIDetailIntro', 'apigwAPIDetailDoc'],
          3: ['componentAPI', 'ComponentAPIDetailIntro', 'ComponentAPIDetailDoc'],
          4: ['apigwSDK'],
          5: ['esbSDK']
        },
        isSwitch: false
      }
    },
    computed: {
      ...mapGetters(['mainContentLoading', 'user']),
      permissionApplyList () {
        return this.$store.state.permission.permissionApplyList
      },
      applyCount () {
        return this.$store.state.permission.permissionApplyCount
      },
      applyEsbCount () {
        return this.$store.state.componentPermission.permissionApplyCount
      },
      curNav () {
        if (this.$route.name === 'index' || this.$route.meta.hasMenu === false) {
          return {
            nav: 'top-bottom',
            needMenu: false,
            name: this.$t('上下结构导航')
          }
        } else {
          return {
            nav: 'top-bottom',
            needMenu: true,
            name: this.$t('上下结构导航')
          }
        }
      },
      curApigwFeature () {
        return this.$store.state.curApigw
      },
      microFlagState () {
        if (!this.curApigwFeature.feature_flags) return false
        return this.curApigwFeature.feature_flags.MICRO_GATEWAY_ENABLED
      },
      pluginFlagState () {
        if (!this.curApigwFeature.feature_flags) return false
        return this.curApigwFeature.feature_flags.PLUGIN_ENABLED
      },
      accessStrategyState () {
        if (!this.curApigwFeature.feature_flags) return false
        return this.curApigwFeature.feature_flags.ACCESS_STRATEGY_ENABLED
      },
      isIndex () {
        return this.$route.name === 'index'
      },
      isAgigwDoc () {
        const routerNameData = Object.values(this.activeRouterData).reduce((p, v) => {
          return [...p, ...v]
        }, [])
        return routerNameData.includes(this.$route.name)
      },
      apigwId () {
        if (this.$route.params.id !== undefined) {
          return this.$route.params.id
        }
        return undefined
      },
      apigwList () {
        return sortByKey(this.$store.state.apis.apigwList, 'name')
      },
      curApigwId: {
        get () {
          const apigwList = this.$store.state.apis.apigwList
          const result = apigwList.find(apigw => {
            return String(apigw.id) === String(this.apigwId)
          })
          return result ? result.id : ''
        },
        set () {}
      },
      curApigwName: {
        get () {
          const apigwList = this.$store.state.apis.apigwList
          const result = apigwList.find(apigw => {
            return String(apigw.id) === String(this.apigwId)
          })
          return result ? result.name : ''
        }
      },
      curApigwData () {
        return this.apigwList.find(apigw => String(apigw.id) === String(this.selectApigwId)) || {}
      },
      isShowSelect () {
        return this.header.active === 0
      },
      localLanguage () {
        return this.$store.state.localLanguage
      },
      curLanguage () {
        return jsCookie.get('blueking_language') || 'zh-hans'
      },
      themeColor () {
        return {
          'item-default-color': '#63656E',
          'item-active-bg-color': '#E1ECFF',
          'item-active-color': '#3A84FF',
          'item-active-icon-color': '#3A84FF',
          'sub-menu-open-bg-color': '#F5F7FA',
          'item-child-icon-default-color': '#C4C6CC',
          'item-child-icon-hover-color': '#C4C6CC',
          'item-child-icon-active-color': '#3A84FF'
        }
      },
      tagCount () {
        let count = 0
        if (this.curApigwData.status === 0) {
          count++
        }
        if (this.curApigwData.is_official) {
          count++
        }
        if (this.curApigwData.hosting_type === 1) {
          count++
        }
        return count
      },
      apigwTitleWidth () {
        if (this.tagCount === 0) {
          return 180
        } else if (this.tagCount === 1) {
          return 150
        } else {
          return 114
        }
      }
    },
    watch: {
      async '$route' (to, from) {
        if (COMPONENT_API_ROUTER.map(item => item.url).includes(to.meta.matchRoute)
          || COMPONENT_API_ROUTER.some(item => (item.children && item.children.length > 0) && item.indexUrl === to.meta.matchIndexRouter)) {
          this.getEsbApigwPermissionApplyList()
          this.nav.list = COMPONENT_API_ROUTER
          this.header.active = 1
        } else {
          // 切换文档路由不请求
          if (!to.meta.isDocRouter) {
            await this.getApisDetail()
          }
          this.getCurNav(to.name)
          Object.keys(this.activeRouterData).forEach(index => {
            if (this.activeRouterData[index].includes(to.name)) {
              const isEsbApi = !this.GLOBAL_CONFIG.PLATFORM_FEATURE.MENU_ITEM_ESB_API
              // 根据nav过滤项对应key高亮调整
              this.header.active = (isEsbApi && Number(index) > 0) ? Number(index - 1) : Number(index)
            }
          })
        }

        this.nav.id = this.$route.meta ? this.$route.meta.matchRoute : this.$route.name

        // 创建网关页面，隐藏侧边栏
        if (to.name === 'createApigw') {
          this.systemCls += ' create'
        } else {
          this.systemCls = this.systemCls.replace('create', '')
        }

        // 404，隐藏侧边栏
        if (to.name === 'none') {
          this.systemCls += ' none-page'
        } else {
          this.systemCls = this.systemCls.replace('none-page', '')
        }
                
        // doc路由需要更新
        if (to.meta.isDocRouter) {
          if (to.name !== from.name) {
            this.routerKey = +new Date()
          } else if (to.params.id !== from.params.id) {
            this.routerKey = +new Date()
          } else if (to.params.hasOwnProperty('version')) {
            if (to.params['version'] !== from.params['version']) {
              this.routerKey = +new Date()
            }
          }
        }
      },
      apigwId () {
        if (this.apigwId && !this.$route.meta.isDocRouter) {
          this.getApigwPermissionApplyList()
          this.systemCls = this.systemCls.replace('create', '')
          this.getApisDetail()
        }
      },
      pluginFlagState (val) {
        // const plginData = {
        //     name: this.$t('插件管理') ,
        //     url: 'apigwGatewayPlugin'
        // }
        if (!val && this.$route.name === 'apigwGatewayPlugin') {
          this.$router.push({
            name: 'apigwLabel'
          })
          // this.nav.list[0].children.splice(3, 1)
        }
        // } else {
        //     this.nav.list[0].children.splice(3, 0, plginData)
        // }
      },
      curApigwId: {
        handler (id) {
          this.selectApigwId = id
        },
        immediate: true
      },
      selectIndex (newIndex) {
        if (newIndex > -1) {
          this.setOptionActive()
        }
      }
    },
    created () {
      const platform = window.navigator.platform.toLowerCase()
      if (platform.indexOf('win') === 0) {
        this.systemCls = 'win'
      }
      if (!this.$route.meta.isDocRouter) {
        this.getApisDetail()
      }
      this.curYear = (new Date()).getFullYear()
      const ESB_API_NAV_ID = 4
      if (!this.GLOBAL_CONFIG.PLATFORM_FEATURE.MENU_ITEM_ESB_API) {
        this.header.list = this.header.list.filter(item => item.id !== ESB_API_NAV_ID)
      }
    },
    mounted () {
      const self = this
      bus.$on('show-login-modal', data => {
        self.$refs.bkAuth.showLoginModal(data)
      })
      bus.$on('show-404-page', data => {
        this.$router.push({
          name: 'none'
        })
      })
      bus.$on('close-login-modal', () => {
        self.$refs.bkAuth.hideLoginModal()
        setTimeout(() => {
          window.location.reload()
        }, 0)
      })
      this.axiosInstance = axios.create({
        withCredentials: true,
        headers: { 'X-REQUESTED-WITH': 'XMLHttpRequest' }
      })

      // 菜单栏收起/展开完成派发事件，由于组件中的toggle事件触发的是动画的开始，对于需要计算宽度的场景无效，所以使用此方法
      this.$refs.menu.$el.closest('.navigation-nav').addEventListener('transitionend', this.emitSideToggleEnd, false)
    },
    beforeDestroy () {
      this.$refs.menu.$el.closest('.navigation-nav').removeEventListener('transitionend', this.emitSideToggleEnd, false)
    },
    methods: {
      async getApisDetail () {
        if (this.apigwId) {
          const res = await this.$store.dispatch('apis/getApisDetail', this.apigwId)
          this.$store.commit('updateCurApigw', res.data)
        }
      },
      handleToPage (routeName, index, link) {
        this.header.active = index
        // 文档组件API
        if (routeName === 'componentAPI') {
          if (BK_PAAS2_ESB_DOC_URL) {
            window.open(BK_PAAS2_ESB_DOC_URL)
            return
          }
        }
        // 常用工具
        if (link !== undefined) {
          window.open(routeName)
          return
        }
        if (routeName === 'apigwSystem') {
          this.$router.push({
            name: 'apigwSystem'
          })
          return
        }
        this.goPage(routeName)
      },
      getFlag (paylaod) {
        if (paylaod.url === 'permManager') {
          return !!this.applyCount
        }
        if (paylaod.url === 'esbPermManager') {
          return !!this.applyEsbCount
        }
        return false
      },
      getCurNav (routerName) {
        const matchRouters = ['apigwSystem', 'apigwApi', 'apigwAccess', 'apigwComPermissionRecord', 'apigwComPermissionApply', 'apigwComPermission']
        if (!matchRouters.includes(routerName)) {
          this.nav.list = [
            {
              name: this.$t('基本设置'),
              enabled: true,
              icon: 'apigateway-icon icon-ag-cog',
              open: true,
              url: 'basicConfig',
              children: [
                {
                  name: this.$t('资源管理'),
                  url: 'apigwResource'
                },
                {
                  name: this.$t('环境管理'),
                  url: 'apigwStage'
                },
                {
                  name: this.$t('访问策略'),
                  hidden: !this.accessStrategyState,
                  url: 'apigwStrategy'
                },
                {
                  name: this.$t('插件配置'),
                  hidden: !this.pluginFlagState,
                  url: 'apigwGatewayPlugin'
                },
                {
                  name: this.$t('标签管理'),
                  url: 'apigwLabel'
                },
                {
                  name: this.$t('基本信息'),
                  url: 'apigwInfo'
                }
              ]
            },
            {
              name: this.$t('微网关实例'),
              enabled: this.microFlagState,
              icon: 'apigateway-icon icon-ag-miniapi',
              url: 'microGateway'
            },
            {
              name: this.$t('发布变更'),
              enabled: true,
              icon: 'apigateway-icon icon-ag-order',
              url: 'pulishChange',
              children: [
                {
                  name: this.$t('版本发布'),
                  url: 'apigwVersionCreate'
                },
                {
                  name: this.$t('版本管理'),
                  url: 'apigwVersion'
                },
                {
                  name: this.$t('发布历史'),
                  url: 'apigwReleaseHistory'
                }
              ]
            },
            {
              name: this.$t('权限管理'),
              enabled: true,
              icon: 'apigateway-icon icon-ag-permission',
              url: 'permManager',
              children: [
                {
                  name: this.$t('权限审批'),
                  url: 'apigwPermissionApply'
                },
                {
                  name: this.$t('应用权限'),
                  url: 'apigwPermission'
                },
                {
                  name: this.$t('审批历史'),
                  url: 'apigwPermissionRecord'
                }
              ]
            },
            {
              name: this.$t('运行数据'),
              enabled: this.GLOBAL_CONFIG.PLATFORM_FEATURE.ENABLE_RUN_DATA,
              icon: 'apigateway-icon icon-ag-bar-chart',
              url: 'runData',
              children: [
                {
                  name: this.$t('流水日志'),
                  url: 'apigwAccessLog'
                },
                {
                  name: this.$t('统计报表'),
                  hidden: !this.GLOBAL_CONFIG.PLATFORM_FEATURE.ENABLE_RUN_DATA_METRICS,
                  url: 'apigwReport'
                }
              ]
            },
            {
              name: this.$t('监控告警'),
              enabled: this.GLOBAL_CONFIG.PLATFORM_FEATURE.ENABLE_MONITOR,
              icon: 'apigateway-icon icon-ag-monitor',
              url: 'monitorAlarm',
              children: [
                {
                  name: this.$t('告警策略'),
                  url: 'apigwMonitorAlarmStrategy'
                },
                {
                  name: this.$t('告警历史'),
                  url: 'apigwMonitorAlarmHistory'
                }
              ]
            },
            {
              name: this.$t('在线调试'),
              enabled: true,
              icon: 'apigateway-icon icon-ag-debug',
              url: 'apigwTest'
            },
            {
              name: this.$t('资源SDK'),
              enabled: true,
              icon: 'apigateway-icon icon-ag-log-collection',
              url: 'apigwSdk'
            },
            {
              name: this.$t('操作审计'),
              enabled: true,
              icon: 'apigateway-icon icon-ag-audit',
              url: 'apigwAudit'
            }
          ]
        }
      },
      goPage (routeName) {
        if (routeName) {
          this.$router.push({
            name: routeName,
            params: {
              id: routeName === 'index' ? '' : this.apigwId
            }
          })
        }
      },
      dropdownShow () {
        this.isDropdownShow = true
      },
      dropdownHide () {
        this.isDropdownShow = false
      },
      isExternalLink (url) {
        return /^https?:\/\//.test(url)
      },
      async getApisList () {
        try {
          await this.$store.dispatch('apis/getApisList')
        } catch (e) {
          console.error(e)
        }
      },
      handleSelect (id, item) {
        this.nav.url = id
        this.nav.id = id
        this.goPage(id)
      },
      logout () {
        bkLogout.logout()
        window.location = this.GLOBAL_CONFIG.LOGIN_URL + '/?c_url=' + window.location.href
      },
      handleToggle (opened) {
        this.nav.toggle = opened
        this.menuOpened = opened
      },
      handleToggleClick (opened) {
        this.menuOpened = opened
        this.$store.commit('setMenuOpened', opened)
        bus.$emit('nav-toggle', opened)
      },
      getApigwPermissionApplyList (page) {
        const apigwId = this.apigwId
        const pageParams = {
          limit: 10,
          offset: 0,
          bk_app_code: '',
          applied_by: ''
        }

        this.$store.dispatch('permission/getApigwPermissionApplyList', { apigwId, pageParams })
      },
      async getEsbApigwPermissionApplyList () {
        const pageParams = {
          limit: 10,
          offset: 0,
          bk_app_code: '',
          applied_by: ''
        }
        this.$store.dispatch('componentPermission/getPermissionByPending', pageParams)
      },
      emitSideToggleEnd () {
        bus.$emit('side-toggle-end')
      },
      handleApigwSelect (id) {
        if (!id) {
          return
        }
        const routeParams = {
          name: this.$route.meta.matchRoute || this.$route.name,
          params: this.$route.params,
          meta: this.$route.meta
        }
        if (routeParams.name !== 'apigwVersionCreate') {
          routeParams.query = this.$route.query
        }
        routeParams.params.id = this.isSwitch ? this.activeApigwId : id
        this.$router.push(routeParams)
      },
      async changeLanguage (languageType) {
        const language = this.languageMap[languageType]
        if (this.curLanguage === language) {
          return false
        }
        try {
          const CSRFToken = cookie.parse(document.cookie)[DASHBOARD_CSRF_COOKIE_NAME || `${window.PROJECT_CONFIG.BKPAAS_APP_ID}_csrftoken`]
          const data = new URLSearchParams()
          data.append('language', language)
          await this.axiosInstance.post(`${DASHBOARD_URL}/i18n/setlang/`, data, {
            headers: {
              'Accept': 'application/json, text/plain',
              'Content-Type': 'application/x-www-form-urlencoded',
              'X-CSRFToken': CSRFToken
            }
          })
          if (window.BK_COMPONENT_API_URL) {
            jsonpRequest(
              `${window.BK_COMPONENT_API_URL}/api/c/compapi/v2/usermanage/fe_update_user_language/`,
              {
                language
              }
            )
          }
          this.$router.go(0)
        } catch (e) {
          console.error(e)
        }
      },
      handleClose (id) {
        if (id === 'basicConfig') {
          this.isNavigation = false
        }
      },
      handleOpen (id) {
        if (id === 'basicConfig') {
          setTimeout(() => {
            this.isNavigation = true
          }, 300)
        }
      },
      // select 支持键盘操作选择
      handleApigwToggle (status) {
        this.isUp = !this.isUp
        const optionInput = document.querySelector('.bk-select-search-input')
        if (status) {
          this.$nextTick(() => {
            this.options = Array.from(document.querySelectorAll('.apigw-option-cls'))
            this.selectIndex = this.options.findIndex(el => (Number(el.dataset.index)) !== -1)
            optionInput.addEventListener('keydown', this.handleNavigate)
          })
        } else {
          optionInput.removeEventListener('keydown', this.handleNavigate)
          this.isSwitch = false
        }
      },
      // 键盘上下键回车处理
      handleNavigate (e) {
        const length = this.apigwList.length
        switch (e.keyCode) {
          case 38:
            if (this.selectIndex === -1 || this.selectIndex === 0) {
              this.selectIndex = length - 1
            } else {
              this.selectIndex--
            }
            this.isSwitch = true
            break
          case 40:
            this.selectIndex < length - 1 ? this.selectIndex++ : this.selectIndex = 0
            this.isSwitch = true
            break
          case 13:
            e.preventDefault()
            this.selectApigwId = this.activeApigwId
            break
          default:
            this.isSwitch = false
            break
        }
      },
      // 设置高亮
      setOptionActive () {
        this.options.forEach(el => {
          el.classList.remove('is-selected')
        })
        this.options.find((el, index) => {
          if (this.selectIndex === index) {
            el.classList.add('is-selected')
            this.activeApigwId = el.dataset.id
            return true
          }
        })
      }
    }
  }
</script>

<style lang="postcss">
    @import './css/reset-doc.css';
    @import './css/app-doc.css';
    @import './css/reset.css';
    @import './css/app.css';

    .ag-project-logo {
        width: 34px;
        height: 34px;
        line-height: 34px;
        border-radius: 10px;
        object-fit: cover;
        text-align: center;
        background: #F0F1F5;
        font-size: 18px;
        font-weight: bold;
        position: absolute;
        left: 12px;
        top: 8px;
    }

    .main-content {
        min-height: 300px;
    }
    .split {
        margin-bottom: 15px;
    }
    .header-bussiness {
        margin-right: 50px;
    }
    .header-icon {
        margin-right: 8px;
        display: inline-block;
        color: #63656e;
        font-size: 16px;
        width: 32px;
        height: 32px;
        border-radius: 50%;
        text-align: center;
        line-height: 32px;
    }
    .header-icon:hover {
        background: #f0f1f5;
        cursor: pointer;
    }
    .header-avatar {
        display: inline-block;
        width: 30px;
        height: 30px;
        border-radius: 50%;
        font-size: 16px;
        color: #979ba5;
        line-height: 28px;
        text-align: center;
        margin-left: 8px;
        margin-right: 25px;
        background: #f0f1f5;
        border: 1px solid #eee;
        box-shadow: 0px 3px 6px 0px rgba(99, 101, 110, 0.06);
        cursor: pointer;
    }
    .ag-navigation-header {
        .bk-icon {
            vertical-align: middle;
        }
    }
    /* 以下样式是为了适应例子父级的宽高而设置 */
    .bk-navigation {
        outline: 1px solid #ebebeb;
        .bk-navigation-wrapper {
            height: calc(100vh - 252px)!important;
        }
    }
    /* 以上样式是为了适应例子父级的宽高而设置 */

    @define-mixin defualt-icon-mixin $color: #768197 {
        color: $color;
        font-size: 16px;
        position: relative;
        height: 32px;
        width: 32px;
        display: flex;
        align-items: center;
        justify-content: center;
        margin-right: 8px;
    }
    @define-mixin is-left-mixin $needBgColor: true {
        color: #63656E;
        &:hover {
            color: #3A84FF;
            @if $needBgColor {
                background: #F0F1F5;
            }
        }
    };
    @define-mixin icon-hover-mixin {
        background: linear-gradient(270deg,rgba(37,48,71,1) 0%,rgba(38,50,71,1) 100%);
        border-radius: 100%;
        cursor: pointer;
        color: #D3D9E4;
    }
    @define-mixin popover-panel-mxin $width: 150px, $itemHoverColor: #3A84FF {
        width: $width;
        display: flex;
        flex-direction: column;
        background: #FFFFFF;
        border: 1px solid #E2E2E2;
        box-shadow: 0px 3px 4px 0px rgba(64,112,203,0.06);
        padding: 6px 0;
        margin: 0;
        color: #63656E;
        .nav-item {
            flex: 0 0 32px;
            display: flex;
            align-items: center;
            padding: 0 20px;
            list-style: none;
            &:hover {
                color: $itemHoverColor;
                cursor: pointer;
                background-color: #F0F1F5;
            }
        }
    }
    .ag-navigation {
        &-header {
            flex: 1;
            /* padding-left: 12px; */
            height: 100%;
            display: flex;
            align-items: center;
            font-size: 14px;
            .header-nav {
                display: flex;
                padding: 0;
                margin: 0;
                &-item {
                    list-style: none;
                    margin-right: 40px;
                    color: #96A2B9;
                    &.item-active {
                        color: #FFFFFF !important;
                    }
                    &:hover {
                        cursor: pointer;
                        color: #D3D9E4;
                    }
                    a {
                        color: #96A2B9;
                        &:hover {
                            color: #D3D9E4;
                        }
                    }
                }
            }
            .header-title {
                color: #63656E;
                font-size: 16px;
                display: flex;
                align-items: center;
                margin-left: -6px;
                &-icon {
                    display: flex;
                    align-items: center;
                    width: 28px;
                    height: 28px;
                    font-size: 28px;
                    color: #3A84FF;
                    cursor: pointer;
                }
            }
            .header-select {
                width: 240px;
                margin-left: auto;
                margin-right: 34px;
                border: none;
                background: #252F43;
                color: #D3D9E4;
                box-shadow: none;
                &.is-left {
                    background: #F0F1F5;
                    color: #63656E;
                }
            }
            .header-mind {
               @mixin defualt-icon-mixin;
               &.is-left {
                   @mixin is-left-mixin;
               }
               &-mark {
                   position: absolute;
                   right: 8px;
                   top: 8px;
                   height: 7px;
                   width: 7px;
                   border: 1px solid #27334C;
                   background-color: #EA3636;
                   border-radius: 100%;
                   &.is-left {
                       border-color: #F0F1F5;
                   }
               }
               &:hover {
                   @mixin icon-hover-mixin;
                }
            }
            .header-help {
                @mixin defualt-icon-mixin;
                font-size: 0;
                &.is-left {
                   @mixin is-left-mixin;
                }
                &:hover {
                    background: -webkit-gradient(linear,right top, left top,from(rgba(37,48,71,1)),to(rgba(38,50,71,1)));
                    background: linear-gradient(270deg,rgba(37,48,71,1) 0%,rgba(38,50,71,1) 100%);
                    border-radius: 100%;
                    cursor: pointer;
                    color: #D3D9E4;
                }

                .menu-icon {
                    width: 16px;
                    height: 16px;
                }
                .bk-tooltip-ref {
                    padding: 8px;
                    &:hover {
                        .feedback {
                            color: #D3D9E4;
                        }
                    }
                }
            }
            .header-user {
                height: 100%;
                line-height: 32px;
                display: flex;
                align-items: center;
                justify-content: center;
                color: #96A2B9;
                margin-left: 8px;
                .bk-icon {
                    margin-left: 5px;
                    font-size: 12px;
                }
                &.is-left {
                   @mixin is-left-mixin false;
                }
                &:hover {
                    cursor: pointer;
                    color: #D3D9E4;
                }
            }
        }
        &-content {
            min-height: calc(100% - 185px);
            border-radius: 2px;
            margin-top: 52px;
        }
        &-footer {
            height: 52px;
            width: 100%;
            margin: 32px 0 0 ;
            display: flex;
            align-items: center;
            justify-content: center;
            color: #63656E;
            font-size: 12px;
        }
        &-message {
            display: flex;
            flex-direction: column;
            width: 360px;
            background-color: #FFFFFF;
            border: 1px solid #E2E2E2;
            border-radius: 2px;
            box-shadow: 0px 3px 4px 0px rgba(64,112,203,0.06);
            color: #979BA5;
            font-size: 12px;
            .message-title {
                flex: 0 0 48px;
                display: flex;
                align-items: center;
                color: #313238;
                font-size: 14px;
                padding: 0 20px;
                margin: 0;
                border-bottom: 1px solid #F0F1F5;
            }
            .message-list {
                flex: 1;
                max-height: 450px;
                overflow: auto;
                margin: 0;
                display: flex;
                flex-direction: column;
                padding: 0;
                &-item {
                    display: flex;
                    width: 100%;
                    padding: 0 20px;
                    .item-message {
                        padding: 13px 0;
                        line-height: 16px;
                        min-height: 42px;
                        flex: 1;
                        flex-wrap: wrap;
                        color: #63656E;
                    }
                    .item-date {
                        padding: 13px 0;
                        margin-left: 16px;
                        color: #979BA5;
                    }
                    &:hover {
                        cursor: pointer;
                        background: #F0F1F5;
                    }
                }
            }
            .message-footer {
                flex: 0 0 42px;
                border-top: 1px solid #F0F1F5;
                display: flex;
                align-items: center;
                justify-content: center;
                color: #3A84FF;
            }
        }
        &-nav {
            @mixin popover-panel-mxin;
        }
        &-admin {
            @mixin popover-panel-mxin 170px #63656E;
        }
    }
    .tippy-popper {
        .tippy-tooltip.navigation-message-theme {
            padding: 0;
            border-radius: 0;
            box-shadow: none;
        }
    }
    .ag-side-title {
        height: 52px;
        line-height: 50px;
        font-size: 18px;
        color: #63656E;
        border-bottom: 1px solid #DCDEE5;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        .bk-tooltip-ref {
            vertical-align: top;
        }
    }
    .ag-select-apigw {
        &.bk-select {
            border: none;
            line-height: 52px;

            .icon-angle-down {
                display: none;
            }

            &.is-focus {
                border: none;
                box-shadow: none;
            }

            .bk-select-name {
                height: 52px;
            }

            .bk-select-angle {
                top: 14px;
                right: 12px;
                font-size: 27px;
                font-weight: normal;
            }

            .bk-select-name {
                font-weight: normal;
                font-size: 14px;
                padding-left: 16px;
                color: #63656E;
                padding-right: 100px;
                position: relative;
                z-index: 9;
            }
        }
    }
    .tag-select-warpper {
        position: relative;
        i.apigateway-icon {
            position: absolute;
            top: 20px;
            right: 18px;
            z-index: 99;
            font-size: 14px;
            color: #979BA5;
            transition: .3s;
            pointer-events: none;
            &.up {
                transform: rotate(-180deg);
            }
        }
    }
    .apigw-option-cls {
        .bk-option-content {
            padding-right: 5px;
        }
        .option-tips {
            margin-top: 8px;
        }
    }
    .ag-tag-apigw {
        .select-apigw-wrapper .apigw-name {
            max-width: 150px;
        }
    }
    .ag-tag-apigw-zero {
        .select-apigw-wrapper .apigw-name {
            max-width: 180px;
        }
    }
    .ag-select-popover {
        /*width: 243px !important;*/
        position: relative;
        left: 4px;
        .bk-select-search-input {
            width: 216px;
            border: 1px solid #dcdee5;
            border-radius: 2px;
            margin: 10px 10px 0 10px;
        }
        .bk-options .bk-option-content {
            padding-left: 11px;
        }
        .bk-select-search-wrapper {
            padding: 0;

            .left-icon {
                left: 23px;
                margin-top: 5px;
            }
        }
    }

    .header-help-popover {
        .tippy-tooltip {
            background: #fff;
            border: 1px solid #eee;
            padding: 0;
            border-radius: 2px;
            box-shadow: 0 2px 5px #e5e5e5;
        }
        .menu-list {
            width: 108px;
            padding: 10px 15px;
            li {
                line-height: 30px;
                text-align: center;

                a {
                    font-size: 14px;
                    color: #666;
                    &:hover {
                        color: #3a84ff;
                    }
                }
            }
        }
    }

    .user {
        max-width: 200px;
        opacity: 0;
        visibility: hidden;
        background: #fff;
        border: solid 1px #eeeeee;
        border-radius: 2px;
        position: absolute;
        right: 0;
        top: 55px;
        transition: all .3s;
        box-shadow: 0 2px 5px #e5e5e5;
        cursor: default;

        &:after {
            content: "";
            position: absolute;
            top: -10px;
            right: 36px;
            width: 16px;
            height: 10px;
        }
    }
    .user-yourname {
        padding: 20px 24px 15px 24px;
        border-bottom: solid 1px #eeeeee;
        display: flex;
    }

    .user-yourname img {
        width: 36px;
        border-radius: 2px;
    }

    .user-yourname span.fright {
        min-width: 80px;
        max-width: 115px;
        overflow: hidden;
        white-space: nowrap;
        text-overflow: ellipsis;
        color: #666666;
        padding-left: 15px;
        line-height: 36px;
    }

    .my-monitor {
        width: 32px;
        height: 32px;
        display: flex;
        align-items: center;
        justify-content: center;
        margin-right: 8px;
        cursor: pointer;
        color: #768197;
        .icon-ag-monitor-fill {
            font-size: 16px;
        }
        &:hover {
            background: linear-gradient(270deg,rgba(37,48,71,1) 0%,rgba(38,50,71,1) 100%);
            border-radius: 100%;
            cursor: pointer;
            color: #D3D9E4;
        }
    }

    .user-opation {
        padding: 10px 24px;
    }

    .user-opation a {
        line-height: 36px;
        color: #666666;
    }

    .user-opation a:hover {
        color: #3A84FF;
    }

    .header-user {
        z-index: 1000;
        position: relative;
    }
    .header-user:hover .user {
        opacity: 1;
        visibility: visible;

    }
    .info {
        margin-bottom: 5px;
    }
    .info span {
        position: relative;
        top: -1px;
    }
    .info a {
        color: #3a84ff;
    }
    .option-tips {
        display: inline-block;
        height: 16px;
        line-height: 16px;
        padding: 0px 3px;
        color: #3a84ff;
        background-color: #edf4ff;
        border-radius: 2px;
    }
    .official {
        color: #3fc06d;
        background-color: #e5f6ea;
    }
    .terminated {
        color: #63656E;
        background: #F0F1F5;
    }
    .ps-logo {
        height: 22px;
        cursor: pointer;
    }
    .cur-quantity {
        color: #63656E;
        background: #F0F1F5;
    }

    .icon-style {
        font-size: 22px;
        color: #96A2B9;
    }
    .icon-style:hover {
        color: #3A84FF;
    }
    .monitor-navigation-admin {
        width: 136px;
        display: -webkit-box;
        display: -ms-flexbox;
        display: flex;
        -webkit-box-orient: vertical;
        -webkit-box-direction: normal;
        -ms-flex-direction: column;
        flex-direction: column;
        background: #FFFFFF;
        border: 1px solid #E2E2E2;
        -webkit-box-shadow: 0px 3px 4px 0px rgba(64,112,203,0.06);
        box-shadow: 0px 3px 4px 0px rgba(64,112,203,0.06);
        padding: 6px 0;
        margin: 0;
        color: #63656E;
    }
    .monitor-navigation-admin .nav-item {
        -webkit-box-flex: 0;
        -ms-flex: 0 0 32px;
        flex: 0 0 32px;
        display: -webkit-box;
        display: -ms-flexbox;
        display: flex;
        -webkit-box-align: center;
        -ms-flex-align: center;
        align-items: center;
        padding: 0 16px;
        list-style: none;
    }
    .monitor-navigation-admin .nav-item .lang-icon {
        font-size: 20px;
        margin-right: 6px;
    }
    .ag-navigation-header .header-mind.feedback {
        width: 14px;
        height: 14px;
        margin: 0;
    }
    .monitor-navigation-admin .nav-item:hover,
    .monitor-navigation-admin .nav-item a:hover {
        cursor: pointer;
        background-color: #F5F7FA;
    }
    .monitor-navigation-admin .nav-item.avatar {
        flex: 0 0 52px;
        .fright {
            margin-left: 8px;
            overflow: hidden;
            white-space: nowrap;
            text-overflow: ellipsis;
        }
    }
    .monitor-navigation-admin .nav-item a {
        color: #63656E;
    }
    .navigation-item-wrapper:first-child .navigation-sbmenu-content.collapse-transition {
        height: auto !important;
    }
    .header-language {
        transform: translateY(1px);
    }
    .active-language-item {
        cursor: pointer;
        background-color: #F5F7FA;
    }
    .monitor-navigation-footer{
        height:52px;
        width:100%;
        margin:32px 0 0;
        display:-webkit-box;
        display:-ms-flexbox;
        display:flex;
        -webkit-box-align:center;
        -ms-flex-align:center;
        align-items:center;
        -webkit-box-pack:center;
        -ms-flex-pack:center;
        justify-content:center;
        border-top:1px solid #DCDEE5;
        color:#63656E;
        font-size:12px;
    }
    /* 二级 */
    .navigation-menu .navigation-sbmenu-content .navigation-menu-item.group-theme:hover {
        background: #EAEBF0;
    }
    .navigation-menu {
        margin-top: 8px;
    }
    .select-apigw-wrapper {
        display: flex;
        align-items: center;
        padding-left: 16px;

        .apigw-name {
            max-width: 114px;
            font-weight: normal;
            font-size: 14px;
            color: #63656E;
            margin-right: 8px;
            overflow: hidden;
            white-space: nowrap;
            text-overflow: ellipsis;
        }
        .tag-tips-wrapper {
            display: flex;
            font-size: 12px;
            .title-tips,
            .title-quantity {
                margin-top: 0 !important;
                margin-right: 2px;
                padding: 0 2px !important;
            }
        }
    }
    .ag-side-title .bk-tooltip {
        width: 100%;
        height: 100%;
        .bk-tooltip-ref {
            width: 100%;
        }
    }
    .side-title-popover-cls {
        .tippy-tooltip {
            background: #fff;
            color:#63656E;
            .tippy-arrow {
                border-top: 8px solid #fff;
            }
        }
        .side-title-popover-content {
            display: flex;
            align-items: center;
            .option-tips {
                margin-top: 0 !important;
            }
            .m2 {
                margin-right: 2px;
            }
        }
        .tippy-content {
            max-width: 400px;
        }
    }
    .table-header-tips-cls {
        white-space: nowrap;
        text-overflow: ellipsis;
        overflow: hidden;
    }
</style>

<style>
    .tips-disabled-btn {
        position: relative;
        display: inline-block;
        height: 32px;
        line-height: 30px;
        min-width: 64px;
        white-space: nowrap;
        padding: 0 15px;
        font-size: 14px;
        border-radius: 2px;
        text-align: center;
        vertical-align: middle;
        background-color: #dcdee5;
        border-color: #dcdee5;
        color: #fff;
        cursor: not-allowed;
        transition: background-color .3s ease;
        user-select: none
    }
    .bk-transfer .source-list ul.content {
        padding-bottom: 40px;
    }
    /* 穿梭框样式设置 */
    .resource-transfer-wrapper .transfer-source-item {
        white-space: nowrap;
        text-overflow: ellipsis;
        overflow: hidden;
    }
    /* 侧栏离开info全局样式 */
    .sideslider-close-cls.bk-dialog-wrapper .bk-dialog-sub-header .bk-dialog-header-inner {
        text-align: center;
    }
</style>
