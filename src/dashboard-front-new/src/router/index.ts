import {
  createRouter,
  createWebHistory,
  RouteRecordRaw,
} from 'vue-router';

const Home = () => import(/* webpackChunkName: "Home" */ '@/views/home.vue');
const ApigwMain = () => import(/* webpackChunkName: 'apigw-main'*/'@/views/main.vue');
const ApigwResource = () => import(/* webpackChunkName: 'apigw-main'*/'@/views/resource/index.vue');
const ApigwResourceEdit = () => import(/* webpackChunkName: 'apigw-doc'*/'@/views/resource/edit.vue');
const apigwStageOverview = () => import(/* webpackChunkName: 'apigw-env'*/'@/views/stage/overview/index.vue');
const apigwStageDetail = () => import(/* webpackChunkName: 'apigw-env'*/'@/views/stage/overview/detail-mode/index.vue');
const apigwReleaseHistory = () => import(/* webpackChunkName: 'apigw-env'*/'@/views/stage/published/index.vue');
const apigwStageResourceInfo = () => import(/* webpackChunkName: 'apigw-env'*/'@/views/stage/overview/detail-mode/resource-info.vue');
const apigwStagePluginManage = () => import(/* webpackChunkName: 'apigw-env'*/'@/views/stage/overview/detail-mode/plugin-manage.vue');
const apigwStageVariableManage = () => import(/* webpackChunkName: 'apigw-env'*/'@/views/stage/overview/detail-mode/variable-manage.vue');


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
        path: '/:id/stage',
        name: 'apigwStageOverview',
        component: apigwStageOverview,
        meta: {
          title: '环境管理',
          matchRoute: 'apigwStageOverview',
          isCustomTopbar: 'stageOverview',
        },
      },
      {
        path: '/:id/stage/detail-mode',
        name: 'apigwStageDetail',
        component: apigwStageDetail,
        meta: {
          title: '环境概览',
          matchRoute: 'apigwStageOverview',
          isCustomTopbar: 'stageOverview',
        },
        children: [
          {
            path: '',
            name: 'apigwStageResourceInfo',
            component: apigwStageResourceInfo,
            meta: {
              title: '环境概览',
              matchRoute: 'apigwStageOverview',
              isCustomTopbar: 'stageOverview',
            },
          },
          {
            path: 'plugin-manage',
            name: 'apigwStagePluginManage',
            component: apigwStagePluginManage,
            meta: {
              title: '环境概览',
              matchRoute: 'apigwStageOverview',
              isCustomTopbar: 'stageOverview',
            },
          },
          {
            path: 'variable-manage',
            name: 'apigwStageVariableManage',
            component: apigwStageVariableManage,
            meta: {
              title: '环境概览',
              matchRoute: 'apigwStageOverview',
              isCustomTopbar: 'stageOverview',
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
        },
      },
    ],
  },
];
export default createRouter({
  history: createWebHistory(window.SITE_URL),
  routes,
});
