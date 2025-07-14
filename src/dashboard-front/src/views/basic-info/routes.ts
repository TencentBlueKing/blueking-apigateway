import type { RouteRecordRaw } from 'vue-router';
import { t } from '@/locales';

const routes: RouteRecordRaw[] = [
  {
    path: 'basic-info',
    name: 'BasicInfo',
    component: () => import('@/views/basic-info/Index.vue'),
    meta: {
      title: t('基本信息'),
      matchRoute: 'BasicInfo',
    },
  },
];

export default function getBasicInfoRoutes() {
  return routes;
}
