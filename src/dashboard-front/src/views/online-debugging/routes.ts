import type { RouteRecordRaw } from 'vue-router';
import { t } from '@/locales';

const routes: RouteRecordRaw[] = [
  {
    path: 'online-debugging',
    name: 'OnlineDebugging',
    component: () => import('@/views/online-debugging/Index.vue'),
    meta: {
      title: t('在线调试'),
      matchRoute: 'OnlineDebugging',
    },
  },
];

export default function getOnlineDebuggingRoutes() {
  return routes;
}
