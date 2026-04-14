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

import type { TNil } from './trace';

export enum ETraceViewType {
  TraceGraph = 'TraceGraph',
  TraceSpansView = 'TraceSpansView',
  TraceStatistics = 'TraceStatistics',
  TraceTimelineViewer = 'TraceTimelineViewer',
}

export interface IChildrenHiddenStore {
  childrenHiddenIds: Ref<any>
  onChange: (spanId: string) => void
}

export interface IFocusMatchesStore {
  findMatchesIDs: Ref<any>
  focusMatchesId: Ref<string>
  focusMatchesIdIndex: Ref<number>
}

export interface ISpanBarStore {
  current: Ref<[number, number]>
  onCurrentChange: (current: [number, number]) => void
}

export interface IViewRange { time: IViewRangeTime }

export interface IViewRangeStore {
  viewRange: Ref<IViewRange>
  onViewRangeChange: (viewRange: IViewRange) => void
}

export interface IViewRangeTime {
  current: [number, number]
  cursor?: number | TNil
  shiftEnd?: number
  shiftStart?: number
  reframe?: {
    anchor: number
    shift: number
  }
}

export type TUpdateViewRangeTimeFunction = (start: number, end: number, trackSrc?: string) => void;

export type ViewRangeTimeUpdate = ITimeCursorUpdate | ITimeReframeUpdate | ITimeShiftEndUpdate | ITimeShiftStartUpdate;

interface ITimeCursorUpdate { cursor: number | TNil }

interface ITimeReframeUpdate {
  reframe: {
    anchor: number
    shift: number
  }
}

interface ITimeShiftEndUpdate { shiftEnd: number }

interface ITimeShiftStartUpdate { shiftStart: number }
