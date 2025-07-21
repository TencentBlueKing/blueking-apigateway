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
export interface IApprovalListItem {
  bk_app_code: string
  applied_by: string
  applied_time: string
  handled_by: string
  handled_time: string
  reason: string
  status: string
  comment: string
  grant_dimension_display: string
  expire_days_display: number
  resourceList: any[]
  resource_ids: any[]
  handled_resources: any[]
}

export interface IPermission {
  id: number // 权限ID
  bk_app_code: string // 蓝鲸应用编码
  resource_id: number // 资源ID
  resource_name: string // 资源名称
  resource_path: string // 资源路径
  resource_method: string // 资源方法
  expires: string // 过期时间
  grant_dimension: string // 授权维度
  grant_type: string // 授权类型
  renewable: boolean // 是否可续期
  detail?: unknown[] // 详细信息（可选）
}

export interface IFilterValues {
  id: number | string // 过滤器ID
  name: string // 过滤器名称
  values: IFilterValue[] // 过滤器值数组
  type?: string // 过滤器类型（可选）
}

export interface IResource {
  id: number // 资源ID
  method: string // 资源方法
  name: string // 资源名称
  path: string // 资源路径
}

export interface IFilterValue {
  id: number | string // 过滤器值ID
  name: string // 过滤器值名称
};

export interface IFilterSearchParams {
  op_type: string // 操作类型
  op_status: string // 操作状态
  op_object?: string // 操作对象（可选）
  op_object_type: string // 操作对象类型
  username?: string // 用户名（可选）
  time_start?: string // 开始时间（可选）
  time_end?: string // 结束时间（可选）
  keyword?: string // 关键词（可选）
  order_by?: string // 排序字段（可选）
}
