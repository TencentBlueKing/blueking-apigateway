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

/*
* 操作记录相关类型
*  */

export interface IAuditLog {
  // 操作类型
  op_type: string
  // 操作状态
  op_status: string
  // 操作对象
  op_object?: string
  // 操作对象类型
  op_object_type: string
  // 用户名
  username?: string
  // 开始时间（Unix 秒），未选择时为空字符串
  time_start?: number | ''
  // 结束时间（Unix 秒），未选择时为空字符串
  time_end?: number | ''
  // 关键词（可选）
  keyword?: string
  // 排序字段（可选）
  order_by?: string
}
