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
    path: '/:id/monitor/alarm-strategy',
    name: 'MonitorAlarmStrategy',
    component: () => import('@/views//monitor-alarm/alarm-strategy/Index.vue'),
    meta: {
      title: t('告警策略'),
      matchRoute: 'MonitorAlarmStrategy',
      enabled: true,
    },
  },
  {
    path: '/:id/monitor/alarm-history',
    name: 'MonitorAlarmHistory',
    component: () => import('@/views/monitor-alarm/alarm-history/Index.vue'),
    meta: {
      title: t('告警记录'),
      matchRoute: 'MonitorAlarmHistory',
      enabled: true,
    },
  },
];

export default function getMonitorAlarmRoutes() {
  return routes;
}
