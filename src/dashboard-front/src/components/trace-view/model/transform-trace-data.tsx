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

import type { ISpan, KeyValuePair } from '@/components/trace-view/typings';
import type { ITraceLog } from '@/services/source/observability';
import { DEFAULT_TRACE_DATA } from '@/components/trace-view/constants/trace';
import { getSpanBgColor, getTraceName } from '@/components/trace-view/model/trace-viewer';
import { getConfigValue } from '@/components/trace-view/utils/config/get-config';

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

// exported for tests
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

    // 标签处理
    const tagsInfo = deduplicateTags(span.tags);
    span.tags = orderTags(tagsInfo.tags, getConfigValue('topTagPrefixes'));
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
