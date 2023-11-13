import {
  createRouter,
  createWebHistory,
  RouteRecordRaw,
} from 'vue-router';

const Home = () => import(/* webpackChunkName: "Home" */ '@/views/home.vue');
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
      }, {
        path: '/:id/resource/import-doc',
        name: 'apigwResourceImportDoc',
        component: ApigwResourceImportDoc,
        meta: {
          title: '导入资源文档',
          matchRoute: 'apigwResource',
          showBackIcon: true,
        },
      },
    ],
  },
];
export default createRouter({
  history: createWebHistory(window.SITE_URL),
  routes,
});
