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
* 流水日志相关类型
*  */

export interface ISearchParamsInterface {
  stage_id?: number // 阶段ID，可选
  resource_id?: string | number // 资源ID，可以是字符串或数字，可选
  time_start?: string | number // 开始时间，可以是字符串或数字，可选
  time_end?: string | number // 结束时间，可以是字符串或数字，可选
  query?: string // 查询字符串，可选
  backend_name?: string // 后端服务名称，可选
}

export interface ILogDetailInterface {
  offset?: number // 偏移量，可选
  limit?: number // 限制数量，可选
  bk_nonce: string // 随机数，用于安全验证
  bk_signature: string // 签名，用于安全验证
  bk_timestamp: string // 时间戳，用于安全验证
  shared_by: string // 共享者信息
}
