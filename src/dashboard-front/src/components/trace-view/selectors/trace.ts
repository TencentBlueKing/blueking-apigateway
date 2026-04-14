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

import { createSelector, createStructuredSelector } from 'reselect';
import { ONE_SECOND, formatMillisecondTime, formatSecondTime } from '../utils/date';
import { numberSortComparator } from '../utils/sort';
import TreeNode from '../utils/tree-node';
import { getProcessServiceName } from './process';
import {
  type ISpan,
  getSpanDuration,
  getSpanId,
  getSpanName,
  getSpanServiceName,
  getSpanTimestamp,
} from './span';
import type { ISpanReference } from '../typings';
import type { ITraceLog } from '@/services/source/observability';

export const getTraceId = (trace: { trace_id: string }) => trace.trace_id;

export const getTraceSpans = (trace: { spans: Record<string, any> }) => trace.spans;

const getTraceProcesses = (trace: { processes: Record<string, any> }) => trace.processes;

const getSpanWithProcess = createSelector(
  state => state.span,
  state => state.processes,
  (span, processes) => ({
    ...span,
    process: processes?.span?.processID,
  }),
);

export const getTraceSpansAsMap = createSelector(getTraceSpans, spans =>
  spans.reduce((map: { set: (arg0: string | number, arg1: any) => any },
    span: ISpan) => map.set(getSpanId(span), span), new Map()),
);

export const TREE_ROOT_ID = '__root__';

/**
 * 构建一个由{ value: span_id, children }项组成的树结构，这些项源自
 * span.references```信息。该树表示父级/子级的分组关系
 * 子关系。最顶层的节点具有名词性
 * .value === TREE_ROOT_ID```  这是因为在根跨度（即主追踪）中已处理
 * 跨度*并不总是包含在追踪数据中。因此，可能会存在
 * 多个顶级跨度，根节点作为它们的共同父节点。
 *
 * 构建树后，子节点按`span.start_offset_ms`排序。
 *
 * @param  {Trace} trace 追踪并构建了spanIDs树
 * @return {TreeNode}    从关系中导出的spanID树在轨迹中的跨度之间
 */
export const getTraceSpanIdsAsTree = (trace: ITraceLog): TreeNode => {
  const nodesById = new Map<string | number, TreeNode>();
  const spansById = new Map<string | number, ISpan>();

  // 递归注册节点，不打平！
  const registerNode = (span: ISpan) => {
    if (!span || nodesById.has(span.span_id)) return;
    nodesById.set(span.span_id, new TreeNode(span.span_id));
    spansById.set(span.span_id, span);
    span.children?.forEach((child: ISpan) => registerNode(child));
  };

  // 只注册顶层 span，内部自动递归
  trace.spans.forEach(span => registerNode(span));

  const root = new TreeNode(TREE_ROOT_ID);

  // 递归构建树：完全保留嵌套结构
  const buildFromChildren = (parentSpan: ISpan, parentNode: TreeNode) => {
    parentSpan.children?.forEach((childSpan: ISpan) => {
      const childNode = nodesById.get(childSpan.span_id);
      if (childNode) {
        parentNode.children.push(childNode);
        buildFromChildren(childSpan, childNode);
      }
    });
  };

  // 构建顶层
  trace.spans.forEach((topSpan) => {
    const topNode = nodesById.get(topSpan.span_id);
    if (topNode) {
      root.children.push(topNode);
      buildFromChildren(topSpan, topNode);
    }
  });

  // 排序函数
  const comparator = (nodeA: TreeNode, nodeB: TreeNode) => {
    const a = spansById.get(nodeA.value as string | number)!;
    const b = spansById.get(nodeB.value as string | number)!;
    return +(a.start_offset_ms > b.start_offset_ms) || +(a.start_offset_ms === b.start_offset_ms) - 1;
  };

  // 递归整棵树排序
  const sortTree = (node: TreeNode) => {
    if (node.children.length > 1) {
      node.children.sort(comparator);
    }
    node.children.forEach(child => sortTree(child));
  };

  sortTree(root);
  return root;
};

// 将流程作为对象附加到每个跨度。
export const hydrateSpansWithProcesses = (trace: any) => {
  const spans = getTraceSpans(trace);
  const processes = getTraceProcesses(trace);

  return {
    ...trace,
    spans: spans.map((span: any) => getSpanWithProcess({
      span,
      processes,
    })),
  };
};

export const getTraceSpanCount = createSelector(getTraceSpans, spans => spans.length);

export const getTraceTimestamp = createSelector(getTraceSpans, spans =>
  spans.reduce(
    (prevTimestamp: number, span: ISpan) =>
      (prevTimestamp ? Math.min(prevTimestamp, getSpanTimestamp(span)) : getSpanTimestamp(span)),
    null,
  ),
);

export const getTraceDuration = createSelector(getTraceSpans, getTraceTimestamp, (spans, timestamp) =>
  spans.reduce(
    (prevDuration: number, span: ISpan) =>
      prevDuration
        ? Math.max(getSpanTimestamp(span) - timestamp + getSpanDuration(span), prevDuration)
        : getSpanDuration(span),
    null,
  ),
);

export const getTraceEndTimestamp = createSelector(
  getTraceTimestamp,
  getTraceDuration,
  (timestamp, duration) => timestamp + duration,
);

export const getParentSpan = createSelector(
  getTraceSpanIdsAsTree,
  getTraceSpansAsMap,
  (tree, spanMap) =>
    tree.children
      .map(node => spanMap.get(node.value))
      .sort((spanA, spanB) => numberSortComparator(getSpanTimestamp(spanA), getSpanTimestamp(spanB)))[0],
);

export const getTraceDepth = createSelector(getTraceSpanIdsAsTree, spanTree => spanTree.depth - 1);

