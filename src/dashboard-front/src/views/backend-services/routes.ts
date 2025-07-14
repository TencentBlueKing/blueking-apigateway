import type { RouteRecordRaw } from 'vue-router';
import { t } from '@/locales';

const routes: RouteRecordRaw[] = [
  {
    path: 'backend',
    name: 'BackendService',
    component: () => import('@/views/backend-services/Index.vue'),
    meta: {
      title: t('后端服务'),
      matchRoute: 'BackendService',
      topMenu: 'Home',
    },
  },
];

export default function getBackendServicesRoutes() {
  return routes;
}
