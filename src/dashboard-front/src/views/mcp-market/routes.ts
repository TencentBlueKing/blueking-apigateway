import type { RouteRecordRaw } from 'vue-router';
import { t } from '@/locales';

const routes: RouteRecordRaw[] = [
  {
    path: '/mcp-market',
    name: 'McpMarket',
    component: () => import('@/layout/mcp-market/Index.vue'),
    meta: {
      title: t('MCP 市场'),
      matchRoute: 'McpMarket',
      topMenu: 'McpMarket',
    },
  },
  {
    path: '/mcp-market-details/:id',
    name: 'McpMarketDetails',
    component: () => import('@/views/mcp-market/Details.vue'),
    meta: {
      title: t('MCP 详情'),
      matchRoute: 'McpMarket',
      topMenu: 'McpMarket',
    },
  },
];

export default function getMcpMarketRoutes() {
  return routes;
}
