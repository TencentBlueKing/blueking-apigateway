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

import { createPinia, setActivePinia } from 'pinia';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import type { ITraceLog } from '@/types/observability';

const { getFeatureFlagsMock } = vi.hoisted(() => ({ getFeatureFlagsMock: vi.fn() }));

vi.mock('@/services/source/platform/setting', () => ({ getFeatureFlags: getFeatureFlagsMock }));
vi.mock('@/services/source/gateway/stage', () => ({
  getStageDetail: vi.fn(),
  getStageList: vi.fn(),
}));

import { useFeatureFlag } from '@/stores/useFeatureFlag';
import { useStage } from '@/stores/useStage';
import { useTrace } from '@/stores/useTrace';

describe('stores/useFeatureFlag', () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    getFeatureFlagsMock.mockReset();
  });

  it('正确拉取功能开关并通过 getters 暴露多租户、AI、路由冲突检测与通知栏状态', async () => {
    const store = useFeatureFlag();
    expect(store.isTenantMode).toBe(false);
    expect(store.isEnableDisplayName).toBe(false);
    expect(store.isAIEnabled).toBe(false);
    expect(store.isEnabledNotice).toBe(false);
    expect(store.isEnablePathConflictCheck).toBe(false);

    getFeatureFlagsMock.mockResolvedValueOnce({
      ...store.flags,
      ENABLE_MULTI_TENANT_MODE: true,
      ENABLE_DISPLAY_NAME_RENDER: true,
      ENABLE_AI_COMPLETION: true,
      ENABLE_RESOURCE_PATH_CONFLICT_CHECK: true,
    });

    await store.fetchFlags();
    expect(getFeatureFlagsMock).toHaveBeenCalledWith({
      limit: 10000,
      offset: 0,
    });
    expect(store.isTenantMode).toBe(true);
    expect(store.isEnableDisplayName).toBe(true);
    expect(store.isAIEnabled).toBe(true);
    expect(store.isEnablePathConflictCheck).toBe(true);

    store.setNoticeAlert(true);
    expect(store.isEnabledNotice).toBe(true);
  });
});

describe('stores/useStage', () => {
  beforeEach(() => {
    setActivePinia(createPinia());
  });

  it('正确维护环境列表、默认环境与发布状态字段', () => {
    const store = useStage();
    expect(store.defaultStage).toEqual({});

    const stages = [
      {
        id: 1,
        name: 'prod',
      },
      {
        id: 2,
        name: 'test',
      },
    ];
    store.setStageList(stages);
    store.setNotUpdatedStages([stages[1]]);
    store.setStageMainLoading(true);
    store.setExist2(true);
    store.setDoing(true);

    expect(store.defaultStage).toEqual(stages[0]);
    expect(store.getNotUpdatedStages).toEqual([stages[1]]);
    expect(store.realStageMainLoading).toBe(true);
    expect(store.getExist2).toBe(true);
    expect(store.getDoing).toBe(true);
  });
});

describe('stores/useTrace', () => {
  beforeEach(() => {
    setActivePinia(createPinia());
  });

  it('格式化 trace 列表，并支持瀑布树折叠展开联动与重置表格状态', () => {
    const store = useTrace();

    store.setTraceList([
      {
        trace_id: 't-1',
        trace_duration: 125.5,
        time: '2026-11-24 10:00:00',
        root_service: 'mcp-proxy',
        root_span_name: 'tools/call',
        root_status_code: {
          value: '200',
          type: 'normal',
        },
        root_category: 'mcp',
      } as any,
    ]);
    expect(store.traceList[0]).toMatchObject({
      trace_id: 't-1',
      duration: '125.5 ms',
      entryService: 'mcp-proxy',
      entryEndpoint: 'tools/call',
      statusCode: '200',
      status: 'normal',
      type: 'mcp',
    });

    // 设置调用链数据并验证聚合节点折叠/展开切换
    store.setMcpTraceInfo({
      request_id: 'req-1',
      x_request_id: 'x-req-1',
      total_latency_ms: 50,
      spans: [
        {
          span_id: 's1',
          parent_span_id: '',
          service: 'mcp-proxy',
          service_name: 'mcp-proxy',
          operation: 'tools/call',
          layer: 'mcp',
          mcp_method: 'tools/call',
          start_offset_ms: 0,
          latency_ms: 50,
          children: [
            {
              span_id: 's2',
              parent_span_id: 's2',
              service: 'upstream',
              service_name: 'upstream',
              operation: 'GET /items',
              layer: 'gateway',
              start_offset_ms: 10,
              latency_ms: 20,
              group_info: { id: 'grp-1' },
              is_expand: false,
            },
          ],
        },
      ],
    } as unknown as ITraceLog);

    expect(store.traceTree.spans).toHaveLength(2);
    expect(store.spanGroupTree.map(s => s.span_id)).toEqual(['s1']);

    store.updateSpanGroupCollapse('grp-1', 'expand');
    expect(store.spanGroupTree.map(s => s.span_id)).toEqual(['s1', 's2']);

    store.updateSpanGroupCollapse('grp-1', 'collpase');
    expect(store.spanGroupTree.map(s => s.span_id)).toEqual(['s1']);

    // resetTable 重置列表与计数
    store.setPageLoading(true);
    store.setTraceTotalCount(42);
    store.resetTable();
    expect(store.loading).toBe(false);
    expect(store.totalCount).toBe(0);
    expect(store.traceList).toEqual([]);
  });

  it('parseTraceChainLogs 标准化上下游网关日志并处理空值', () => {
    const store = useTrace();

    expect(store.parseTraceChainLogs(null)).toEqual({
      upstream_log: null,
      downstream_log: null,
    });

    const parsed = store.parseTraceChainLogs({
      upstream_gateway_log: {
        request_id: 'u-1',
        status: 200,
      },
      downstream_gateway_log: null,
    } as unknown as ITraceLog);

    expect(parsed).toEqual({
      upstream_log: {
        request_id: 'u-1',
        status: 200,
        layer: 'gateway_upstream',
      },
      downstream_log: null,
    });
  });
});
