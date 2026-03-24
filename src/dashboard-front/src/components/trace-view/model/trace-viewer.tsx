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

import _memoize from 'lodash-es/memoize';
import type { ISpan } from '@/components/trace-view/typings';

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

/**
 * @description: 根据layer展示对应span的icon
 */
export const getSpanIcon = (span: ISpan) => {
  const { mcp_method, layer } = span;

  if (['mcp'].includes(layer)) {
    if (['tools/call'].includes(mcp_method)) {
      return 'tool';
    }
    return 'mcp-2';
  }

  return 'http';
};
