import { createRouter, createWebHashHistory } from 'vue-router';
import getStageManagementRoutes from '@/views/stage-management/routes.ts';
import getBasicInfoRoutes from '@/views/basic-info/routes.ts';

const router = createRouter({
  history: createWebHashHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'Home',
      component: () => import('@/views/home/Index.vue'),
    },
    {
      path: '/:id',
      name: 'Resources',
      component: () => import('@/layout/my-gateway/Index.vue'),
      children: [
        ...getStageManagementRoutes(),
        ...getBasicInfoRoutes(),
      ],
    },
  ],
});

export default router;
