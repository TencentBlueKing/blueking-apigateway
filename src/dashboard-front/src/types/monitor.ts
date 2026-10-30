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
* 监控告警相关类型
*  */

export interface IAlarmStrategy {
  id: number
  name: string
  alarm_type: string
  alarm_subtype: string
  updated_time?: string
  effective_stages: string[]
  gateway_labels?: number[]
  config?: {
    detect_config?: {
      count: number
      duration: number
      method: string
    }
    converge_config?: { duration: number }
    notice_config?: {
      notice_way: string[]
      notice_role: string[]
      notice_extra_receiver: string[]
    }
    filter_config?: {
      type: string
      match: string
      items: string[]
    }
  }
  enabled?: boolean
}

export interface IAlarmRecord {
  id: number
  alarm_id: string
  status: string
  message: string
  created_time: string
  comment: string
  alarm_strategy_names: string[]
}
