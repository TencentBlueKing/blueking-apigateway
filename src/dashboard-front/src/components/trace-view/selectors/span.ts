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

import { createSelector } from 'reselect';
import { getProcessServiceName } from './process';

// 类型定义
export interface ISpanReference {
  refType: string
  span_id: number | string
  trace_id?: number | string
}

export interface ISpanProcess {
  serviceName: string
  [key: string]: any
}

export interface ISpan {
  span_id: number | string
  operation: string
  duration?: number
  startTime?: number
  processID?: string | number
  references?: ISpanReference[]
  process?: ISpanProcess
  [key: string]: any
}

type FuzzyResult<T> = {
  original: T
  score?: number
};

const fuzzy = {
  filter<T>(searchText: string, list: T[], options: { extract: (item: T) => string }): FuzzyResult<T>[] {
    if (!searchText) {
      return list.map(item => ({ original: item }));
    }

    const lowerText = searchText.toLowerCase();

    return list
      .map((item) => {
        const content = options.extract(item).toLowerCase();
        let score = 0;
        let p = 0;

        for (let i = 0; i < content.length && p < lowerText.length; i++) {
          if (content[i] === lowerText[p]) {
            score += 1;
            p += 1;
          }
        }

        return p === lowerText.length
          ? {
            original: item,
            score,
          }
          : null;
      })
      .filter(item => item !== null)
      .sort((a: { score: number }, b: { score: number }) => (a?.score ?? 0) - (b?.score ?? 0));
  },
};

// 基础 ISpan 选择器
export const getSpanId = (span: ISpan): ISpan['span_id'] => span.span_id;
export const getSpanName = (span: ISpan): string => span.operation;
export const getSpanDuration = (span: ISpan): number => span?.latency ?? 0;
export const getSpanTimestamp = (span: ISpan): number => span.start_offset_ms ?? 0;
export const getSpanReferences = (span: ISpan): ISpanReference[] => span.references || [];

// 根据类型获取引用
export const getSpanReferenceByType = createSelector(
  (_: unknown, { span }: { span: ISpan }) => getSpanReferences(span),
  (_: unknown, { type }: { type: string }) => type,
  (references: any[], type: string) => references.find(ref => ref.refType === type),
);

// 获取父 ISpan ID
export const getSpanParentId = createSelector(
  (span: ISpan) => getSpanReferenceByType(undefined, {
    span,
    type: 'CHILD_OF',
  }),
  (childOfRef: { span_id: string | number }) => (childOfRef ? childOfRef.span_id : null),
);

// 获取 ISpan 关联的 Process
export const getSpanProcess = (span: ISpan): ISpanProcess => {
  if (!span.process) {
    throw new Error(`
      you must hydrate the spans with the processes, perhaps
      using hydrateSpansWithProcesses(), before accessing a span's process
    `);
  }
  return span.process;
};

// 获取服务名称
export const getSpanServiceName = createSelector(
  getSpanProcess,
  getProcessServiceName,
);

// 根据时间戳过滤 ISpan
export const filterSpansForTimestamps = createSelector(
  ({ spans }: { spans: ISpan[] }) => spans,
  ({ leftBound }: { leftBound: number }) => leftBound,
  ({ rightBound }: { rightBound: number }) => rightBound,
  (spans: any[], leftBound: number, rightBound: number) =>
    spans.filter((span: ISpan) => getSpanTimestamp(span) >= leftBound && getSpanTimestamp(span) <= rightBound),
);

// 根据文本模糊搜索过滤 ISpan
export const filterSpansForText = createSelector(
  ({ spans }: { spans: ISpan[] }) => spans,
  ({ text }: { text: string }) => text,
  (spans, text) =>
    fuzzy
      .filter(text, spans, { extract: (span: ISpan) => `${getSpanServiceName(span)} ${getSpanName(span)}` })
      .map(item => item.original),
);

// 文本过滤后的 ISpan 转为 ID 映射
const getTextFilteredSpansAsMap = createSelector(
  filterSpansForText,
  (matchingSpans: any[]): Record<string | number, ISpan> =>
    matchingSpans.reduce(
      (obj, span) => ({
        ...obj,
        [getSpanId(span)]: span,
      }),
      {} as Record<string | number, ISpan>,
    ),
);

// 高亮/淡化匹配的 ISpan
export const highlightSpansForTextFilter = createSelector(
  ({ spans }: { spans: ISpan[] }) => spans,
  getTextFilteredSpansAsMap,
  (spans: any[], textFilteredSpansMap: { [x: string]: any }) =>
    spans.map((span: ISpan) => ({
      ...span,
      muted: !textFilteredSpansMap[getSpanId(span)],
    })),
);
