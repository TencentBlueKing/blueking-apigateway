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
 * 成员管理的呈现层常量
 *
 * 角色授权策略（谁能访问什么）位于 `@/constants/gateway-permission`，
 * 此文件只负责把策略翻译成面向用户的文案与视图数据
 */

import {
  GATEWAY_PERMISSION_KEYS,
  GATEWAY_PERMISSION_MATRIX,
  type GatewayPermissionKey,
} from '@/constants/gateway-permission';
import type { IPermissionItem } from './types';
import i18n from '@/locales';

interface IPermissionLabel {
  label: string
  tip?: string
}

// 权限项的展示文案，key 与授权矩阵一一对应，缺项即编译报错
const PERMISSION_LABELS: Record<GatewayPermissionKey, IPermissionLabel> = {
  'stage': {
    label: i18n.global.t('环境管理'),
    tip: i18n.global.t('包含概览、创建/编辑/删除环境、环境变量、插件、发布、下架、发布记录与失败重试'),
  },
  'backend': { label: i18n.global.t('后端服务') },
  'model': {
    label: i18n.global.t('模型服务'),
    tip: i18n.global.t('仅 AI 网关展示'),
  },
  'resource': {
    label: i18n.global.t('资源管理'),
    tip: i18n.global.t('包含资源配置、资源版本和 SDK 相关操作'),
  },
  'permission': {
    label: i18n.global.t('权限管理'),
    tip: i18n.global.t('包含权限审批和应用权限'),
  },
  'runtime': {
    label: i18n.global.t('运行数据'),
    tip: i18n.global.t('包含流水日志、仪表盘和统计报表'),
  },
  'alarm-strategy': { label: i18n.global.t('告警策略') },
  'alarm-history': { label: i18n.global.t('告警记录') },
  'debug': { label: i18n.global.t('在线调试') },
  'mcp-server': {
    label: i18n.global.t('MCP Server'),
    tip: i18n.global.t('包含创建/编辑/删除、启用/停用和使用指南'),
  },
  'mcp-perm': {
    label: i18n.global.t('MCP 权限管理'),
    tip: i18n.global.t('包含 MCP 权限审批和 MCP 应用权限'),
  },
  'mcp-obs': { label: i18n.global.t('MCP 可观测') },
  'basic-view': {
    label: i18n.global.t('基本信息查看'),
    tip: i18n.global.t('只读查看名称、描述、类型、状态和负责人'),
  },
  'basic-edit': {
    label: i18n.global.t('基本信息编辑'),
    tip: i18n.global.t('包含修改配置、启停和删除网关'),
  },
  'member': {
    label: i18n.global.t('成员管理'),
    tip: i18n.global.t('包含添加/移除成员和变更角色'),
  },
  'audit': { label: i18n.global.t('操作记录') },
};

// 由授权矩阵与展示文案拼装，顺序与 GATEWAY_PERMISSION_KEYS 一致
export const PERMISSION_ITEMS: IPermissionItem[] = GATEWAY_PERMISSION_KEYS.map(key => ({
  key,
  ...GATEWAY_PERMISSION_MATRIX[key],
  ...PERMISSION_LABELS[key],
}));
