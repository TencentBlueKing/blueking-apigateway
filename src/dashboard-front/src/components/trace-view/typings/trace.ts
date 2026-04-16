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

import type { ISpan as ITraceSpan } from '@/services/source/observability';

export type CrossRelation = {
  app_code: string
  bk_app_code: number
  bk_biz_id: number
  bk_biz_name: string
  permission: boolean
  trace_id: string
};

export type GroupInfo = {
  duration: number
  id: string
  members: string[]
};

export type KeyValuePair = {
  key: string
  value: any
};

export type Link = {
  text: string
  url: string
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

export type TNil = undefined | null;

export type Trace = TraceData & {
  duration: number
  endTime: number
  services: {
    name: string
    numberOfSpans: number
  }[]
  spans: ISpan[]
  startTime: number
  traceName: string
};

export type TraceData = {
  processes?: Record<string, Process>
  request_id: string
  x_request_id: string
  total_latency_ms: number
};

export enum EListItemType {
  events = 'Events',
  process = 'Process',
  stageTime = 'StageTime',
  tags = 'Tags',
}

export enum ETopoType {
  service = 'service',
  time = 'time',
}

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

export interface IDiffInfo {
  baseline: number
  comparison: number
  diff: number
  mark: 'added' | 'changed' | 'removed' | 'unchanged'
}

export interface IEventsItem {
  titleRight?: any
  list: {
    content: ITagContent[]
    header: {
      date: string
      duration: string
      name: string
    }
    isExpan: boolean
  }[]
}

export interface IInfo {
  list: IListItem[]
  title: string
  header: {
    others: {
      content: any
      label: string
      title: string
    }[]
    timeTag: string // 时间
    // 头部
    title: string // 标题
  }
}

export interface IListItem {
  [EListItemType.events]?: IEventsItem
  [EListItemType.process]?: IProcessItem
  [EListItemType.stageTime]?: IStageTimeItem
  [EListItemType.tags]?: ITagsItem
  isExpan: boolean
  title?: string
  type: EListItemType
}

export interface IProcessItem {
  title: string
  list: {
    content?: string
    label: string
    query_key: string
    query_value: any
  }[]
}

export interface IQueryParams {
  agg_method?: string
  app_code?: string
  bk_biz_id?: number
  data_type?: string
  diagram_types?: string[]
  diff_filter_labels?: any
  diff_profile_id?: string
  end: number
  filter_labels?: Record<string, string>
  global_query: boolean
  is_compared?: boolean
  offset?: number
  profile_id?: string
  sort?: string
  start: number
}

export interface IServiceSpanListItem {
  collapsed: boolean
  collapsed_span_num: number
  color: string
  display_name: string
  duration: number
  icon: string
  kind: number
  operation_name: string
  service: string
  span_id: string
  span_ids: string[]
  span_name: string
  start_time: number
}

export interface ISpanClassifyItem {
  app_code?: string
  color: string
  count: number
  filter_key: string
  filter_value: number | string
  icon: string
  name: string
  type: string
}

export interface ISpanDetail {
  origin_data: IOriginData
  trace_tree: {
    processes: { [key: string]: object }
    spans: {
      app_code: string
      attributes: any[]
      color: string
      duration: number
      error: boolean
      events: any[]
      flags: number
      icon: string
      id: string
      kind: number
      logs: any[]
      message: string
      operation: string
      processID: string
      references: {
        refType: string
        span_id: string
        trace_id: string
      }[]
      resource: any[]
      service: string
      span_id: string
      startTime: number
      tags: {
        key: string
        query_key: string
        query_value: string
        type: string
        value: string
      }[]
      trace_id: string
    }[]
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

export interface IStageTimeItem {
  // 阶段耗时
  active: string
  content: { [propName: string]: IStageTimeItemContent[] }
  list: {
    error: boolean
    errorMsg: string
    id: string
    label: string
  }[]
}

export interface IStageTimeItemContent {
  gapTime?: string
  type: 'gapTime' | 'useTime'
  useTime?: {
    gap: {
      type: 'toLeft' | 'toRight'
      value: string
    }
    tags: string[]
  }
}

export interface ITagContent {
  content?: string
  isFormat?: boolean
  label: string
  query_key: string
  query_value: any
  type: string
}

export interface ITagsItem { list: ITagContent[] }

export interface ITopoNode {
  bgColor?: string
  collapsed: boolean
  color: string
  diff_info?: Record<string, IDiffInfo>
  duration: number
  error: boolean | number
  icon: string
  id: string
  operation: string
  service: string
  spans: string[]
}

export interface ITopoRelation {
  source: string
  target: string
}

export interface ITraceData extends ITraceListItem {
  [key: string]: any
  ebpf_enabled?: boolean
  original_data: any[]
  span_classify: ISpanClassifyItem[]
  topo_nodes: ITopoNode[]
  topo_relation: ITopoRelation[]
  trace_tree?: ITraceTree
  streamline_service_topo?: {
    edges: any[]
    nodes: any[]
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

export interface OriginCrossAppSpanMap { [key: string]: ISpan[] }

interface IOriginData {
  elapsed_time: number
  end_time: number
  events: any[]
  kind: number
  links: any[]
  parent_span_id: string
  span_id: string
  span_name: string
  start_time: number
  time: string
  trace_id: string
  trace_state: string
  attributes: {
    key: string
    query_key: string
    query_value: number
    type: string
    value: number
  }
  resource: {
    key: string
    query_key: string
    query_value: string
    type: string
    value: string
  }
  status: {
    code: number
    message: string
  }
}

// 定义时间刻度类型
export interface ITimeTick {
  time: number
  percent: number
  label: string
  isLast?: boolean
}
