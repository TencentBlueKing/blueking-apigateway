/*
 * TencentBlueKing is pleased to support the open source community by making
 * 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
 * Copyright (C) 2017 THL A29 Limited, a Tencent company. All rights reserved.
 * Licensed under the MIT License (the "License"); you may not use this file except
 * in compliance with the License. You may obtain a copy of the License at
 *
 *     http://opensource.org/licenses/MIT
 *
 * Unless required by applicable law or agreed to in writing, software distributed under
 * the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND,
 * either express or implied. See the License for the specific language governing permissions and
 * limitations under the License.
 *
 * We undertake not to change the open source license (MIT license) applicable
 * to the current version of the project delivered to anyone in the future.
 */
/**
 * @file router 配置
 * @author
 */

import Vue from 'vue'
import VueRouter from 'vue-router'

import globalConfig from '../../static/json/config.js'
import store from '@/store'
import http from '@/api'
import NotFound from '@/views/404'
import Building from '@/views/building'

import Index from '@/views/index'
// const Index = () => import(/* webpackChunkName: 'inddex'*/'@/views/index')
import ApigwMain from '@/views/main'
// const ApigwMain = () => import(/* webpackChunkName: 'inddex'*/'@/views/main')
import i18n from '@/language/i18n.js'
import preloadDoc from '@/common/preload-doc'

// import ApigwEdit from '@/views/base/create-apigw'
const ApigwEdit = () => import(/* webpackChunkName: 'apigw-info'*/'@/views/base/create-apigw')
// import ApigwInfo from '@/views/base/info'
const ApigwInfo = () => import(/* webpackChunkName: 'apigw-info'*/'@/views/base/info')

// import ApigwLabel from '@/views/label/index'
const ApigwLabel = () => import(/* webpackChunkName: 'label'*/'@/views/label/index')

// import ApigwResource from '@/views/resource/index'
const ApigwResource = () => import(/* webpackChunkName: 'resource'*/'@/views/resource/index')

// import ApigwResourceEdit from '@/views/resource/edit'
const ApigwResourceEdit = () => import(/* webpackChunkName: 'resource'*/'@/views/resource/edit')

// import ApigwResourceImport from '@/views/resource/import'
const ApigwResourceImport = () => import(/* webpackChunkName: 'resource'*/'@/views/resource/import')

const apigwResourceImportDoc = () => import(/* webpackChunkName: 'resource'*/'@/views/resource/import-doc')

// import ApigwReleaseHistory from '@/views/release-history/index'
const ApigwReleaseHistory = () => import(/* webpackChunkName: 'release-history'*/'@/views/release-history/index')

// import ApigwPermission from '@/views/permission/index'
const ApigwPermission = () => import(/* webpackChunkName: 'permission'*/'@/views/permission/index')

// import ApigwPermissionApply from '@/views/permission/permission-apply'
const ApigwPermissionApply = () => import(/* webpackChunkName: 'permission'*/'@/views/permission/permission-apply')

// import ApigwPermissionRecord from '@/views/permission/permission-record'
const ApigwPermissionRecord = () => import(/* webpackChunkName: 'permission'*/'@/views/permission/permission-record')

// import ApigwStrategy from '@/views/strategy/index'
const ApigwStrategy = () => import(/* webpackChunkName: 'strategy'*/'@/views/strategy/index')

// import ApigwGatewayPlugin from '@/views/gateway-plugin/index'
const ApigwGatewayPlugin = () => import(/* webpackChunkName: 'gateway-plugin'*/'@/views/gateway-plugin/index')

// import ApigwStrategyEdit from '@/views/strategy/edit'
const ApigwStrategyEdit = () => import(/* webpackChunkName: 'strategy'*/'@/views/strategy/edit')

// 运行数据
// import ApigwAccessLog from '@/views/access-log/index'
const ApigwAccessLog = () => import(/* webpackChunkName: 'access-log'*/'@/views/access-log/index')

// import ApigwMonitorAlarmStrategy from '@/views/monitor/alarm-strategy'
const ApigwMonitorAlarmStrategy = () => import(/* webpackChunkName: 'monitor'*/'@/views/monitor/alarm-strategy')

