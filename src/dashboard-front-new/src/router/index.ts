import {
  createRouter,
  createWebHistory,
  RouteRecordRaw,
} from 'vue-router';

import globalConfig from '@/constant/config';

const Home = () => import(/* webpackChunkName: "Home" */ '@/views/home.vue');
const ApigwDocs = () => import(/* webpackChunkName: "ApigwDocs" */ '@/views/apigwDocs/index.vue');
const ApigwAPIDetail = () => import(/* webpackChunkName: "apigw-doc" */ '@/views/apigwDocs/components/detail.vue');
const ApigwAPIDetailIntro = () => import(/* webpackChunkName: "apigw-doc" */ '@/views/apigwDocs/components/intro.vue');
const ApigwAPIDetailDoc = () => import(/* webpackChunkName: "apigw-doc" */ '@/views/apigwDocs/components/doc.vue');
const ApigwMain = () => import(/* webpackChunkName: 'apigw-main'*/'@/views/main.vue');
const ApigwResource = () => import(/* webpackChunkName: 'apigw-main'*/'@/views/resource/setting/index.vue');
const ApigwResourceEdit = () => import(/* webpackChunkName: 'apigw-doc'*/'@/views/resource/setting/edit.vue');
const apigwResourceVersion = () => import(/* webpackChunkName: 'apigw-main'*/'@/views/resource/version/index.vue');
const ApigwResourceImport = () => import(/* webpackChunkName: 'apigw-doc'*/'@/views/resource/setting/import.vue');
const ApigwResourceImportDoc = () => import(/* webpackChunkName: 'apigw-doc'*/'@/views/resource/setting/import-doc.vue');
const apigwStageOverview = () => import(/* webpackChunkName: 'apigw-env'*/'@/views/stage/overview/index.vue');
const apigwStageDetail = () => import(/* webpackChunkName: 'apigw-env'*/'@/views/stage/overview/detail-mode/index.vue');
const apigwReleaseHistory = () => import(/* webpackChunkName: 'apigw-env'*/'@/views/stage/published/index.vue');
const apigwStageResourceInfo = () => import(/* webpackChunkName: 'apigw-env'*/'@/views/stage/overview/detail-mode/resource-info.vue');
const apigwStagePluginManage = () => import(/* webpackChunkName: 'apigw-env'*/'@/views/stage/overview/detail-mode/plugin-manage.vue');
const apigwOnlineTest = () => import(/* webpackChunkName: 'apigw-env'*/'@/views/online-test/index.vue');
const apigwStageVariableManage = () => import(/* webpackChunkName: 'apigw-env'*/'@/views/stage/overview/detail-mode/variable-manage.vue');
const apigwPermissionApplys = () => import(/* webpackChunkName: 'apigw-env'*/'@/views/permission/apply/index.vue');
const apigwPermissionApps = () => import(/* webpackChunkName: 'apigw-env'*/'@/views/permission/app/index.vue');
const apigwPermissionRecords = () => import(/* webpackChunkName: 'apigw-env'*/'@/views/permission/record/index.vue');
const apigwAccessLog = () => import(/* webpackChunkName: 'apigw-env'*/'@/views/operate-data/access-log/index.vue');
const apigwAccessLogDetail = () => import(/* webpackChunkName: 'apigw-env'*/'@/views/operate-data/access-log/detail.vue');
const apigwReport = () => import(/* webpackChunkName: 'apigw-env'*/'@/views/operate-data/report/index.vue');
const apigwBackendService = () => import(/* webpackChunkName: 'apigw-env'*/'@/views/backend-service/index.vue');
const ApiBasicInfo = () => import(/* webpackChunkName: 'apigw-env'*/'@/views/basic-info/index.vue');
const apigwMonitorAlarmStrategy = () => import(/* webpackChunkName: 'apigw-env'*/'@/views/monitor/alarm-strategy/index.vue');
const apigwMonitorAlarmHistory = () => import(/* webpackChunkName: 'apigw-env'*/'@/views/monitor/alarm-history/index.vue');
const ApigwOperateRecords  = () => import(/* webpackChunkName: 'apigw-env'*/'@/views/operate-records/index.vue');

