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

import type { ISpan, KeyValuePair, TNil } from '../typings';

export default function filterSpans(textFilter: string, spans: ISpan[] | TNil) {
  if (!spans) {
    return null;
  }

  // if a span field includes at least one filter in includeFilters, the span is a match
  const includeFilters: string[] = [];

  // values with keys that include text in any one of the excludeKeys will be ignored
  const excludeKeys: string[] = [];

  // split textFilter by whitespace, remove empty strings, and extract includeFilters and excludeKeys
  textFilter
    .split(/\s+/)
    .filter(Boolean)
    .forEach((w) => {
      if (w[0] === '-') {
        excludeKeys.push(w.substr(1).toLowerCase());
      }
      else {
        includeFilters.push(w.toLowerCase());
      }
    });

  const isTextInFilters = (filters: Array<string>, text: string) =>
    filters.some(filter => text.toLowerCase().includes(filter));

  const isTextInKeyValues = (kvs: Array<KeyValuePair>) =>
    kvs
      ? kvs.some((kv) => {
        // ignore checking key and value for a match if key is in excludeKeys
        if (isTextInFilters(excludeKeys, kv.key)) {
          return false;
        }
        // match if key or value matches an item in includeFilters
        return (
          isTextInFilters(includeFilters, kv.key)
          || isTextInFilters(includeFilters, kv.value.toString())
        );
      })
      : false;

  const isSpanAMatch = (span: ISpan) =>
    isTextInFilters(includeFilters, span.operation)
    || isTextInFilters(includeFilters, span.process.serviceName)
    || (Array.isArray(span?.tags) && isTextInKeyValues(span.tags))
    || (span?.logs && Array.isArray(span.logs) && span.logs.some(log => isTextInKeyValues(log.fields)))
    || isTextInKeyValues(span.process.tags)
    || includeFilters.some(filter => filter.replace(/^0*/, '') === span.span_id.replace(/^0*/, ''));

  // declare as const because need to disambiguate the type
  const rv: Set<string> = new Set(spans.filter(isSpanAMatch).map((span: ISpan) => span.span_id));
  return rv;
}