export const getSpanDepthForTrace = createSelector(
  createSelector(state => state.trace, getTraceSpanIdsAsTree),
  createSelector(state => state.span, getSpanId),
  (node: any, span_id) => node.getPath(span_id).length - 1,
);

export const getTraceServices = createSelector(getTraceProcesses, processes =>
  Object.keys(processes).reduce(
    (services, processID) => services.add(getProcessServiceName(processes[processID])),
    new Set(),
  ),
);

export const getTraceServiceCount = createSelector(getTraceServices, services => services.size);

// establish constants to determine how math should be handled
// for nanosecond-to-millisecond conversions.
export const DURATION_FORMATTERS: Record<string, any> = {
  ms: formatMillisecondTime,
  s: formatSecondTime,
};

const getDurationFormatterForTrace = createSelector(getTraceDuration, totalDuration =>
  totalDuration >= ONE_SECOND ? DURATION_FORMATTERS.s : DURATION_FORMATTERS.ms,
);

export const formatDurationForUnit = createSelector(
  ({ duration }) => duration || 0,
  ({ unit }) => DURATION_FORMATTERS[unit],
  (duration: number, formatter?: (n: number) => string) => {
    return typeof formatter === 'function' ? formatter(duration) : duration;
  },
);

export const formatDurationForTrace = createSelector(
  ({ duration }: { duration: number }) => duration,
  createSelector(({ trace }) => trace, getDurationFormatterForTrace),
  (duration, formatter) => formatter(duration),
);

export const getSortedSpans = createSelector(
  ({ trace }) => trace,
  ({ spans }) => spans,
  ({ sort }) => sort,

  (trace, spans, { dir, comparator, selector }) =>
    [...spans].sort((spanA, spanB) => dir * comparator(selector(spanA, trace), selector(spanB, trace))),
);

const getTraceSpansByHierarchyPosition = createSelector(getTraceSpanIdsAsTree, (tree) => {
  const hierarchyPositionMap = new Map();
  let i = 0;

  tree.walk(span_id => hierarchyPositionMap.set(span_id, i++));
  return hierarchyPositionMap;
});

export const getTreeSizeForTraceSpan = createSelector(
  createSelector(state => state.trace, getTraceSpanIdsAsTree),
  createSelector(state => state.span, getSpanId),
  (tree, span_id) => {
    const node = tree.find(span_id);
    if (!node) {
      return -1;
    }
    return node.size - 1;
  },
);

export const getSpanHierarchySortPositionForTrace = createSelector(
  createSelector(({ trace }) => trace, getTraceSpansByHierarchyPosition),
  ({ span }) => span,
  (hierarchyPositionMap: { get: (arg0: string | number) => any }, span: ISpan) =>
    hierarchyPositionMap.get(getSpanId(span)),
);

export const getTraceName = createSelector(
  createSelector(
    createSelector(hydrateSpansWithProcesses, getParentSpan),
    createStructuredSelector({
      name: getSpanName,
      serviceName: getSpanServiceName,
    }),
  ),
  ({ name, serviceName }) => `${serviceName}: ${name}`,
);

export const omitCollapsedSpans = createSelector(
  ({ spans = [] }) => spans,
  createSelector(({ trace }) => trace, getTraceSpanIdsAsTree),
  ({ collapsed }) => collapsed,
  (spans = [], tree, collapse) => {
    const hiddenSpanIds = collapse.reduce((result: { add: (arg0: any) => any }, collapsedSpanId: any) => {
      tree.find(collapsedSpanId).walk((id: any) => id !== collapsedSpanId && result.add(id));
      return result;
    }, new Set());

    return hiddenSpanIds.size > 0 ? spans.filter((span: ISpan) => !hiddenSpanIds.has(getSpanId(span))) : spans;
  },
);

export const DEFAULT_TICK_INTERVAL = 4;
export const DEFAULT_TICK_WIDTH = 3;
export const getTicksForTrace = createSelector(
  ({ trace }) => trace,
  ({ interval = DEFAULT_TICK_INTERVAL }) => interval,
  ({ width = DEFAULT_TICK_WIDTH }) => width,
  (
    trace,
    interval,
    width,
    // timestamps will be spaced over the interval, starting from the initial timestamp
  ) =>
    [...Array(interval + 1).keys()].map(num => ({
      timestamp: getTraceTimestamp(trace) + getTraceDuration(trace) * (num / interval),
      width,
    })),
);

// TODO: delete this when the backend can ensure uniqueness
/* istanbul ignore next */
export const enforceUniqueSpanIds = createSelector(
  /* istanbul ignore next */ trace => trace,
  getTraceSpans,
  /* istanbul ignore next */ (trace, spans) => {
    const map = new Map();

    return {
      ...trace,
      spans: spans.reduce((result: any[], span: ISpan) => {
        const span_id = map.has(getSpanId(span)) ? `${getSpanId(span)}_${map.get(getSpanId(span))}` : getSpanId(span);
        const updatedSpan = {
          ...span,
          span_id,
        };

        if (span_id !== getSpanId(span)) {
          console.warn('duplicate span_id in trace replaced', getSpanId(span), 'new:', span_id);
        }

        // set the presence of the span in the map or increment the number
        map.set(getSpanId(span), (map.get(getSpanId(span)) || 0) + 1);

        return result.concat([updatedSpan]);
      }, []),
    };
  },
);

// TODO: delete this when the backend can ensure uniqueness
export const dropEmptystart_offset_msSpans = createSelector(
  /* istanbul ignore next */ trace => trace,
  getTraceSpans,
  /* istanbul ignore next */ (trace, spans) => ({
    ...trace,
    spans: spans.filter((span: ISpan) => !!getSpanTimestamp(span)),
  }),
);
