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
* 资源版本相关类型
*  */

export interface IVersionItem {
  id: number | string
  released_stages: {
    id: number
    name: string
  }[]
  sdk_count: number
  version: string
  schema_version: string
  comment: string
  created_time: string
  created_by: string
}

export interface IDiffData {
  add: Record<string, any>[]
  delete: Record<string, any>[]
  update: {
    source: Record<string, any>
    target: Record<string, any>
  }[]
}
