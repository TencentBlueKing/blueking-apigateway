import {
  createRouter,
  createWebHistory,
} from 'vue-router';

const Home = () => import(/* webpackChunkName: "Home" */ '@/views/home.vue');
const ApigwMain = () => import(/* webpackChunkName: 'apigw-main'*/'@/views/main.vue');
const ApigwResource = () => import(/* webpackChunkName: 'apigw-main'*/'@/views/resource/index.vue');
const ApigwDoc = () => import(/* webpackChunkName: 'apigw-doc'*/'@/views/components/doc/index.vue');

export default createRouter({
  history: createWebHistory(window.SITE_URL),
  routes: [
    {
      path: '/',
      name: 'home',
      component: Home,
    },
    {
      path: '/apigw-api',
      name: 'apigwDoc',
      component: ApigwDoc,
    },
    {
      path: '/',
      component: ApigwMain,
      children: [
        {
          path: '/:id/resource',
          name: 'apigwResource',
          component: ApigwResource,
          meta: {
            title: '资源管理',
            matchRoute: 'apigwResource',
          },
        },
      ],
    },
  ],
});
