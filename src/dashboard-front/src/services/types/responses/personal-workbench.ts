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

// 个人工作台 - 下拉筛选选项列表返回参数
export interface IPersonalWorkbenchFilterOptionResponse {
  id: number
  name: string
  title?: string
}

// 个人工作台 - API 网关资源
export interface IResources {
  id: number
  method: string
  name: string
  path: string
}

// 个人工作台 —> MCP Server 列表/ gateway 列表响应参数
export interface IPersonalWorkbenchListResponse {
  id: number
  bk_app_code: string
  gateway_name: string
  grant_dimension: string
  grant_dimension_display: string
  expire_days: number
  expire_days_display: string
  reason: string
  applied_by: string
  created_time: string
  status: string
  itsm_ticket_id?: string
  itsm_ticket_url?: string
  applied_time?: string
  handled_by?: string
  handled_time: string
  comment?: string
  mcp_server?: {
    id: number
    name: string
    title: string
    gateway_name: string
    gateway_id: number
  }
  resources?: IResources[]
}
