import {
  createRouter,
  createWebHistory,
} from 'vue-router';

const HomeDemo = () => import(/* webpackChunkName: "HomeDemo" */ '../views/home-demo.vue');

export default createRouter({
  history: createWebHistory(window.SITE_URL),
  routes: [
    {
      path: '/',
      component: HomeDemo,
    },
  ],
});