// 文档一级路由出口
const docsComponent = {
  name: 'DocMain',
  template: '<router-view></router-view>',
};

const routes: RouteRecordRaw[] = [
  {
    path: '/',
    name: 'home',
    component: Home,
    meta: {
      isMenu: false,   // 是否作为侧边栏菜单
    },
  },
  {
    path: '/',
    name: 'apigwMain',
    component: ApigwMain,
    meta: {
      title: '资源管理',
      matchRoute: 'apigwMain',
    },
    children: [
      {
        path: ':id/stage',
        name: 'apigwStageOverview',
        component: apigwStageOverview,
        meta: {
          title: '环境管理',
          matchRoute: 'apigwStageOverview',
          customHeader: true,
        },
      },
      {
        path: ':id/stage/detail-mode',
        name: 'apigwStageDetail',
        component: apigwStageDetail,
        meta: {
          title: '环境概览',
          matchRoute: 'apigwStageOverview',
          customHeader: true,
        },
        children: [
          {
            path: '',
            name: 'apigwStageResourceInfo',
            component: apigwStageResourceInfo,
            meta: {
              title: '环境概览',
              matchRoute: 'apigwStageOverview',
            },
          },
          {
            path: 'plugin-manage',
            name: 'apigwStagePluginManage',
            component: apigwStagePluginManage,
            meta: {
              title: '环境概览',
              matchRoute: 'apigwStageOverview',
            },
          },
          {
            path: 'variable-manage',
            name: 'apigwStageVariableManage',
            component: apigwStageVariableManage,
            meta: {
              title: '环境概览',
              matchRoute: 'apigwStageOverview',
            },
          },
        ],
      },
      {
        path: '/:id/published',
        name: 'apigwReleaseHistory',
        component: apigwReleaseHistory,
        meta: {
          title: '发布记录',
          matchRoute: 'apigwReleaseHistory',
        },
      },
      {
        path: '/:id/resource',
        name: 'apigwResource',
        component: ApigwResource,
        meta: {
          title: '资源配置',
          matchRoute: 'apigwResource',
        },
      },
      {
        path: '/:id/resource/create',
        name: 'apigwResourceCreate',
        component: ApigwResourceEdit,
        meta: {
          title: '新建资源',
          matchRoute: 'apigwResource',
          showBackIcon: true,
        },
      },
      {
        path: '/:id/resource/:resourceId/edit',
        name: 'apigwResourceEdit',
        component: ApigwResourceEdit,
        meta: {
          title: '编辑资源',
          matchRoute: 'apigwResource',
          showBackIcon: true,
        },
      },
      {
        path: '/:id/resource/:resourceId/clone',
        name: 'apigwResourceClone',
        component: ApigwResourceEdit,
        meta: {
          title: '克隆资源',
          matchRoute: 'apigwResource',
          showBackIcon: true,
        },
      },
      {
        path: '/:id/version',
        name: 'apigwResourceVersion',
        component: apigwResourceVersion,
        meta: {
          title: '资源版本',
          matchRoute: 'apigwResourceVersion',
          isCustomTopbar: 'resourceVersionOverview',
        },
      },
      {
        path: '/:id/online',
        name: 'apigwOnlineTest',
        component: apigwOnlineTest,
        meta: {
          title: '在线调试',
          matchRoute: 'apigwOnlineTest',
        },
      },
      {
        path: '/:id/resource/import',
        name: 'apigwResourceImport',
        component: ApigwResourceImport,
        meta: {
          title: '导入资源配置',
          matchRoute: 'apigwResource',
          showBackIcon: true,
        },
      },
      {
        path: '/:id/backend-service',
        name: 'apigwBackendService',
        component: apigwBackendService,
        meta: {
          title: '后端服务',
          matchRoute: 'apigwBackendService',
        },
      },
      {
        path: '/:id/permission/applys',
        name: 'apigwPermissionApplys',
        component: apigwPermissionApplys,
        meta: {
          title: '权限审批',
          matchRoute: 'apigwPermissionApplys',
        },
      },
      {
        path: '/:id/permission/apps',
        name: 'apigwPermissionApps',
        component: apigwPermissionApps,
        meta: {
          title: '应用权限',
          matchRoute: 'apigwPermissionApps',
        },
      },
      {
        path: '/:id/permission/records',
        name: 'apigwPermissionRecords',
        component: apigwPermissionRecords,
        meta: {
          title: '审批历史',
          matchRoute: 'apigwPermissionRecords',
        },
      },
      {
        path: '/:id/access-log',
        name: 'apigwAccessLog',
        component: apigwAccessLog,
        meta: {
          title: '流水日志',
          matchRoute: 'apigwAccessLog',
        },
      },
      {
        path: '/:id/access-log/:requestId',
        name: 'apigwAccessLogDetail',
        component: apigwAccessLogDetail,
        meta: {
          title: '流水日志',
          matchRoute: 'apigwAccessLogDetail',
        },
      },
      {
        path: '/:id/report',
        name: 'apigwReport',
        component: apigwReport,
        meta: {
          title: '统计报表',
          matchRoute: 'apigwReport',
        },
      },
      {
        path: '/:id/monitor/alarm-strategy',
        name: 'apigwMonitorAlarmStrategy',
        component: apigwMonitorAlarmStrategy,
        meta: {
          title: '告警策略',
          matchRoute: 'apigwMonitorAlarmStrategy',
        },
      },
      {
        path: '/:id/monitor/alarm-history',
        name: 'apigwMonitorAlarmHistory',
        component: apigwMonitorAlarmHistory,
        meta: {
          title: '告警历史',
          matchRoute: 'apigwMonitorAlarmHistory',
        },
      },
      {
        path: '/:id/resource/import-doc',
        name: 'apigwResourceImportDoc',
        component: ApigwResourceImportDoc,
        meta: {
          title: '导入资源文档',
          matchRoute: 'apigwResource',
          showBackIcon: true,
        },
      },
      {
        path: '/:id/basic-info',
        name: 'apigwBasicInfo',
        component: ApiBasicInfo,
        meta: {
          title: '基本信息',
          matchRoute: 'apigwBasicInfo',
        },
      },
      {
        path: '/:id/operate-records',
        name: 'apigwOperateRecords',
        component: ApigwOperateRecords,
        meta: {
          title: '操作记录',
          matchRoute: 'apigwOperateRecords',
        },
      },
    ],
  },
  // 文档路由映射
  {
    path: `${globalConfig.PREV_URL}`,
    redirect: `${globalConfig.PREV_URL}/apigw-api/`,
    name: 'docsMain',
    component: docsComponent,
    alias: '',
    children: [
      {
        path: 'apigw-api',
        name: 'apigwDoc',
        component: ApigwDocs,
        meta: {
          matchRoute: 'apigwDoc',
          notAppHeader: true,
          isDocRouter: true,
          isMenu: false,   // 是否作为侧边栏菜单
        },
      },
      {
        path: 'apigw-api/:apigwId/',
        name: 'apigwAPIDetail',
        component: ApigwAPIDetail,
        meta: {
          matchRoute: 'apigwAPIDetail',
          isDocRouter: true,
        },
        children: [
          {
            path: 'apigw-api/:apigwId/intro',
            alias: '',
            name: 'apigwAPIDetailIntro',
            component: ApigwAPIDetailIntro,
            meta: {
              matchRoute: 'apigwAPIDetailIntro',
              isDocRouter: true,
            },
          },
          {
            path: 'apigw-api/:apigwId/:resourceId/doc',
            alias: '',
            name: 'apigwAPIDetailDoc',
            component: ApigwAPIDetailDoc,
            meta: {
              matchRoute: 'apigwAPIDetailDoc',
              isDocRouter: true,
            },
          },
        ],
      },
    ],
  },
];
export default createRouter({
  history: createWebHistory(window.SITE_URL),
  routes,
});
