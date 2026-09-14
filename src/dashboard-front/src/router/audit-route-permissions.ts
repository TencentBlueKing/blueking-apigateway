/*
 * TencentBlueKing is pleased to support the open source community by making
 * 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
 * Copyright (C) Tencent. All rights reserved.
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
import type { GatewayPermissionKey } from '@/constants/gateway-permission';

/**
 * 递归收集未声明 meta.permission 的网关内叶子页面
 * permission 支持从父路由继承，与 vue-router 的 meta 合并行为保持一致
 */
function collectMissingPermissionRoutes(
  records: readonly RouteRecordRaw[],
  inherited: GatewayPermissionKey | undefined,
  missing: string[],
) {
  records.forEach((record) => {
    const permission = record.meta?.permission ?? inherited;

    if (record.children?.length) {
      collectMissingPermissionRoutes(record.children, permission, missing);
      return;
    }

    // 仅检查真正会渲染页面的叶子路由，重定向与分组节点无需声明权限
    const isLeafPage = 'component' in record && !!record.component;
    if (isLeafPage && !record.meta?.skipRoleCheck && !permission) {
      missing.push(String(record.name ?? record.path));
    }
  });
}

/**
 * 开发环境下体检网关内路由的权限声明
 * 运营者角色采用 fail-closed 策略，漏标 meta.permission 会导致页面静默 404，
 * 这里在应用启动时一次性全量提示，避免等到有人访问才发现
 */
export function auditGatewayRoutePermissions(records: readonly RouteRecordRaw[]) {
  const missing: string[] = [];
  collectMissingPermissionRoutes(records, undefined, missing);

  if (missing.length) {
    console.warn(
      `[route-permission] 以下 ${missing.length} 个网关内路由未声明 meta.permission，`
      + `运营者角色将无法访问：\n  - ${missing.join('\n  - ')}\n`
      + '请在对应 route 文件的 meta 中补充权限矩阵 key（GatewayPermissionKey）。',
    );
  }
}
