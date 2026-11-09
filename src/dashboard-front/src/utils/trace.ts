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

// 调用链瀑布图的数据处理：接口数据转换为瀑布树、折叠分组、耗时格式化
// 由 useTrace Store 与 components/mcp/trace-view 共用，不依赖组件内部实现

import _memoize from 'lodash-es/memoize';
import { DEFAULT_TRACE_DATA } from '@/constants/trace';
import type { ITraceLog } from '@/types/observability';
import type { ISpan, KeyValuePair } from '@/types/trace';

type IToggleStatus = 'collpase' | 'expand';

export function _getTraceNameImpl(spans: ISpan[]) {
  let candidateSpan: ISpan | undefined;
  const allIDs: Set<string> = new Set(spans.map(({ span_id }) => span_id));

  for (let i = 0; i < spans.length; i++) {
    const hasInternalRef = !!spans[i].references?.some(
      ({ trace_id, span_id }: {
        trace_id: string
        span_id: string
      }) =>
        trace_id === spans[i].trace_id && allIDs.has(span_id),
    );
    if (hasInternalRef) {
      continue;
    }

    if (!candidateSpan) {
      candidateSpan = spans[i];
      continue;
    }

    const thisRefLength = spans[i] && Array.isArray(spans[i].references) ? spans[i].references!.length : 0;
    const candidateRefLength = (candidateSpan?.references && candidateSpan.references.length) || 0;

    if (
      thisRefLength < candidateRefLength
      || (thisRefLength === candidateRefLength && (spans[i].startTime ?? 0) < (candidateSpan.startTime ?? 0))
    ) {
      candidateSpan = spans[i];
    }
  }

  return candidateSpan ? `${candidateSpan.service_name}: ${candidateSpan.operation}` : '';
}

export const getTraceName = _memoize(_getTraceNameImpl, (spans: ISpan[]) => {
  if (!spans.length) {
    return 0;
  }
  return spans?.[0]?.trace_id ?? '';
});

/**
 * @description: 根据layer展示对应span的borderColor
 * @param detail 需要展示的span数据
 */
export const getSpanBgColor = (span: ISpan) => {
  const { mcp_method, layer } = span;

  if (['mcp'].includes(layer)) {
    if (['tools/call'].includes(mcp_method)) {
      return '#92d4f1';
    }

    return '#f5c78e';
  }

  return '#5ab8a8';
};

export function deduplicateTags(spanTags: KeyValuePair[]) {
  const warningsHash: Map<string, string> = new Map<string, string>();
  const tags: KeyValuePair[] = spanTags.reduce<KeyValuePair[]>((uniqueTags, tag) => {
    if (!uniqueTags.some(t => t.key === tag.key && t.value === tag.value)) {
      uniqueTags.push(tag);
    }
    else {
      warningsHash.set(`${tag.key}:${tag.value}`, `Duplicate tag "${tag.key}:${tag.value}"`);
    }
    return uniqueTags;
  }, []);
  const warnings = Array.from(warningsHash.values());
  return {
    tags,
    warnings,
  };
}

export function orderTags(spanTags: KeyValuePair[], topPrefixes?: string[]) {
  const orderedTags: KeyValuePair[] = spanTags.slice();
  const tp = (topPrefixes || []).map((p: string) => p.toLowerCase());

  orderedTags.sort((a, b) => {
    const aKey = a.key.toLowerCase();
    const bKey = b.key.toLowerCase();

    for (let i = 0; i < tp.length; i++) {
      const p = tp[i];
      if (aKey.startsWith(p) && !bKey.startsWith(p)) {
        return -1;
      }
      if (!aKey.startsWith(p) && bKey.startsWith(p)) {
        return 1;
      }
    }

    if (aKey > bKey) {
      return 1;
    }
    if (aKey < bKey) {
      return -1;
    }
    return 0;
  });

  return orderedTags;
}

