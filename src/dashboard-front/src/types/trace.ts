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

// 调用链瀑布图（components/mcp/trace-view）的数据模型，由 useTrace Store 与瀑布图组件共用
// 这里的 ISpan 是瀑布图展示用的 span，在接口返回的 span（observability.ts 的 ISpan）上补充了层级、折叠等字段

import type { ISpan as ITraceSpan } from '@/types/observability';

export type GroupInfo = {
  duration: number
  id: string
  members: string[]
};

export type KeyValuePair = {
  key: string
  value: any
};

export type Log = {
  fields: Array<KeyValuePair>
  timestamp: number
};

export type Process = {
  serviceName: string
  tags: Array<KeyValuePair>
};

export type SpanAttributesItem = {
  key: string
  query_key: string
  query_value: string
  type: string
  value: string
};

export type ISpanData = {
  id?: number | string
  app_code?: string
  attributes?: Array<SpanAttributesItem>
  bgColor?: string
  color?: string
  duration?: number
  ebpf_kind?: string // ebpf 类型
  ebpf_tap_port_name?: string
  ebpf_tap_side?: string
  ebpf_thread_name?: string
  error?: boolean
  group_info?: GroupInfo // 折叠分组信息
  icon?: string
  is_expand: boolean // 折叠节点当前被展开
  is_virtual?: boolean // 是否推断（虚拟）span
  kind?: number
  logs?: Array<Log>
  mark?: string
  operation: string
  processID?: string
  references?: Array<ISpanReference>
  service: string
  source?: string
  span_id: string
  startTime?: number
  start_offset_ms: number
  tags?: Array<KeyValuePair>
  trace_id?: string
  warnings?: Array<string> | null
};

export type ISpan = ITraceSpan & ISpanData & {
  depth: number
  hasChildren: boolean
  references?: NonNullable<ISpanData['references']>
  relativeStartTime?: number
  subsidiarilyReferencedBy?: Array<ISpanReference>
  tags?: NonNullable<ISpanData['tags']>
  warnings?: NonNullable<ISpanData['warnings']>
};

export type ISpanReference = {
  refType: 'CHILD_OF' | 'FOLLOWS_FROM'
  span: ISpan | undefined
  span_id: string
  trace_id: string
};

export type DirectionType = 'ltr' | 'rtl';

export interface IDetailInfo {
  [key: string]: any
  app_code?: string
  category?: string // 调用类型
  error?: boolean // 入口服务感叹号
  hierarchy_count: number
  max_duration: number
  min_duration: number
  product_time: number
  root_endpoint?: string
  root_service?: string
  root_span_id: string
  service_count: number
  time_error: boolean
  trace_duration: number
  trace_end_time?: number
  trace_start_time?: number
  status_code?: {
    type: string
    value: number
  }
}

export interface ISpanListItem {
  [key: string]: any
  elapsed_time: number | string
  end_time: number | string
  kind: number
  parent_span_id: string
  span_id: string
  span_name: string
  start_time: number | string
  time: string
  trace_id: string
  trace_state: string
  resource: {
    'bk.instance.id': string
    'bk_data_id': number
    'service.name': string
    'service.version': string
    'telemetry.sdk.language': string
    'telemetry.sdk.name': string
    'telemetry.sdk.version': string
  }
  status: {
    code: number
    message: string
  }
  status_code: {
    type: string
    value: string
  }
}

export interface ITraceListItem {
  [key: string]: any
  appName?: string
  duration?: string
  entryEndpoint?: string
  entryService?: string
  status?: string
  statusCode?: number
  time?: number
  trace_id: string
  trace_info: IDetailInfo
  type?: string
}

export interface ITraceTree {
  [key: string]: any
  duration?: number
  endTime?: number
  entryEndpoint?: string
  entryService?: string
  processes?: Record<string, Process>
  spans: ISpan[]
  startTime?: number
  status?: string
  statusCode?: string
  time?: string
  trace_id?: string
  type?: string
}
