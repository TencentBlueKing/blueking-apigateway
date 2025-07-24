import type { RouteRecordRaw } from 'vue-router';
import { t } from '@/locales';

const routes: RouteRecordRaw[] = [
  {
    path: 'log',
    name: 'AccessLog',
    component: () => import('@/views/operate-data/access-log/Index.vue'),
    meta: {
      title: t('流水日志'),
      matchRoute: 'AccessLog',
      topMenu: 'home',
    },
  },
  {
    path: 'access-log/:requestId',
    name: 'AccessLogDetail',
    component: () => import('@/views/operate-data/access-log/Detail.vue'),
    meta: {
      title: t('流水日志'),
      matchRoute: 'AccessLogDetail',
      topMenu: 'home',
      isMenu: false,
    },
  },
  {
    path: 'dashboard',
    name: 'Dashboard',
    component: () => import('@/views/operate-data/dashboard/Index.vue'),
    meta: {
      title: t('仪表盘'),
      matchRoute: 'Dashboard',
      topMenu: 'home',
    },
  },
  {
    path: 'report',
    name: 'Report',
    component: () => import('@/views/operate-data/report/Index.vue'),
    meta: {
      title: t('统计报表'),
      matchRoute: 'Report',
      topMenu: 'home',
    },
  },
];

export default function getOperateDataRoutes() {
  return routes;
}
