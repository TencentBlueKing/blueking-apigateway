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
