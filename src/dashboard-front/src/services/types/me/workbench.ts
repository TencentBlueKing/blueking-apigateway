/*
 * TencentBlueKing is pleased to support the open source community by making
 * 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
 * Copyright (C) 2026 Tencent. All rights reserved.
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

import type { IResource } from '@/types/permission';

// 个人工作台 —> 我的待办、我的已办、我的申请
export type IApprovalStatus = 'pending' | 'applied' | 'handled';

// 个人工作台 —> MCP Server 列表/ gateway 列表请求参数
export interface IPersonalWorkbenchListQuery {
  limit?: number
  offset?: number
  keyword?: string
  /** 开始时间（Unix 秒），>= time_start；两端各自生效，同时传时起点不得晚于终点 */
  time_start?: number
  /** 结束时间（Unix 秒），<= time_end */
  time_end?: number
  applied_by?: string | string[]
  bk_app_code?: string
  gateway_id?: string | number
  mcp_server_id?: string | number
  grant_dimension?: string
}

// 个人工作台 - 下拉筛选选项列表请求参数
export interface IPersonalWorkbenchFilterOptionQuery {
  type: IApprovalStatus
}

// 个人工作台 - 下拉筛选选项列表返回参数
export interface IPersonalWorkbenchFilterOptionResponse {
  id: number
  name: string
  display_name?: string
  title?: string
  gateway_id?: number
  gateway_name?: string
  gateway_display_name?: string
}

// 个人工作台 - 我的待办数量统计返回参数
export interface IPersonalWorkbenchPendingCountResponse {
  gateways: number
  mcp_servers: number
  total: number
}

// 个人工作台 —> MCP Server 列表/ gateway 列表响应参数
export interface IPersonalWorkbenchListResponse {
  id: number
  bk_app_code: string
  gateway_id?: number
  gateway_name?: string
  gateway_display_name?: string
  grant_dimension?: string
  grant_dimension_display?: string
  expire_days: number
  expire_days_display?: string
  reason: string
  applied_by: string
  created_time?: string
  status: string
  status_display?: string
  itsm_ticket_id?: string
  itsm_ticket_url?: string
  applied_time?: string
  handled_by?: string
  handled_time?: string | null
  comment?: string
  mcp_server?: {
    id: number
    name: string
    title: string
    gateway_name: string
    gateway_display_name?: string
    gateway_id: number
  }
  resources?: IResource[]
  approvers?: string[]
}
