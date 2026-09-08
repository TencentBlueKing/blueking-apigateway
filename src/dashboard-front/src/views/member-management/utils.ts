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

/**
 * 成员管理的角色展示纯函数
 *
 * 均为无状态纯函数：输入角色，输出面向用户的文案或视图数据。
 * 角色授权策略位于 `@/constants/gateway-permission`
 */

import type { MemberRole } from '@/constants/gateway-permission';
import { PERMISSION_ITEMS } from './constants';
import i18n from '@/locales';

// 角色名称
export function getRoleLabel(role: MemberRole) {
  return role === 'administrator' ? i18n.global.t('管理员') : i18n.global.t('运营者');
}

// 单个角色的权限描述
export function getRoleDescription(role: MemberRole) {
  return role === 'administrator'
    ? i18n.global.t('拥有全部权限')
    : i18n.global.t('可管理权限审批、运行数据、告警记录、MCP 权限与可观测，以及查看基本信息');
}

// 指定角色在当前网关类型下可访问的权限项
export function getRolePermissions(role: MemberRole, isAIGateway: boolean) {
  return PERMISSION_ITEMS.filter(item => (!item.aiOnly || isAIGateway) && item[role]);
}
