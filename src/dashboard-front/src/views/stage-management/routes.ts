import type { RouteRecordRaw } from 'vue-router';
import { t } from '@/locales';

const routes: RouteRecordRaw[] = [
  {
    path: 'stage',
    name: 'StageManagement',
    component: () => import('@/views/stage-management/Index.vue'),
    meta: {
      title: t('环境概览'),
      matchRoute: 'StageOverview',
    },
  },
];

export default function getStageManagementRoutes() {
  return routes;
}
