import {
  createRouter,
  createWebHistory,
  RouteRecordRaw,
} from 'vue-router';

const Home = () => import(/* webpackChunkName: "Home" */ '@/views/home.vue');
const ApigwMain = () => import(/* webpackChunkName: 'apigw-main'*/'@/views/main.vue');
const ApigwResource = () => import(/* webpackChunkName: 'apigw-main'*/'@/views/resource/index.vue');
const ApigwDoc = () => import(/* webpackChunkName: 'apigw-doc'*/'@/views/components/doc/index.vue');


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
        name: 'apigwDoc',
        component: ApigwDoc,
        meta: {
          title: '环境管理',
          matchRoute: 'apigwDoc',
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
    ],
  },
];
export default createRouter({
  history: createWebHistory(window.SITE_URL),
  routes,
});
