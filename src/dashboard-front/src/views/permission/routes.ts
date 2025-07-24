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
    path: '/:id/permission/apply',
    name: 'PermissionApply',
    component: () => import('@/views/permission/apply/Index.vue'),
    meta: {
      title: t('权限审批'),
      matchRoute: 'PermissionApply',
      topMenu: 'Home',
    },
  },
  {
    path: '/:id/permission/record',
    name: 'PermissionRecord',
    component: () => import('@/views/permission/record/Index.vue'),
    meta: {
      title: t('审批历史'),
      matchRoute: 'PermissionRecord',
      topMenu: 'Home',
      showBackIcon: true,
    },
  },
  {
    path: '/:id/permission/app',
    name: 'PermissionApp',
    component: () => import('@/views/permission/app/Index.vue'),
    meta: {
      title: t('应用权限'),
      matchRoute: 'PermissionApp',
      topMenu: 'Home',
    },
  },
];

export default function getPermissionManagementRoutes() {
  return routes;
}
