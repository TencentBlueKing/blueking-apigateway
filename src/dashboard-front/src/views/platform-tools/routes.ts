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
  {
    path: 'micro-gateway',
    name: 'PlatformToolsMicroGateway',
    component: () => import('@/views/platform-tools/micro-gateway/Index.vue'),
    meta: {
      title: t('蓝鲸微网关'),
      matchRoute: 'PlatformToolsMicroGateway',
      topMenu: 'PlatformTools',
    },
  },
];

export default function getPlatformToolsRoutes() {
  return routes;
}
