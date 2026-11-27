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

import type {
  ISpan,
  ITraceListItem,
  ITraceTree,
  Process,
} from '@/types/trace';

export type CrossRelation = {
  app_code: string
  bk_app_code: number
  bk_biz_id: number
  bk_biz_name: string
  permission: boolean
  trace_id: string
};

export type Link = {
  text: string
  url: string
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
