/*
 * TencentBlueKing is pleased to support the open source community by making
 * 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
 * Copyright (C) 2025 Tencent. All rights reserved.
 * Licensed under the MIT License (the "License"); you may not use this file except
 * in compliance with the License. You may obtain a copy of the License at
 *
 *     http://opensource.org/licenses/MIT
 *
 * Unless required by applicable law or agreed to in writing, software distributed under
 * the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND,
 * either express or implied. See the License for the specific language governing permissions and
 * limitations under the License.
 *
 * We undertake not to change the open source license (MIT license) applicable
 * to the current version of the project delivered to anyone in the future.
 */

import {
  type RouteLocationNormalized,
  type RouteRecordRaw,
  createRouter,
  createWebHistory,
} from 'vue-router';
// 环境概览
import getStageManagementRoutes from '@/views/stage-management/route';
// 资源管理
import getResourceManagementRoutes from '@/views/resource-management/route';
// 基本信息
import getBasicInfoRoutes from '@/views/basic-info/routes';
// 组件管理
import getComponentManagementRoutes from '@/views/component-management/route';
// 后端服务
import getBackendServicesRoutes from '@/views/backend-services/routes';
// 权限管理
import getPermissionManagementRoutes from '@/views/permission/routes';
// 平台工具
import getPlatformToolsRoutes from '@/views/platform-tools/routes.ts';
// MCP 市场
import getMcpMarketRoutes from '@/views/mcp-market/routes';
// 运行数据
import getOperateDataRoutes from '@/views/operate-data/route';
// 在线调试
import getOnlineDebuggingRoutes from '@/views/online-debugging/routes';
// 操作记录
import getAuditLogRoutes from '@/views/audit-log/routes';
// 告警策略
import getMonitorAlarmRoutes from '@/views/monitor-alarm/routes';
// MCP Server
import getMCPServerRoutes from '@/views/mcp-server/route';
// API 文档
import getAPIDocsRoutes from '@/views/api-docs/route';

function props(route: RouteLocationNormalized) {
  const { id } = route.params;
  return { id };
}

const routes: RouteRecordRaw[] = [
  {
    path: '/',
    name: 'Home',
    component: () => import('@/views/home/Index.vue'),
  },
  {
    path: '/:id',
    name: 'Resources',
    component: () => import('@/layout/my-gateway/Index.vue'),
    props,
    children: [
      ...getStageManagementRoutes(),
      ...getResourceManagementRoutes(),
      ...getBasicInfoRoutes(),
      ...getBackendServicesRoutes(),
      ...getPermissionManagementRoutes(),
      ...getOperateDataRoutes(),
      ...getOnlineDebuggingRoutes(),
      ...getAuditLogRoutes(),
      ...getMonitorAlarmRoutes(),
      ...getMCPServerRoutes(),
    ],
  },
  {
    path: '/platform-tools',
    name: 'PlatformTools',
    component: () => import('@/layout/platform-tools/Index.vue'),
    props,
    redirect: '/platform-tools/toolbox',
    children: [
      ...getPlatformToolsRoutes(),
    ],
  },
  ...getMcpMarketRoutes(),
  {
    path: '/components',
    name: 'ComponentsMain',
    component: () => import('@/layout/component-management/Index.vue'),
    props,
    redirect: '/components/access',
    children: [
      ...getComponentManagementRoutes(),
    ],
  },
  {
    path: '/docs',
    name: 'Docs',
    component: () => import('@/layout/docs/Index.vue'),
    redirect: { name: 'ApiDocs' },
    props,
    children: [
      ...getAPIDocsRoutes(),
    ],
  },
];

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
});

export default router;
