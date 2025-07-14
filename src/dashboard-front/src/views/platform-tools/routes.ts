import type { RouteRecordRaw } from 'vue-router';
import { t } from '@/locales';

const routes: RouteRecordRaw[] = [
  {
    path: 'toolbox',
    name: 'PlatformToolsToolbox',
    component: () => import('@/views/platform-tools/toolbox/Index.vue'),
    meta: {
      title: t('工具箱'),
      matchRoute: 'PlatformToolsToolbox',
      topMenu: 'PlatformTools',
    },
  },
  {
    path: 'automated-gateway',
    name: 'PlatformToolsAutomatedGateway',
    component: () => import('@/views/platform-tools/automated-gateway/Index.vue'),
    meta: {
      title: t('自动化接入网关'),
      matchRoute: 'PlatformToolsAutomatedGateway',
      topMenu: 'PlatformTools',
    },
  },
  {
    path: 'programmable-gateway',
    name: 'PlatformToolsProgrammableGateway',
    component: () => import('@/views/platform-tools/programmable-gateway/Index.vue'),
    meta: {
      title: t('可编程网关'),
      matchRoute: 'PlatformToolsProgrammableGateway',
      topMenu: 'PlatformTools',
    },
  },
];

export default function getPlatformToolsRoutes() {
  return routes;
}
