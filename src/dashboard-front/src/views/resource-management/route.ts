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

const route: RouteRecordRaw[] = [
  {
    path: 'resource',
    name: 'ResourceManagement',
    redirect: { name: 'ResourceSetting' },
    meta: {
      title: t('资源管理'),
      matchRoute: 'ResourceManagement',
    },
    children: [
      {
        path: 'setting',
        name: 'ResourceSetting',
        component: () => import('./settings/Index.vue'),
        meta: {
          title: t('资源配置'),
          matchRoute: 'ResourceManagement',
        },
      },
      {
        path: 'edit/:resourceId',
        name: 'ResourceEdit',
        component: () => import('./settings/edit/Index.vue'),
        meta: {
          title: t('编辑资源'),
          matchRoute: 'ResourceManagement',
          showBackIcon: true,
          showPageName: true,
        },
      },
      {
        path: 'create',
        name: 'ResourceCreate',
        component: () => import('./settings/edit/Index.vue'),
        meta: {
          title: t('新建资源'),
          matchRoute: 'ResourceManagement',
          showBackIcon: true,
        },
      },
      {
        path: 'clone/:resourceId',
        name: 'ResourceClone',
        component: () => import('./settings/edit/Index.vue'),
        meta: {
          title: t('克隆资源'),
          matchRoute: 'ResourceManagement',
          showBackIcon: true,
        },
      },
      {
        path: 'import',
        name: 'ResourceImport',
        component: () => import('./settings/import/Index.vue'),
        meta: {
          title: t('导入资源配置'),
          matchRoute: 'ResourceManagement',
          topMenu: 'home',
          showBackIcon: true,
        },
      },
      {
        path: 'import-doc',
        name: 'ResourceImportDoc',
        component: () => import('./settings/import-doc/Index.vue'),
        meta: {
          title: t('导入资源文档'),
          matchRoute: 'ResourceManagement',
          topMenu: 'home',
          showBackIcon: true,
        },
      },
      {
        path: 'version',
        name: 'ResourceVersion',
        component: () => import('./versions/Index.vue'),
        meta: {
          title: t('资源版本'),
          matchRoute: 'ResourceManagement',
          hideHeaderBorder: true,
        },
      },
    ],
  },
];

export default function getResourceManagementRoutes() {
  return route;
}
