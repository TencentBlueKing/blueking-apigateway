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
import { t } from '@/locales';

// 方法名称
export const METHODS_CONSTANTS = [
  {
    id: 'GET',
    name: 'GET',
  },
  {
    id: 'POST',
    name: 'POST',
  },
  {
    id: 'PUT',
    name: 'PUT',
  },
  {
    id: 'PATCH',
    name: 'PATCH',
  },
  {
    id: 'DELETE',
    name: 'DELETE',
  },
  {
    id: 'HEAD',
    name: 'HEAD',
  },
  {
    id: 'OPTIONS',
    name: 'OPTIONS',
  },
  {
    id: 'ANY',
    name: 'ANY',
  },
];

// 授权维度
export const AUTHORIZATION_DIMENSION = [
  {
    id: 'api',
    name: t('按网关'),
  },
  {
    id: 'resource',
    name: t('按资源'),
  },
];

// 时间维度
export const EXPIRE_DAYS_CONSTANTS = [
  {
    label: t('永久'),
    value: 0,
  },
  {
    label: t('6个月'),
    value: 180,
  },
  {
    label: t('12个月'),
    value: 360,
  },
];