// import ApigwMonitorAlarmHistory from '@/views/monitor/alarm-history'
const ApigwMonitorAlarmHistory = () => import(/* webpackChunkName: 'monitor'*/'@/views/monitor/alarm-history')

// import ApigwReport from '@/views/report/index'
const ApigwReport = () => import(/* webpackChunkName: 'report'*/'@/views/report/index')

// import ApigwTest from '@/views/online-test/index'
const ApigwTest = () => import(/* webpackChunkName: 'online-test'*/'@/views/online-test/index')

// 资源sdk
// import ApigwSdk from '@/views/sdk'
const ApigwSdk = () => import(/* webpackChunkName: 'sdk'*/'@/views/sdk')

// 我的告警
// import MyMonitor from '@/views/my-monitor'
const MyMonitor = () => import(/* webpackChunkName: 'my-monitor'*/'@/views/my-monitor')

// const NotFound = () => import(/* webpackChunkName: 'none' */'@/views/404')

// 日志详情
const ApigwAccessLogDetail = () => import(/* webpackChunkName: 'access-log-detail' */'@/views/access-log/detail')

// import ApigwStage from '@/views/stage/index'
const ApigwStage = () => import(/* webpackChunkName: 'stage'*/'@/views/stage/index')
// import ApigwStageEdit from '@/views/stage/edit'
const ApigwStageEdit = () => import(/* webpackChunkName: 'stage'*/'@/views/stage/edit')

// import ApigwVersion from '@/views/version/index'
const ApigwVersion = () => import(/* webpackChunkName: 'version'*/'@/views/version/index')
// import ApigwVersionCreate from '@/views/version/create-version'
const ApigwVersionCreate = () => import(/* webpackChunkName: 'version'*/'@/views/version/create-version')
const ApigwVersionDetail = () => import(/* webpackChunkName: 'version'*/'@/views/version/detail')

const ApigwAudit = () => import(/* webpackChunkName: 'audit'*/'@/views/audit')

const ApigwSystemManager = () => import(/* webpackChunkName: 'system'*/'@/views/system')

const ApigwDocCategoryManager = () => import(/* webpackChunkName: 'category'*/'@/views/doc-category')

const ApigwRuntimeIndex = () => import(/* webpackChunkName: 'runtime-data'*/'@/views/runtime-data/index')

const ApigwRuntimeData = () => import(/* webpackChunkName: 'runtime-data'*/'@/views/runtime-data/list')

const ApigwRuntimeDetail = () => import(/* webpackChunkName: 'runtime-data'*/'@/views/runtime-data/detail')

const ApigwComponentApi = () => import(/* webpackChunkName: 'api'*/'@/views/api')

const ApigwAccessManager = () => import(/* webpackChunkName: 'access'*/'@/views/component-manager')

const SyncApigwAccess = () => import(/* webpackChunkName: 'sync-access'*/'@/views/component-manager/sync-access/index')

const SyncHistory = () => import(/* webpackChunkName: 'sync-history'*/'@/views/component-manager/sync-access/history')

const SyncVersion = () => import(/* webpackChunkName: 'sync-version'*/'@/views/component-manager/sync-access/version')

// import ApigwComPermission from '@/views/component-permission/index'
const ApigwComPermission = () => import(/* webpackChunkName: 'component-permission'*/'@/views/component-permission/index')

// import ApigwComPermissionApply from '@/views/component-permission/permission-apply'
const ApigwComPermissionApply = () => import(/* webpackChunkName: 'component-permission'*/'@/views/component-permission/permission-apply')

// import ApigwComPermissionRecord from '@/views/component-permission/permission-record'
const ApigwComPermissionRecord = () => import(/* webpackChunkName: 'component-permission'*/'@/views/component-permission/permission-record')

const MicroGateway = () => import(/* webpackChunkName: 'micro-gateway'*/'@/views/micro-gateway/index')
 
const createMicroGateway = () => import(/* webpackChunkName: 'createMicroGateway'*/'@/views/micro-gateway/components/create')
const ApigwGatewayPluginEdit = () => import(/* webpackChunkName: 'apigwGatewayPluginEdit'*/'@/views/gateway-plugin/edit')

