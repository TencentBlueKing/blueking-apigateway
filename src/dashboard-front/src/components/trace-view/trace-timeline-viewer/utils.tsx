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

import type { ISpan } from '@/services/source/observability';

export type ViewedBoundsFunctionType = (start: number, end: number) => {
  start: number
  end: number
};

/**
 * Given a range (`min`, `max`) and factoring in a zoom (`viewStart`, `viewEnd`)
 * a function is created that will find the position of a sub-range (`start`, `end`).
 * The calling the generated method will return the result as a `{ start, end }`
 * object with values ranging in [0, 1].
 * @returns {(number, number) => Object} Created view bounds function
 */
export function createViewedBoundsFunc(viewRange: {
  max: number
  min: number
  viewEnd: number
  viewStart: number
}): (start: number, end: number) => object {
  const { min, max, viewStart, viewEnd } = viewRange;
  const duration = max - min;
  const viewMin = min + viewStart * duration;
  const viewMax = max - (1 - viewEnd) * duration;
  const viewWindow = viewMax - viewMin;

  /**
   * View bounds function
   * @param  {number} start     The start of the sub-range.
   * @param  {number} end       The end of the sub-range.
   * @return {Object}           The resultant range.
   */
  return (start: number, end: number): object => ({
    start: (start - viewMin) / viewWindow,
    end: (end - viewMin) / viewWindow,
  });
}

/**
 * Returns `true` if the `span` has a tag matching `key` = `value`.
 *
 * @param  {string} key   The tag key to match on.
 * @param  {any}    value The tag value to match.
 * @param  {{tags}} span  An object with a `tags` property of { key, value }
 *                        items.
 * @return {boolean}      True if a match was found.
 */
export function spanHasTag(key: string, value: any, span: ISpan): boolean {
  if (!Array.isArray(span.tags) || !span.tags.length) {
    return false;
  }
  return span.tags.some(tag => tag.key === key && tag.value === value);
}

const isErrorBool = spanHasTag.bind(null, 'error', true);
const isErrorStr = spanHasTag.bind(null, 'error', 'true');
export const isErrorSpan = (span: ISpan) => isErrorBool(span) || isErrorStr(span);

/**
 * Expects the first span to be the parent span.
 */
/**
 * 找到根节点下 最深的 RPC 子 span（兼容 mcp_0、mcp_0_1）
 * 你的数据里：一定能找到 mcp_0_1（如果有），否则找到 mcp_0
 */
export function findServerChildSpan(spans: ISpan[]) {
  if (!spans || spans.length === 0) {
    return null;
  }

  // 第一个 span 就是根节点
  const rootSpan = spans[0];
  const rootId = rootSpan.span_id;

  // 快速查询 span
  const spanMap = new Map(spans.map(s => [s.span_id, s]));

  // 遍历所有 span
  for (const span of spans) {
    // 向上溯源：只要是 rootId 的后代（不管 depth 多少层）
    let current: ISpan | undefined = span;
    let foundRoot = false;

    while (current) {
      if (current.parent_span_id === rootId) {
        foundRoot = true;
        break;
      }
      current = spanMap.get(current.parent_span_id!);
    }

    // 找到第一个符合条件的，直接返回！
    if (foundRoot) {
      return span;
    }
  }

  return null;
}

/**
 * Returns `true` if at least one of the descendants of the `parentSpanIndex`
 * span contains an error tag.
 *
 * @param      {ISpan[]}   spans            The spans for a trace - should be
 *                                         sorted with children following parents.
 * @param      {number}   parentSpanIndex  The index of the parent span - only
 *                                         subsequent spans with depth less than
 *                                         the parent span will be checked.
 * @return     {boolean}  Returns `true` if a descendant contains an error tag.
 */
export function spanContainsErredSpan(spans: ISpan[], parentSpanIndex: number): boolean {
  const { depth } = spans[parentSpanIndex];
  let i = parentSpanIndex + 1;
  for (; i < spans.length && spans[i].depth > depth; i++) {
    if (isErrorSpan(spans[i])) {
      return true;
    }
  }
  return false;
}

export { formatDuration } from '../utils/date';
