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
import { type RouteRecordRaw } from 'vue-router';
import { t } from '@/locales';

const ComponentsIntro = () => import('@/views/component-management/intro/Index.vue');
const ComponentsSystem = () => import('@/views/component-management/system/Index.vue');
const ComponentsManage = () => import('@/views/component-management/manage/Index.vue');
const ComponentsCategory = () => import('@/views/component-management/category/Index.vue');
const ComponentsRuntimeData = () => import('@/views/component-management/runtime-data/Index.vue');
const ComponentsRuntimeDetail = () => import('@/views/component-management/runtime-data/Detail.vue');
const SyncApigwAccess = () => import('@/views/component-management/manage/components/SyncAccess.vue');
const SyncHistory = () => import('@/views/component-management/manage/components/SyncHistory.vue');
const SyncVersion = () => import('@/views/component-management/manage/components/SyncVersion.vue');

// 组件管理
const routes: RouteRecordRaw[] = [
  {
    path: 'intro',
    name: 'ComponentsIntro',
    component: ComponentsIntro,
    meta: {
      title: t('简介'),
      matchRoute: 'ComponentsIntro',
      topMenu: 'ComponentsMain',
    },
  },
  {
    path: 'system',
    name: 'ComponentsSystem',
    component: ComponentsSystem,
    meta: {
      title: t('系统管理'),
      matchRoute: 'ComponentsSystem',
      topMenu: 'ComponentsMain',
    },
  },
  {
    path: 'access',
    name: 'ComponentsManage',
    component: ComponentsManage,
    meta: {
      title: t('组件管理'),
      matchRoute: 'ComponentsManage',
      topMenu: 'ComponentsMain',
    },
  },
  {
    path: 'sync',
    name: 'SyncApigwAccess',
    component: SyncApigwAccess,
    meta: {
      title: t('同步组件配置到 API 网关'),
      matchRoute: 'SyncApigwAccess',
      topMenu: 'ComponentsMain',
      showBackIcon: true,
    },
  },
  {
    path: 'history',
    name: 'SyncHistory',
    component: SyncHistory,
    meta: {
      title: t('组件同步历史'),
      matchRoute: 'SyncHistory',
      topMenu: 'ComponentsMain',
      showBackIcon: true,
    },
  },
  {
    path: 'version',
    name: 'SyncVersion',
    component: SyncVersion,
    meta: {
      title: t('组件同步版本'),
      matchRoute: 'SyncVersion',
      topMenu: 'ComponentsMain',
      showBackIcon: true,
    },
  },
  {
    path: 'category',
    name: 'ComponentsCategory',
    component: ComponentsCategory,
    meta: {
      title: t('文档分类'),
      matchRoute: 'ComponentsCategory',
      topMenu: 'ComponentsMain',
    },
  },
  {
    path: 'runtime-data',
    name: 'ComponentsRuntimeData',
    component: ComponentsRuntimeData,
    meta: {
      title: t('实时运行数据'),
      matchRoute: 'ComponentsRuntimeData',
      topMenu: 'ComponentsMain',
    },
  },
  {
    path: 'system/:system/detail',
    name: 'ComponentsRuntimeDetail',
    component: ComponentsRuntimeDetail,
    meta: {
      title: t('系统实时概况'),
      matchRoute: 'ComponentsRuntimeDetail',
      topMenu: 'ComponentsMain',
      showBackIcon: true,
    },
  },
];

export default function getComponentManagementRoutes() {
  return routes;
}
