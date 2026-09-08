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
 * 网关成员的角色授权策略（纯数据，不含任何文案与 i18n 依赖）
 *
 * 此文件是「谁能访问什么」的唯一事实源，被路由守卫、路由 meta、通用 hook 与布局菜单共同消费。
 * 面向用户展示的中文标签、悬浮说明及矩阵表格等呈现层逻辑，位于
 * `@/views/member-management/` 目录（constants.ts 存文案、utils.ts 存展示函数），
 * 由该处读取本策略拼装而成。
 */

import type { GatewayMemberRole } from '@/services/types/responses/gateway-members';

export type MemberRole = GatewayMemberRole;

export const MEMBER_ROLES: MemberRole[] = ['administrator', 'operator'];

/**
 * 权限 key 白名单
 *
 * 每个 key 对应网关内左侧导航的一个菜单项（少数为页面内的能力开关），
 * 顺序与 `src/layout/my-gateway/Index.vue` 的 menuList 保持一致。
 *
 * 新增页面的登记流程：
 * 1. 在此登记 key；
 * 2. 在下方 GATEWAY_PERMISSION_MATRIX 中补充角色授权（Record 类型强制要求，漏写即编译报错）；
 * 3. 在 `views/member-management/constants.ts` 的 PERMISSION_LABELS 中补充展示文案（同上）；
 * 4. 在对应路由文件的 meta.permission 中引用（有类型补全，拼错即编译报错）。
 */
export const GATEWAY_PERMISSION_KEYS = [
  // 环境管理（含「环境概览」「发布记录」）—— StageManagement
  'stage',
  // 后端服务 —— BackendService
  'backend',
  // 模型服务，仅 AI 网关展示 —— ModelService
  'model',
  // 资源管理（含「资源配置」「资源版本」及资源的新建/编辑/克隆/导入）—— ResourceManagement
  'resource',
  // 权限管理（含「权限审批」「应用权限」「审批历史」）—— PermissionApply / PermissionApp
  'permission',
  // 运行数据（含「流水日志」「仪表盘」「统计报表」）—— AccessLog / Dashboard / Report
  'runtime',
  // 监控告警 >「告警策略」—— MonitorAlarmStrategy
  'alarm-strategy',
  // 监控告警 >「告警记录」—— MonitorAlarmHistory
  'alarm-history',
  // 在线调试 —— OnlineDebugging
  'debug',
  // MCP >「MCP Server」（含 Server 详情）—— MCPServer / MCPServerDetail
  'mcp-server',
  // MCP >「MCP 权限管理」—— MCPServerPermission
  'mcp-perm',
  // MCP >「可观测」—— MCPServerObservability
  'mcp-obs',
  // 网关设置 >「基本信息」的只读查看 —— BasicInfo
  'basic-view',
  // 网关设置 >「基本信息」的编辑能力，非独立菜单项，控制该页内的启停/删除/改配置等操作
  'basic-edit',
  // 网关设置 >「成员管理」—— MemberManagement
  'member',
  // 网关设置 >「操作记录」—— AuditLog
  'audit',
] as const;

export type GatewayPermissionKey = typeof GATEWAY_PERMISSION_KEYS[number];

export interface IGatewayPermissionRule {
  administrator: boolean
  operator: boolean
  // 仅 AI 网关（kind === 2）下生效
  aiOnly?: boolean
}

/**
 * 角色 × 权限 授权矩阵
 * 调整某个角色的可访问范围时，只需在此翻转布尔值，
 * 路由拦截与成员管理页的权限说明表会同步生效
 */
export const GATEWAY_PERMISSION_MATRIX: Record<GatewayPermissionKey, IGatewayPermissionRule> = {
  'stage': {
    administrator: true,
    operator: false,
  },
  'backend': {
    administrator: true,
    operator: false,
  },
  'model': {
    administrator: true,
    operator: false,
    aiOnly: true,
  },
  'resource': {
    administrator: true,
    operator: false,
  },
  'permission': {
    administrator: true,
    operator: true,
  },
  'runtime': {
    administrator: true,
    operator: true,
  },
  'alarm-strategy': {
    administrator: true,
    operator: false,
  },
  'alarm-history': {
    administrator: true,
    operator: true,
  },
  'debug': {
    administrator: true,
    operator: false,
  },
  'mcp-server': {
    administrator: true,
    operator: false,
  },
  'mcp-perm': {
    administrator: true,
    operator: true,
  },
  'mcp-obs': {
    administrator: true,
    operator: true,
  },
  'basic-view': {
    administrator: true,
    operator: true,
  },
  'basic-edit': {
    administrator: true,
    operator: false,
  },
  'member': {
    administrator: true,
    operator: false,
  },
  'audit': {
    administrator: true,
    operator: false,
  },
};
