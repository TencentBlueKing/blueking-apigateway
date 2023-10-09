import {
  createRouter,
  createWebHistory,
} from 'vue-router';

const Home = () => import(/* webpackChunkName: "Home" */ '@/views/home.vue');
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
  ],
});