/**
  * 响应数据转换为瀑布图需要参数格式
*/
export function transformTraceTree(data: ITraceLog): ITraceLog {
  const {
    request_id,
    x_request_id,
    total_latency_ms,
    logList = [],
    upstream_gateway_log,
    downstream_gateway_log,
  } = data;

  if (!request_id || !data.spans?.length) {
    return DEFAULT_TRACE_DATA;
  }

  let traceStartTime = Number.MAX_SAFE_INTEGER;
  let traceEndTime = 0;
  const allSpans: ISpan[] = [];
  const svcCounts: Record<string, number> = {};

  const stack: Array<{
    span: ISpan
    depth: number
  }> = [];

  // 所有顶级 span 统一 depth:0（挂载到虚拟 __root__ 下）
  for (let i = data.spans.length - 1; i >= 0; i--) {
    stack.push({
      span: data.spans[i],
      depth: 0,
    });
  }

  while (stack.length) {
    const { span, depth } = stack.pop()!;

    // 赋值层级
    span.depth = depth;
    span.hasChildren = !!(span.children?.length);

    // 基础默认值
    span.warnings ||= [];
    span.tags ||= [];
    span.references ||= [];

    // 时间计算
    const startMs = span.start_offset_ms ?? 0;
    const latencyMs = span.latency_ms ?? 0;
    const endMs = startMs + latencyMs;
    traceStartTime = Math.min(traceStartTime, startMs);
    traceEndTime = Math.max(traceEndTime, endMs);

    // 标签处理（按 key 排序，不设置置顶前缀）
    const tagsInfo = deduplicateTags(span.tags);
    span.tags = orderTags(tagsInfo.tags);
    span.warnings = span.warnings.concat(tagsInfo.warnings);
    span.color = getSpanBgColor(span);

    // 收集 & 统计
    allSpans.push(span);
    if (span.service) {
      svcCounts[span.service] = (svcCounts[span.service] || 0) + 1;
    }

    // 子节点入栈，depth +1（倒序保证顺序）
    if (span.children?.length) {
      for (let i = span.children.length - 1; i >= 0; i--) {
        stack.push({
          span: span.children[i],
          depth: depth + 1,
        });
      }
    }
  }

  // 统一赋值相对时间
  allSpans.forEach((span) => {
    span.relativeStartTime = (span.start_offset_ms ?? 0) - traceStartTime;
  });

  return {
    services: Object.entries(svcCounts).map(([name, numberOfSpans]) => ({
      name,
      numberOfSpans,
    })),
    spans: allSpans,
    request_id,
    x_request_id,
    total_latency_ms,
    traceName: getTraceName(allSpans),
    duration: traceEndTime - traceStartTime,
    startTime: traceStartTime,
    endTime: traceEndTime,
    logList,
    upstream_gateway_log,
    downstream_gateway_log,
  };
}

/** 基于 traceTree 进行折叠分组
 * 当前节点为折叠的聚合节点 parent_span_id !== span_id
 */
export const handleTraceTreeGroup = (spans: ISpan[]) => {
  const list: ISpan[] = [];
  spans.forEach((span) => {
    if (span.parent_span_id !== span.span_id || span.is_expand) {
      list.push(span);
    }
  });

  return list;
};

/** 切换 traceTree 分组的折叠状态 */
export const handleToggleCollapse = (spans: ISpan[], groupID: string, status: IToggleStatus) => {
  let list = [];
  // 点击切换折叠状态时 只需要更改 is_expand 的值
  list = spans.map(span => ({
    ...span,
    is_expand: span.group_info?.id === groupID ? status === 'expand' : span.is_expand,
  }));

  return list;
};

/**
 * 耗时格式化，直接以 ms 输出，不做单位换算
 *
 * @param {number} duration 耗时（ms）
 * @param {string} split 分隔符
 * @param {number} precision 精度
 * @return {string} formatted duration
 */
export function formatDuration(duration: number, split: string = '', precision?: number | null): string {
  const decimalLen = (String(duration).split('.')[1] || '').length;
  if (precision && duration > 0) {
    return decimalLen > precision ? `${duration.toFixed(precision)}${split}ms` : `${duration}${split}ms`;
  }

  // 直接以 ms 输出，完全不换算、不四舍五入
  return `${duration}${split}ms`;
}