const ApigwDoc = () => import(/* webpackChunkName: 'apigw-doc'*/'@/views/component-doc/doc/index')
const ComponentAPI = () => import(/* webpackChunkName: 'component-api'*/'@/views/component-doc/api/index')
const ComponentAPIDetail = () => import(/* webpackChunkName: 'component-api' */'@/views/component-doc/api/detail')
const ComponentAPIDetailDoc = () => import(/* webpackChunkName: 'component-api' */'@/views/component-doc/api/doc')
const ComponentAPIDetailIntro = () => import(/* webpackChunkName: 'component-api' */'@/views/component-doc/api/intro')

const ApigwAPIDetail = () => import(/* webpackChunkName: 'apigw-doc'*/'@/views/component-doc/doc/detail')
const ApigwAPIDetailDoc = () => import(/* webpackChunkName: 'apigw-doc'*/'@/views/component-doc/doc/doc')
const ApigwAPIDetailIntro = () => import(/* webpackChunkName: 'apigw-doc'*/'@/views/component-doc/doc/intro')
const ApigwSDK = () => import(/* webpackChunkName: 'sdk' */'@/views/component-doc/sdk/index')
Vue.use(VueRouter)

// 文档一级路由出口
const docsComponent = {
  name: 'DocMain',
  template: '<router-view></router-view>'
}

