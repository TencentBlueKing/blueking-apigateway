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

import type { IPersonalWorkbenchListResponse, IResources } from '@/services/types/responses/personal-workbench.ts';

// 个人工作台 —> MCP Server 列表/ gateway tab选项
export type ITabKey = 'gateway' | 'mcp';

// 个人工作台 —> MCP Server 列表/ gateway 审批状态
export type IApplyStatus = '' | 'approved' | 'rejected';

// 个人工作台 —> 我的待办、我的已办、我的申请
export type IApprovalStatus = 'pending' | 'applied' | 'handled';

//  个人工作台 —> 接口响应内容和自定义UI界面变量
export type IPersonalWorkbenchUIState = IPersonalWorkbenchListResponse & {
  isExpand: boolean
  isSelectAll: boolean
  isLoading?: boolean
  gateway_id?: number
  resource_ids: number[]
  selection?: IResources[]
};

// 个人工作台 —> MCP Server 列表/ gateway 列表请求参数
export interface IPersonalWorkbenchListQuery {
  limit?: number
  offset?: number
  keyword?: string
  time_start?: string | number
  time_end?: string | number
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

// 个人工作台 —> MCP Server 列表/ gateway 审批参数
export interface IFomDataQuery {
  id?: number
  gateway_id?: number
  ids?: number[]
  status?: IApplyStatus
  comment?: string
  part_resource_ids?: Record<string, unknown>
  mcp_server_id?: string | number
};

// 个人工作台 —> MCP Server 列表/ gateway tab选项
export interface IPermission {
  bk_app_code: string
  grant_dimension: string
  isSelectAll: boolean
  resources?: IResources[]
  selection?: IResources[]
  resource_ids: number[]
}
