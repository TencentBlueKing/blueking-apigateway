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
import { createMemoryHistory, createRouter } from 'vue-router';
import { GATEWAY_PERMISSION_KEYS, GATEWAY_PERMISSION_MATRIX } from '@/constants/gateway-permission';
import { getGatewayErrorRoute, getGatewayRetryRoute } from '@/utils/gateway-access-error';
import { toGatewayFormData, toGatewayUpdatePayload } from '@/utils/gateway-form';
import { getGatewayDisplayName, getGatewayFullName, hasDistinctDisplayName } from '@/utils/gateway-name';
import { canAccessByRole } from '@/utils/gateway-permission';

describe('utils/gateway-name', () => {
  it('按 display_name -> name -> -- 的优先级返回展示名，并在同名或无 ID 时避免重复展示', () => {
    expect(getGatewayDisplayName({
      name: 'demo-gw',
      display_name: ' 示例网关 ',
    })).toBe('示例网关');
    expect(getGatewayDisplayName({
      name: 'demo-gw',
      display_name: '   ',
    })).toBe('demo-gw');
    expect(getGatewayDisplayName(null)).toBe('--');

    // 仅当 display_name 与 name 均非空且内容不同时，才存在独立展示名
    expect(hasDistinctDisplayName({
      name: 'demo-gw',
      display_name: '示例网关',
    })).toBe(true);
    expect(hasDistinctDisplayName({
      name: 'demo-gw',
      display_name: ' demo-gw ',
    })).toBe(false);
    expect(hasDistinctDisplayName({
      name: 'demo-gw',
      display_name: '   ',
    })).toBe(false);
    expect(hasDistinctDisplayName({
      name: '',
      display_name: '仅展示名',
    })).toBe(false);
    expect(hasDistinctDisplayName(null)).toBe(false);

    // 展示名与 ID 相同或为空时，不应拼出 `demo-gw (demo-gw)`
    expect(getGatewayFullName({
      name: 'demo-gw',
      display_name: '示例网关',
    })).toBe('示例网关 (demo-gw)');
    expect(getGatewayFullName({
      name: 'demo-gw',
      display_name: 'demo-gw',
    })).toBe('demo-gw');
    expect(getGatewayFullName({
      name: 'demo-gw',
      display_name: '',
    })).toBe('demo-gw');
    expect(getGatewayFullName({
      name: '',
      display_name: '仅展示名',
    })).toBe('仅展示名');
    expect(getGatewayFullName(null)).toBe('--');
  });
});

describe('utils/gateway-permission', () => {
  it('管理员放行全部权限，运营者严格按权限矩阵判定，未知或空角色始终拒绝', () => {
    expect(canAccessByRole('administrator')).toBe(true);
    expect(canAccessByRole('operator')).toBe(false);
    expect(canAccessByRole('')).toBe(false);
    expect(canAccessByRole('', 'basic-view')).toBe(false);

    for (const key of GATEWAY_PERMISSION_KEYS) {
      expect(canAccessByRole('administrator', key)).toBe(true);
      expect(canAccessByRole('operator', key)).toBe(GATEWAY_PERMISSION_MATRIX[key].operator);
    }
  });
});