const routes = [
  {
    path: '/',
    name: 'index',
    component: Index,
    meta: {
      matchRoute: 'index',
      showFooter: true
    }
  },
  {
    path: '/my-monitor',
    name: 'myMonitor',
    component: MyMonitor,
    meta: {
      matchRoute: 'MyMonitor'
    }
  },

  // 文档路由映射
  {
    path: `/${globalConfig.PREV_URL}`,
    redirect: `/${globalConfig.PREV_URL}/apigw-api/`,
    name: 'docsMain',
    component: docsComponent,
    alias: '',
    children: [
      {
        path: 'apigw-api',
        name: 'apigwDoc',
        component: ApigwDoc,
        meta: {
          matchRoute: 'apigwDoc',
          notAppHeader: true,
          isDocRouter: true
        }
      },

      {
        path: 'component-api',
        alias: '',
        name: 'componentAPI',
        component: ComponentAPI,
        meta: {
          matchRoute: 'componentAPI',
          notAppHeader: true,
          isDocRouter: true
        }
      },
      {
        path: 'sdk/apigw',
        alias: '',
        name: 'apigwSDK',
        component: ApigwSDK,
        meta: {
          matchRoute: 'apigwSDK',
          type: 'apigateway',
          isDocRouter: true
        }
      },
        
      {
        path: 'sdk/esb',
        alias: '',
        name: 'esbSDK',
        component: ApigwSDK,
        meta: {
          matchRoute: 'esbSDK',
          type: 'esb',
          isDocRouter: true
        }
      },

      {
        path: 'component-api/:version/:id',
        alias: '',
        name: 'componentAPIDetail',
        component: ComponentAPIDetail,
        meta: {
          matchRoute: 'componentAPI',
          isDocRouter: true
        },
        children: [
          {
            path: 'intro',
            alias: '',
            name: 'ComponentAPIDetailIntro',
            component: ComponentAPIDetailIntro,
            meta: {
              matchRoute: 'componentAPI',
              isDocRouter: true
            }
          },
          {
            path: ':componentId/doc',
            alias: '',
            name: 'ComponentAPIDetailDoc',
            component: ComponentAPIDetailDoc,
            meta: {
              matchRoute: 'componentAPI',
              isDocRouter: true
            }
          }
        ]
      },
        
      {
        path: 'apigw-api/:apigwId/',
        alias: '',
        name: 'apigwAPIDetail',
        component: ApigwAPIDetail,
        meta: {
          matchRoute: 'apigwAPIDetail',
          isDocRouter: true
        },
        children: [
          {
            path: 'apigw-api/:apigwId/intro',
            alias: '',
            name: 'apigwAPIDetailIntro',
            component: ApigwAPIDetailIntro,
            meta: {
              matchRoute: 'apigwDoc',
              isDocRouter: true
            }
          },
          {
            path: 'apigw-api/:apigwId/:resourceId/doc',
            alias: '',
            name: 'apigwAPIDetailDoc',
            component: ApigwAPIDetailDoc,
            meta: {
              matchRoute: 'apigwDoc',
              isDocRouter: true
            }
          }
        ]
      }
    ]
  },

  {
    path: 'apigw',
    name: 'apigw',
    component: ApigwMain,
    children: [
      {
        path: '/create',
        name: 'createApigw',
        component: ApigwEdit,
        meta: {
          title: i18n.t('创建网关'),
          loader: 'apigw-create-loader',
          matchRoute: 'createApigw',
          notAppHeader: true
        }
      },
      {
        path: '/:id/info',
        name: 'apigwInfo',
        component: ApigwInfo,
        meta: {
          title: i18n.t('基本信息'),
          loader: 'info-loader',
          matchRoute: 'apigwInfo'
        }
      },
      {
        path: '/:id/edit',
        name: 'apigwEdit',
        component: ApigwEdit,
        meta: {
          title: i18n.t('编辑网关'),
          loader: 'info-edit-loader',
          parentRoute: 'apigwInfo',
          matchRoute: 'apigwInfo'
        }
      },

      {
        path: '/:id/label',
        name: 'apigwLabel',
        component: ApigwLabel,
        meta: {
          title: i18n.t('标签管理'),
          loader: 'table-loader',
          matchRoute: 'apigwLabel'
        }
      },

      {
        path: '/:id/stage',
        name: 'apigwStage',
        component: ApigwStage,
        meta: {
          title: i18n.t('环境管理'),
          loader: 'stage-loader',
          matchRoute: 'apigwStage'
        }
      },

      {
        path: '/:id/stage/create',
        name: 'apigwStageCreate',
        component: ApigwStageEdit,
        meta: {
          title: i18n.t('新建环境'),
          loader: 'stage-detail-loader',
          parentRoute: 'apigwStage',
          matchRoute: 'apigwStage'
        }
      },

      {
        path: '/:id/stage/:stageId/edit',
        name: 'apigwStageEdit',
        component: ApigwStageEdit,
        meta: {
          title: i18n.t('编辑环境'),
          loader: 'stage-detail-loader',
          parentRoute: 'apigwStage',
          matchRoute: 'apigwStage'
        }
      },

      {
        path: '/:id/resource',
        name: 'apigwResource',
        component: ApigwResource,
        meta: {
          title: i18n.t('资源管理'),
          loader: 'resource-loader',
          matchRoute: 'apigwResource'
        }
      },

      {
        path: '/:id/resource/create',
        name: 'apigwResourceCreate',
        component: ApigwResourceEdit,
        meta: {
          title: i18n.t('新建资源'),
          loader: 'resource-detail-loader',
          parentRoute: 'apigwResource',
          matchRoute: 'apigwResource'
        }
      },

      {
        path: '/:id/resource/import',
        name: 'apigwResourceImport',
        component: ApigwResourceImport,
        meta: {
          title: i18n.t('导入资源配置'),
          loader: 'resource-import-loader',
          parentRoute: 'apigwResource',
          matchRoute: 'apigwResource'
        }
      },

      {
        path: '/:id/resource/import-doc',
        name: 'apigwResourceImportDoc',
        component: apigwResourceImportDoc,
        meta: {
          title: i18n.t('导入资源文档'),
          loader: 'resource-import-doc-loader',
          parentRoute: 'apigwResource',
          matchRoute: 'apigwResource'
        }
      },

      {
        path: '/:id/resource/:resourceId/edit',
        name: 'apigwResourceEdit',
        component: ApigwResourceEdit,
        meta: {
          title: i18n.t('编辑资源'),
          loader: 'resource-detail-loader',
          parentRoute: 'apigwResource',
          matchRoute: 'apigwResource'
        }
      },

      {
        path: '/:id/resource/:resourceId/clone',
        name: 'apigwResourceClone',
        component: ApigwResourceEdit,
        meta: {
          title: i18n.t('克隆资源'),
          loader: 'resource-detail-loader',
          parentRoute: 'apigwResource',
          matchRoute: 'apigwResource'
        }
      },

      {
        path: '/:id/version',
        name: 'apigwVersion',
        component: ApigwVersion,
        meta: {
          title: i18n.t('版本管理'),
          loader: 'version-loader',
          matchRoute: 'apigwVersion'
        }
      },

      {
        path: '/:id/version/create',
        name: 'apigwVersionCreate',
        component: ApigwVersionCreate,
        meta: {
          title: i18n.t('版本发布'),
          loader: 'version-create-loader',
          matchRoute: 'apigwVersionCreate'
        }
      },

      {
        path: '/:id/version/:versionId/detail',
        name: 'apigwVersionDetail',
        component: ApigwVersionDetail,
        meta: {
          title: i18n.t('版本'),
          loader: 'version-detail-loader',
          parentRoute: 'apigwVersion',
          matchRoute: 'apigwVersion'
        }
      },

      {
        path: '/:id/release-history',
        name: 'apigwReleaseHistory',
        component: ApigwReleaseHistory,
        meta: {
          title: i18n.t('发布历史'),
          loader: 'history-loader',
          matchRoute: 'apigwReleaseHistory'
        }
      },

      {
        path: '/:id/permission/indexs',
        name: 'apigwPermission',
        component: ApigwPermission,
        meta: {
          title: i18n.t('应用权限'),
          loader: 'permission-loader',
          matchRoute: 'apigwPermission'
        }
      },

      {
        path: '/:id/permission/applys',
        name: 'apigwPermissionApply',
        component: ApigwPermissionApply,
        meta: {
          title: i18n.t('权限审批'),
          loader: 'apply-loader',
          matchRoute: 'apigwPermissionApply'
        }
      },

      {
        path: '/:id/permission/records',
        name: 'apigwPermissionRecord',
        component: ApigwPermissionRecord,
        meta: {
          title: i18n.t('审批历史'),
          loader: 'permission-history-loader',
          matchRoute: 'apigwPermissionRecord'
        }
      },

      {
        path: '/:id/strategy',
        name: 'apigwStrategy',
        component: ApigwStrategy,
        meta: {
          title: i18n.t('访问策略'),
          loader: 'strategy-loader',
          matchRoute: 'apigwStrategy'
        }
      },

      {
        path: '/:id/strategy/create',
        name: 'apigwStrategyCreate',
        component: ApigwStrategyEdit,
        meta: {
          title: i18n.t('新建策略'),
          loader: 'strategy-detail-loader',
          parentRoute: 'apigwStrategy',
          matchRoute: 'apigwStrategy'
        }
      },

      {
        path: '/:id/strategy/:strategyId/edit',
        name: 'apigwStrategyEdit',
        component: ApigwStrategyEdit,
        meta: {
          title: i18n.t('编辑策略'),
          loader: 'strategy-detail-loader',
          parentRoute: 'apigwStrategy',
          matchRoute: 'apigwStrategy'
        }
      },

      {
        path: '/:id/gateway-plugin',
        name: 'apigwGatewayPlugin',
        component: ApigwGatewayPlugin,
        meta: {
          title: i18n.t('网关插件'),
          loader: 'version-loader',
          matchRoute: 'apigwGatewayPlugin'
        }
      },

      {
        path: '/:id/gateway-plugin/create',
        name: 'apigwGatewayPluginCreate',
        component: ApigwGatewayPluginEdit,
        meta: {
          title: i18n.t('启用插件'),
          loader: 'version-loader',
          matchRoute: 'apigwGatewayPlugin',
          parentRoute: 'apigwGatewayPlugin'
        }
      },

      {
        path: '/:id/gateway-plugin/edit',
        name: 'apigwGatewayPluginEdit',
        component: ApigwGatewayPluginEdit,
        meta: {
          title: i18n.t('编辑插件'),
          loader: 'version-loader',
          matchRoute: 'apigwGatewayPlugin',
          parentRoute: 'apigwGatewayPlugin'
        }
      },

      {
        path: '/:id/access-log',
        name: 'apigwAccessLog',
        component: ApigwAccessLog,
        meta: {
          title: i18n.t('流水日志'),
          loader: 'access-log-loader',
          matchRoute: 'apigwAccessLog'
        }
      },

      {
        path: '/:id/access-log/:requestId',
        name: 'apigwAccessLogDetail',
        component: ApigwAccessLogDetail,
        meta: {
          title: i18n.t('流水日志'),
          hasMenu: false
        }
      },

      {
        path: '/:id/monitor',
        name: 'apigwMonitor',
        redirect: {
          title: i18n.t('告警策略'),
          loader: 'table-loader',
          name: 'apigwMonitorAlarmStrategy'
        }
      },

      {
        path: '/:id/monitor/alarm-strategy',
        name: 'apigwMonitorAlarmStrategy',
        component: ApigwMonitorAlarmStrategy,
        meta: {
          title: i18n.t('告警策略'),
          loader: 'table-loader',
          matchRoute: 'apigwMonitorAlarmStrategy'
        }
      },

      {
        path: '/:id/monitor/alarm-history',
        name: 'apigwMonitorAlarmHistory',
        component: ApigwMonitorAlarmHistory,
        meta: {
          title: i18n.t('告警历史'),
          loader: 'alarm-history-loader',
          matchRoute: 'apigwMonitorAlarmHistory'
        }
      },

      {
        path: '/:id/report',
        name: 'apigwReport',
        component: ApigwReport,
        meta: {
          title: i18n.t('统计报表'),
          loader: 'report-loader',
          matchRoute: 'apigwReport'
        }
      },

      {
        path: '/:id/test',
        name: 'apigwTest',
        component: ApigwTest,
        meta: {
          title: i18n.t('在线调试'),
          loader: 'test-loader',
          matchRoute: 'apigwTest'
        }
      },

      {
        path: '/:id/sdk',
        name: 'apigwSdk',
        component: ApigwSdk,
        meta: {
          title: i18n.t('资源SDK'),
          loader: 'SDK-loader',
          matchRoute: 'apigwSdk'
        }
      },

      {
        path: '/:id/audit',
        name: 'apigwAudit',
        component: ApigwAudit,
        meta: {
          title: i18n.t('操作审计'),
          loader: 'audit-loader',
          matchRoute: 'apigwAudit'
        }
      },

      {
        path: '/components/system',
        name: 'apigwSystem',
        component: ApigwSystemManager,
        meta: {
          title: i18n.t('系统管理'),
          loader: 'stage-loader',
          matchRoute: 'apigwSystem'
        }
      },

      {
        path: '/components/doc-category',
        name: 'apigwDocCategory',
        component: ApigwDocCategoryManager,
        meta: {
          title: i18n.t('文档分类'),
          loader: 'stage-loader',
          matchRoute: 'apigwDocCategory'
        }
      },

      {
        path: '/components/runtime-data',
        name: 'runtimeIndex',
        component: ApigwRuntimeIndex,
        meta: {
          title: i18n.t('实时运行数据'),
          loader: 'stage-loader',
          matchRoute: 'runtimeData'
        },
        children: [
          {
            path: '/components/runtime-data',
            name: 'runtimeData',
            component: ApigwRuntimeData,
            meta: {
              title: i18n.t('实时运行数据'),
              loader: 'runtime-list-loader',
              matchRoute: 'runtimeData'
            }
          },
          {
            path: '/components/system/:system/detail',
            name: 'runtimeDetail',
            component: ApigwRuntimeDetail,
            meta: {
              title: i18n.t('系统实时概况'),
              loader: 'runtime-chart-loader',
              parentRoute: 'runtimeData',
              matchRoute: 'runtimeData'
            }
          }
        ]
      },

      {
        path: '/components/intro',
        name: 'apigwApi',
        component: ApigwComponentApi,
        meta: {
          title: i18n.t('简介'),
          loader: 'introduce-loader',
          matchRoute: 'apigwApi'
        }
      },

      {
        path: '/components/access',
        name: 'apigwAccess',
        component: ApigwAccessManager,
        meta: {
          title: i18n.t('组件管理'),
          loader: 'component-manager-loader',
          matchRoute: 'apigwAccess',
          helpLinkList: (() => {
            if (globalConfig.DOC.COMPONENT_CREATE_API) {
              return [
                { text: i18n.t('如何开发和发布组件'), url: globalConfig.DOC.COMPONENT_CREATE_API }
              ]
            }
            return []
          })()
        }
      },

      {
        path: '/components/sync-access',
        name: 'syncApigwAccess',
        component: SyncApigwAccess,
        meta: {
          title: i18n.t('同步组件配置到 API 网关'),
          loader: 'table-loader',
          parentRoute: 'apigwAccess',
          matchRoute: 'apigwAccess'
        }
      },

      {
        path: '/components/sync-history',
        name: 'syncHistory',
        component: SyncHistory,
        meta: {
          title: i18n.t('组件同步历史'),
          loader: 'table-loader',
          parentRoute: 'apigwAccess',
          matchRoute: 'apigwAccess'
        }
      },

      {
        path: '/components/sync-version',
        name: 'syncVersion',
        component: SyncVersion,
        meta: {
          title: i18n.t('组件同步版本'),
          loader: 'table-loader',
          parentRoute: 'syncHistory',
          matchRoute: 'syncVersion'
        }
      },

      {
        path: '/components/permission/index',
        name: 'apigwComPermission',
        component: ApigwComPermission,
        meta: {
          title: i18n.t('应用权限'),
          loader: 'permission-loader',
          matchRoute: 'apigwComPermission',
          matchIndexRouter: 'apigwSystem'
        }
      },

      {
        path: '/components/permission/apply',
        name: 'apigwComPermissionApply',
        component: ApigwComPermissionApply,
        meta: {
          title: i18n.t('权限审批'),
          loader: 'apply-loader',
          matchRoute: 'apigwComPermissionApply',
          matchIndexRouter: 'apigwSystem'
        }
      },

      {
        path: '/components/permission/record',
        name: 'apigwComPermissionRecord',
        component: ApigwComPermissionRecord,
        meta: {
          title: i18n.t('审批历史'),
          loader: 'permission-history-loader',
          matchRoute: 'apigwComPermissionRecord',
          matchIndexRouter: 'apigwSystem'
        }
      },

      {
        path: '/:id/microgateway/index',
        name: 'microGateway',
        component: MicroGateway,
        meta: {
          title: i18n.t('微网关实例'),
          loader: 'version-loader',
          matchRoute: 'microGateway'
        }
      },

      {
        path: '/:id/microgateway/create',
        name: 'createMicroGateway',
        component: createMicroGateway,
        meta: {
          title: i18n.t('新建微网关实例'),
          loader: 'version-loader',
          parentRoute: 'microGateway',
          matchRoute: 'microGateway',
          isCreate: 'create'
        }
      }
    ]
  },
  // 404
  {
    path: '*',
    name: '404',
    component: NotFound
  },
  {
    path: '/404',
    name: 'none',
    component: NotFound
  },
  {
    path: 'apigow/:id/building',
    name: 'building',
    component: Building
  }
]

