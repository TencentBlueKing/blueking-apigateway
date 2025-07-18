import type { RouteRecordRaw } from 'vue-router';
import { t } from '@/locales';

const routes: RouteRecordRaw[] = [
  {
    path: '/:id/audit',
    name: 'AuditLog',
    component: () => import('@/views/audit-log/Index.vue'),
    meta: {
      title: t('操作记录'),
      matchRoute: 'AuditLog',
    },
  },
];

export default function getAuditLogRoutes() {
  return routes;
}
