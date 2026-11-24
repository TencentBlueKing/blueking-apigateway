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
import type { IResourceVersionDiffResource } from '@/services/types/gateway/resource-version';
import type { IDiffData } from '@/types/resource-version';
import {
  createDiffIndex,
  filterDiffData,
  getPluginDiffClass,
  hasOnlyDocTimeDiff,
  hasProxyDisplayDiff,
  matchesResourceKeyword,
  normalizeResource,
} from '@/components/release/version-diff/resource-diff';

const createResource = (
  overrides: Partial<IResourceVersionDiffResource> = {},
): IResourceVersionDiffResource => ({
  id: 1,
  name: 'get_users',
  method: 'GET',
  path: '/api/v1/users/',
  proxy: {
    type: 'http',
    backend_id: 10,
    config: {
      method: 'GET',
      path: '/backend/users/',
      timeout: 30,
    },
  },
  ...overrides,
} as unknown as IResourceVersionDiffResource);

describe('components/release/version-diff/resource-diff', () => {
  describe('createDiffIndex & hasProxyDisplayDiff', () => {
    it('合并两侧不对称差异对象，保留 falsy 字段值与父子路径，且不展开数组', () => {
      const index = createDiffIndex(
        {
          is_public: false,
          timeout: 0,
          description: '',
          tags: ['a', 'b'],
          proxy: {
            config: {
              path: '/old',
            },
          },
        } as any,
        {
          nullable: null,
          emptyObj: {},
          proxy: {
            backend_id: 2,
          },
        } as any,
      );

      expect(index.has('is_public')).toBe(true);
      expect(index.has('timeout')).toBe(true);
      expect(index.has('description')).toBe(true);
      expect(index.has('nullable')).toBe(true);
      expect(index.has('emptyObj')).toBe(true);
      expect(index.has('tags')).toBe(true);
      expect(index.has('tags.0')).toBe(false);
      expect(index.has('proxy')).toBe(true);
      expect(index.has('proxy.backend_id')).toBe(true);
      expect(index.has('proxy.config')).toBe(true);
      expect(index.has('proxy.config.path')).toBe(true);
    });

    it('仅在可见的后端配置字段发生变化时返回 true，避免内部未渲染字段触发空标题', () => {
      const hiddenOnly = createDiffIndex({
        proxy: {
          config: {
            upstreams: { loadbalance: 'roundrobin' },
            transform_headers: { set: {} },
          },
        },
      } as any, null);
      expect(hasProxyDisplayDiff(hiddenOnly)).toBe(false);

      const visibleDiff = createDiffIndex(null, {
        proxy: { config: { timeout: 60 } },
      } as any);
      expect(hasProxyDisplayDiff(visibleDiff)).toBe(true);
    });
  });

  describe('getPluginDiffClass & hasOnlyDocTimeDiff', () => {
    it('准确判定插件的无差异、更新、删除（源侧）与新增（目标侧）状态', () => {
      const srcDiff = {
        plugins: {
          'bk-cors': { allow_origins: '*' },
          'bk-ip-restriction': { whitelist: '1.1.1.1' },
        },
      } as any;
      const targetDiff = {
        plugins: {
          'bk-cors': { allow_origins: 'https://example.com' },
          'bk-rate-limit': { rates: {} },
        },
      } as any;

      expect(getPluginDiffClass('bk-mock', srcDiff, targetDiff, true)).toBe('no-diff');
      expect(getPluginDiffClass('bk-cors', srcDiff, targetDiff, true)).toBe('item-updated');
      expect(getPluginDiffClass('bk-ip-restriction', srcDiff, targetDiff, true)).toBe('item-deleted');
      expect(getPluginDiffClass('bk-rate-limit', targetDiff, srcDiff, false)).toBe('item-added');
    });

    it('合并两侧键后判定是否仅包含 doc_updated_time 差异', () => {
      expect(hasOnlyDocTimeDiff({ doc_updated_time: { zh: '2026-01-01' } } as any, null)).toBe(true);
      expect(hasOnlyDocTimeDiff(
        { doc_updated_time: { zh: '2026-01-01' } } as any,
        { doc_updated_time: { zh: '2026-01-02' } } as any,
      )).toBe(true);
      expect(hasOnlyDocTimeDiff(
        { doc_updated_time: { zh: '2026-01-01' } } as any,
        { path: '/new' } as any,
      )).toBe(false);
      expect(hasOnlyDocTimeDiff(null, null)).toBe(false);
    });
  });

  describe('normalizeResource', () => {
    it('兼容对象/JSON 字符串/损坏 JSON 的 proxy.config，动态映射 backend_name 且不修改原对象', () => {
      const backends = [{
        id: 10,
        name: 'user-service',
      }];

      const rawStringProxy = createResource({
        proxy: {
          type: 'http',
          backend_id: 10,
          config: '{"path":"/v2/users","timeout":45}',
        } as any,
      });
      const normalized = normalizeResource(rawStringProxy, backends);
      expect(normalized.proxy.config).toEqual({
        path: '/v2/users',
        timeout: 45,
      });
      expect(normalized.proxy.backend_name).toBe('user-service');
      expect(normalized.plugins).toEqual([]);
      expect(normalized.doc_updated_time).toEqual({});
      expect(typeof rawStringProxy.proxy?.config).toBe('string');

      // 损坏的 JSON 字符串与 null 快照安全兜底为空对象
      const broken = normalizeResource(createResource({
        proxy: {
          type: 'http',
          backend_id: 999,
          config: '{broken-json',
        } as any,
      }), backends);
      expect(broken.proxy.config).toEqual({});
      expect(broken.proxy.backend_name).toBe('');

      expect(normalizeResource(null, backends).proxy.config).toEqual({});
    });
  });

  describe('matchesResourceKeyword & filterDiffData', () => {
    it('忽略大小写匹配方法、路径、名称及字符串态后端路径', () => {
      const res = createResource({
        name: 'CreateOrder',
        method: 'POST',
        path: '/orders/create',
        proxy: {
          type: 'http',
          backend_id: 10,
          config: '{"path":"/internal/v2/billing"}',
        } as any,
      });

      expect(matchesResourceKeyword(res, '')).toBe(true);
      expect(matchesResourceKeyword(res, 'post')).toBe(true);
      expect(matchesResourceKeyword(res, 'CREATEORDER')).toBe(true);
      expect(matchesResourceKeyword(res, '/orders/')).toBe(true);
      expect(matchesResourceKeyword(res, 'billing')).toBe(true);
      expect(matchesResourceKeyword(res, 'unmatched')).toBe(false);
    });

    it('综合过滤类型、关键词与仅文档更新时间差异，且保留原条目引用', () => {
      const addItem = {
        ...createResource({
          id: 1,
          name: 'add_user',
        }),
        isExpanded: false,
      };
      const delItem = {
        ...createResource({
          id: 2,
          name: 'del_order',
          path: '/api/v1/orders/',
          proxy: {
            type: 'http',
            backend_id: 10,
            config: {
              method: 'GET',
              path: '/backend/orders/',
              timeout: 30,
            },
          } as any,
        }),
        isExpanded: false,
      };
      const docOnlyUpdate = {
        isExpanded: false,
        source: createResource({
          id: 3,
          name: 'doc_only_user',
          diff: { doc_updated_time: { zh: 't1' } } as any,
        }),
        target: createResource({
          id: 3,
          name: 'doc_only_user',
          diff: { doc_updated_time: { zh: 't2' } } as any,
        }),
      };
      const realUpdate = {
        isExpanded: false,
        source: createResource({
          id: 4,
          name: 'old_name',
          path: '/api/v1/legacy/',
          proxy: {
            type: 'http',
            backend_id: 10,
            config: {
              method: 'GET',
              path: '/backend/legacy/',
              timeout: 30,
            },
          } as any,
          diff: { path: '/old' } as any,
        }),
        target: createResource({
          id: 4,
          name: 'renamed_user',
          diff: { path: '/new' } as any,
        }),
      };

      const diffData: IDiffData = {
        add: [addItem],
        delete: [delItem],
        update: [docOnlyUpdate, realUpdate],
      };

      // 隐藏仅文档更新 + 关键词 'user'（应命中 addItem 与 target 改名后的 realUpdate）
      const filtered = filterDiffData(diffData, {
        keyword: 'user',
        diffType: '',
        hideOnlyDiffInDocUpdatedTime: true,
      });
      expect(filtered.add).toEqual([addItem]);
      expect(filtered.add[0]).toBe(addItem);
      expect(filtered.delete).toEqual([]);
      expect(filtered.update).toEqual([realUpdate]);
      expect(filtered.update[0]).toBe(realUpdate);

      // 限定 diffType='delete' 时只保留删除列表
      const onlyDelete = filterDiffData(diffData, {
        keyword: '',
        diffType: 'delete',
        hideOnlyDiffInDocUpdatedTime: false,
      });
      expect(onlyDelete.add).toEqual([]);
      expect(onlyDelete.update).toEqual([]);
      expect(onlyDelete.delete).toEqual([delItem]);
    });
  });
});
