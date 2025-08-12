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
import type { RouteRecordRaw } from 'vue-router';
import { t } from '@/locales';

const routes: RouteRecordRaw[] = [
  {
    path: 'mcp',
    name: 'MCP',
    redirect: { name: 'MCPServer' },
    meta: { matchRoute: 'MCP' },
    children: [
      {
        path: 'server',
        name: 'MCPServer',
        component: () => import('@/views/mcp-server/Index.vue'),
        props: true,
        meta: {
          title: 'MCP Server',
          matchRoute: 'MCP',
          topMenu: 'MCP',
        },
      },
      {
        path: 'detail/:serverId',
        name: 'MCPServerDetail',
        component: () => import('@/views/mcp-server/detail/Index.vue'),
        meta: {
          title: t('详情'),
          matchRoute: 'MCP',
          topMenu: 'MCP',
        },
      },
      {
        path: 'permission',
        name: 'MCPServerPermission',
        component: () => import('@/views/mcp-server/permission/Index.vue'),
        meta: {
          title: t('权限审批'),
          matchRoute: 'MCP',
          topMenu: 'MCP',
          showBackIcon: true,
        },
      },
    ],
  },
];

export default function getMCPServerRoutes() {
  return routes;
}