const router = new VueRouter({
  mode: 'history',
  routes: routes
})

const cancelRequest = async () => {
  const allRequest = http.queue.get()
  const requestQueue = allRequest.filter(request => request.cancelWhenRouteChange)
  await http.cancel(requestQueue.map(request => request.requestId))
}

let canceling = true
let pageMethodExecuting = true
let preloading = true

router.beforeEach(async (to, from, next) => {
  canceling = true
  await cancelRequest()
  // 主站
  if (to.meta.isDocRouter) {
    canceling = false

    preloading = true
    await preloadDoc(Vue)
    preloading = false
    next()
  } else {
    canceling = false
    
    const apigwList = store.state.apis.apigwList
    const toApigwId = to.params.id
    const apigwAuthWhitelist = ['apigwAccessLogDetail']
    if (apigwList.length && toApigwId) {
      const result = apigwList.find(item => {
        return String(item.id) === String(toApigwId)
      })
      if (!result && !apigwAuthWhitelist.includes(to.name)) {
        next({ path: '404' })
      } else {
        next()
      }
    } else {
      next()
    }
  }
})

router.afterEach(async (to, from) => {
  store.commit('setMainContentLoading', true)

  const pageDataMethods = []
  const routerList = to.matched
  routerList.forEach(r => {
    Object.values(r.instances).forEach(vm => {
      if (vm && (typeof vm.fetchPageData === 'function')) {
        pageDataMethods.push(vm.fetchPageData())
      }
      if (vm && (vm.$options.preload === 'function')) {
        pageDataMethods.push(vm.$options.preload.call(vm))
      }
    })
  })
  pageMethodExecuting = true
  await Promise.all(pageDataMethods)
  pageMethodExecuting = false
  if (to.meta.isDocRouter) {
    if (!preloading && !canceling && !pageMethodExecuting) {
      store.commit('setMainContentLoading', false)
    }
  }
})

export default router
