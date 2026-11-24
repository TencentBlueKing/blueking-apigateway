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

import { describe, expect, it } from 'vitest';
import { DEFAULT_TRACE_DATA } from '@/constants/trace';
import type { ITraceLog } from '@/types/observability';
import type { ISpan, KeyValuePair } from '@/types/trace';
import {
  _getTraceNameImpl,
  deduplicateTags,
  formatDuration,
  getSpanBgColor,
  getTraceName,
  handleToggleCollapse,
  handleTraceTreeGroup,
  orderTags,
  transformTraceTree,
} from '@/utils/trace';

const createSpan = (overrides: Partial<ISpan> = {}): ISpan => ({
  span_id: 'span-1',
  parent_span_id: '',
  trace_id: 'trace-1',
  service: 'mcp-proxy',
  service_name: 'mcp-proxy',
  operation: 'tools/call',
  layer: 'mcp',
  mcp_method: 'tools/call',
  start_offset_ms: 10,
  latency_ms: 20,
  ...overrides,
} as ISpan);

describe('utils/trace', () => {
  describe('_getTraceNameImpl & getTraceName', () => {
    it('选择无内部引用且引用最少、开始时间最早的根 span 作为链路名称', () => {
      const rootLate = createSpan({
        span_id: 'root-late',
        service_name: 'svc-b',
        operation: 'op-late',
        startTime: 200,
        references: [],
      });
      const rootEarly = createSpan({
        span_id: 'root-early',
        service_name: 'svc-a',
        operation: 'op-early',
        startTime: 100,
        references: [],
      });
      const child = createSpan({
        span_id: 'child',
        service_name: 'svc-c',
        operation: 'op-child',
        startTime: 50,
        references: [{
          trace_id: 'trace-1',
          span_id: 'root-early',
        }] as any,
      });

      expect(_getTraceNameImpl([child, rootLate, rootEarly])).toBe('svc-a: op-early');
      expect(_getTraceNameImpl([])).toBe('');
      expect(getTraceName([])).toBe('');
    });
  });

  describe('getSpanBgColor', () => {
    it('根据 layer 与 mcp_method 返回对应背景色', () => {
      expect(getSpanBgColor(createSpan({
        layer: 'mcp',
        mcp_method: 'tools/call',
      }))).toBe('#92d4f1');
      expect(getSpanBgColor(createSpan({
        layer: 'mcp',
        mcp_method: 'tools/list',
      }))).toBe('#f5c78e');
      expect(getSpanBgColor(createSpan({
        layer: 'gateway',
        mcp_method: 'tools/call',
      }))).toBe('#5ab8a8');
    });
  });

  describe('deduplicateTags & orderTags', () => {
    it('去除重复 tag 并生成对应 warning 提示', () => {
      const result = deduplicateTags([
        {
          key: 'http.method',
          value: 'GET',
        },
        {
          key: 'http.status',
          value: 200,
        },
        {
          key: 'http.method',
          value: 'GET',
        },
      ]);

      expect(result.tags).toEqual([
        {
          key: 'http.method',
          value: 'GET',
        },
        {
          key: 'http.status',
          value: 200,
        },
      ]);
      expect(result.warnings).toEqual(['Duplicate tag "http.method:GET"']);
    });

    it('支持按置顶前缀优先、其余按键名不区分大小写升序排序，且不修改原数组', () => {
      const input = [
        {
          key: 'zeta',
          value: 1,
        },
        {
          key: 'http.url',
          value: '/api',
        },
        {
          key: 'alpha',
          value: 2,
        },
        {
          key: 'error.kind',
          value: 'timeout',
        },
      ];
      const sorted = orderTags(input, ['error', 'http']);

      expect(sorted.map(item => item.key)).toEqual(['error.kind', 'http.url', 'alpha', 'zeta']);
      expect(input.map(item => item.key)).toEqual(['zeta', 'http.url', 'alpha', 'error.kind']);
    });
  });

  describe('transformTraceTree', () => {
    it('缺少 request_id 或 spans 为空时返回默认空链路数据', () => {
      expect(transformTraceTree({
        request_id: '',
        spans: [],
      } as unknown as ITraceLog)).toBe(DEFAULT_TRACE_DATA);
      expect(transformTraceTree({
        request_id: 'req-1',
        spans: [],
      } as unknown as ITraceLog)).toBe(DEFAULT_TRACE_DATA);
    });

    it('展平嵌套树并计算 depth、相对起点、服务计数、颜色、去重排序标签', () => {
      const childSpan = createSpan({
        span_id: 'child-1',
        parent_span_id: 'root-1',
        service: 'upstream',
        service_name: 'upstream',
        operation: 'GET /users',
        layer: 'gateway',
        start_offset_ms: 25,
        latency_ms: 40,
        tags: [
          {
            key: 'b',
            value: 1,
          },
          {
            key: 'a',
            value: 2,
          },
          {
            key: 'b',
            value: 1,
          },
        ],
      });
      const rootSpan = createSpan({
        span_id: 'root-1',
        service: 'mcp-proxy',
        service_name: 'mcp-proxy',
        operation: 'tools/call',
        layer: 'mcp',
        mcp_method: 'tools/call',
        start_offset_ms: 10,
        latency_ms: 60,
        children: [childSpan],
      });

      const tree = transformTraceTree({
        request_id: 'req-100',
        x_request_id: 'x-req-100',
        total_latency_ms: 70,
        spans: [rootSpan],
      } as unknown as ITraceLog);

      expect(tree.request_id).toBe('req-100');
      expect(tree.startTime).toBe(10);
      expect(tree.endTime).toBe(70);
      expect(tree.duration).toBe(60);
      expect(tree.spans).toHaveLength(2);
      expect(tree.spans[0].depth).toBe(0);
      expect(tree.spans[0].hasChildren).toBe(true);
      expect(tree.spans[0].relativeStartTime).toBe(0);
      expect(tree.spans[0].color).toBe('#92d4f1');

      expect(tree.spans[1].depth).toBe(1);
      expect(tree.spans[1].hasChildren).toBe(false);
      expect(tree.spans[1].relativeStartTime).toBe(15);
      expect(tree.spans[1].color).toBe('#5ab8a8');
      expect(tree.spans[1].tags.map((tag: KeyValuePair) => tag.key)).toEqual(['a', 'b']);
      expect(tree.spans[1].warnings).toEqual(['Duplicate tag "b:1"']);

      expect(tree.services).toEqual([
        {
          name: 'mcp-proxy',
          numberOfSpans: 1,
        },
        {
          name: 'upstream',
          numberOfSpans: 1,
        },
      ]);
    });
  });

  describe('handleTraceTreeGroup & handleToggleCollapse', () => {
    it('按聚合节点展开状态过滤，并能独立切换指定分组的折叠状态', () => {
      const spans = [
        createSpan({
          span_id: 's1',
          parent_span_id: 'root',
          group_info: { id: 'g1' } as any,
          is_expand: false,
        }),
        createSpan({
          span_id: 's2',
          parent_span_id: 's2',
          group_info: { id: 'g1' } as any,
          is_expand: false,
        }),
        createSpan({
          span_id: 's3',
          parent_span_id: 's3',
          group_info: { id: 'g2' } as any,
          is_expand: true,
        }),
      ];

      expect(handleTraceTreeGroup(spans).map(s => s.span_id)).toEqual(['s1', 's3']);

      const expanded = handleToggleCollapse(spans, 'g1', 'expand');
      expect(handleTraceTreeGroup(expanded).map(s => s.span_id)).toEqual(['s1', 's2', 's3']);

      const collapsed = handleToggleCollapse(expanded, 'g2', 'collpase');
      expect(handleTraceTreeGroup(collapsed).map(s => s.span_id)).toEqual(['s1', 's2']);
    });
  });

  describe('formatDuration', () => {
    it('按指定分隔符与精度格式化毫秒耗时，不做单位换算', () => {
      expect(formatDuration(0)).toBe('0ms');
      expect(formatDuration(1500)).toBe('1500ms');
      expect(formatDuration(12.3456, ' ', 2)).toBe('12.35 ms');
      expect(formatDuration(12.3, ' ', 2)).toBe('12.3 ms');
      expect(formatDuration(0, ' ', 2)).toBe('0 ms');
    });
  });
});