describe('utils/gateway-access-error', () => {
  describe('getGatewayErrorRoute', () => {
    it('403/404 与 NO_PERMISSION/NOT_FOUND 跳转 GatewayNotFound 且不附带 retry', () => {
      expect(getGatewayErrorRoute({ response: { status: 403 } }, 12, '/12/stage')).toEqual({
        name: 'GatewayNotFound',
        params: { id: 12 },
        replace: true,
      });
      expect(getGatewayErrorRoute({ error: { code: 'NOT_FOUND' } }, 12, '/12/stage')).toEqual({
        name: 'GatewayNotFound',
        params: { id: 12 },
        replace: true,
      });
      expect(getGatewayErrorRoute({ response: { data: { error: { code: 'NO_PERMISSION' } } } }, 12, '/12/stage')).toEqual({
        name: 'GatewayNotFound',
        params: { id: 12 },
        replace: true,
      });
    });

    it('5xx、网络故障或未知异常跳转 GatewayLoadError 并携带 retry 路径', () => {
      expect(getGatewayErrorRoute({ response: { status: 500 } }, 12, '/12/stage?tab=1')).toEqual({
        name: 'GatewayLoadError',
        params: { id: 12 },
        query: { retry: '/12/stage?tab=1' },
        replace: true,
      });
      expect(getGatewayErrorRoute(new Error('network error'), 12, '/12/stage')).toEqual({
        name: 'GatewayLoadError',
        params: { id: 12 },
        query: { retry: '/12/stage' },
        replace: true,
      });
    });
  });

  describe('getGatewayRetryRoute', () => {
    const createTestRouter = () => createRouter({
      history: createMemoryHistory(),
      routes: [
        {
          path: '/:id',
          name: 'Resources',
          component: { template: '<div />' },
          children: [
            {
              path: 'stage',
              name: 'StageOverview',
              component: { template: '<div />' },
            },
            {
              path: 'error',
              name: 'GatewayLoadError',
              meta: { skipRoleCheck: true },
              component: { template: '<div />' },
            },
          ],
        },
        {
          path: '/other/:id',
          name: 'Other',
          component: { template: '<div />' },
        },
      ],
    });

    it('仅允许重试同网关且经过角色检查的业务路由，其余回退至 BasicInfo', () => {
      const router = createTestRouter();

      expect(getGatewayRetryRoute(router, 12, '/12/stage?tab=overview')).toBe('/12/stage?tab=overview');

      const fallback = {
        name: 'BasicInfo',
        params: { id: 12 },
      };
      // 跨网关、跳过角色校验的错误页、非 Resources 子路由、协议相对地址或非字符串均回退
      expect(getGatewayRetryRoute(router, 12, '/99/stage')).toEqual(fallback);
      expect(getGatewayRetryRoute(router, 12, '/12/error')).toEqual(fallback);
      expect(getGatewayRetryRoute(router, 12, '/other/12')).toEqual(fallback);
      expect(getGatewayRetryRoute(router, 12, '//evil.example.com/12/stage')).toEqual(fallback);
      expect(getGatewayRetryRoute(router, 12, 'https://evil.example.com')).toEqual(fallback);
      expect(getGatewayRetryRoute(router, 12, null)).toEqual(fallback);
    });
  });
});

describe('utils/gateway-form', () => {
  it('toGatewayFormData 生成默认值并对数组与 extra_info 做浅拷贝隔离', () => {
    const source = {
      id: 7,
      name: 'demo',
      maintainers: ['alice'],
      developers: ['bob'],
      bk_app_codes: ['app-1'],
      extra_info: {
        language: 'python',
        repository: 'https://git.example.com/demo',
      },
    };
    const form = toGatewayFormData(source);

    expect(form.display_name).toBe('demo');
    expect(form.is_public).toBe(true);
    expect(form.oauth2_app_enabled).toBe(false);
    expect(form.kind).toBe(0);

    form.maintainers.push('charlie');
    form.extra_info.repository = 'changed';
    expect(source.maintainers).toEqual(['alice']);
    expect(source.extra_info.repository).toBe('https://git.example.com/demo');
  });

  it('toGatewayUpdatePayload 仅在字段变化或满足条件时下发对应字段', () => {
    const saved = toGatewayFormData({
      id: 7,
      name: 'demo',
      display_name: 'Demo',
      description: 'old',
      maintainers: ['alice'],
      developers: ['bob'],
      bk_app_codes: ['app-1'],
      related_app_codes: ['app-2'],
      is_public: true,
      oauth2_app_enabled: false,
      kind: 0,
    });
    const edited = {
      ...saved,
      description: 'new',
    };

    // display_name 与 oauth2_app_enabled 未变化时不发送；appBindingEnabled=false 不发 bk_app_codes；非可编程网关不发 extra_info
    const payload = toGatewayUpdatePayload(edited, saved, false);
    expect(payload).toEqual({
      description: 'new',
      maintainers: ['alice'],
      is_public: true,
      developers: ['bob'],
      related_app_codes: ['app-2'],
    });
    expect('display_name' in payload).toBe(false);
    expect('oauth2_app_enabled' in payload).toBe(false);
    expect('bk_app_codes' in payload).toBe(false);
    expect('extra_info' in payload).toBe(false);

    // 可编程网关且改动 display_name / oauth2_app_enabled、开启 appBindingEnabled 时全部带上，非法 language 置 undefined
    const programmablePayload = toGatewayUpdatePayload(
      {
        ...saved,
        display_name: 'Demo Renamed',
        oauth2_app_enabled: true,
        kind: 1,
        extra_info: {
          language: 'rust',
          repository: 'https://git.example.com/demo',
        },
      },
      saved,
      true,
    );
    expect(programmablePayload.display_name).toBe('Demo Renamed');
    expect(programmablePayload.oauth2_app_enabled).toBe(true);
    expect(programmablePayload.bk_app_codes).toEqual(['app-1']);
    expect(programmablePayload.extra_info).toEqual({
      language: undefined,
      repository: 'https://git.example.com/demo',
    });
  });
});
