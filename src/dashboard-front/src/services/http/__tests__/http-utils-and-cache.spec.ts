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

import { afterEach, describe, expect, it, vi } from 'vitest';
import Cache from '@/services/http/lib/cache';
import RequestError from '@/services/http/lib/request-error';
import { paramsSerializer, withExtraQuery } from '@/services/http/lib/utils';

describe('services/http/lib/utils', () => {
  it('withExtraQuery 在查询串非空时拼接，为空时原样返回地址', () => {
    expect(withExtraQuery('/gateways/1/logs/', 'include=status:200&exclude=path:/ping'))
      .toBe('/gateways/1/logs/?include=status:200&exclude=path:/ping');
    expect(withExtraQuery('/gateways/1/logs/', '')).toBe('/gateways/1/logs/');
    expect(withExtraQuery('/gateways/1/logs/')).toBe('/gateways/1/logs/');
  });

  it('paramsSerializer 正确编码常规键值、数组、Date、对象并忽略 null/undefined', () => {
    const date = new Date('2026-11-24T01:02:03.000Z');
    expect(paramsSerializer({
      keyword: 'a b',
      ids: [1, 2],
      at: date,
      filter: { stage: 'prod' },
      empty: null,
      missing: undefined,
    })).toBe(
      'keyword=a+b&ids%5B%5D=1&ids%5B%5D=2&at=2026-11-24T01:02:03.000Z&filter=%7B%22stage%22:%22prod%22%7D',
    );
  });
});

describe('services/http/lib/cache', () => {
  afterEach(() => {
    vi.useRealTimers();
  });

  it('支持写入、读取、删除与清空缓存，且同 key 不覆盖已有缓存值', () => {
    const cache = new Cache();
    const first = Promise.resolve('v1');
    const second = Promise.resolve('v2');

    expect(cache.get('k1')).toBe(false);
    expect(cache.has('k1')).toBe(false);

    cache.set('k1', first, true);
    cache.set('k1', second, true);
    expect(cache.has('k1')).toBe(true);
    expect(cache.get('k1')).toBe(first);

    expect(cache.delete('k1')).toBe(true);
    expect(cache.has('k1')).toBe(false);
    expect(cache.delete('not-exists')).toBe(true);

    cache.set('k2', second, true);
    expect(cache.clear()).toBe(true);
    expect(cache.has('k2')).toBe(false);
  });

  it('带数值 TTL 的缓存过期后自动失效并移除条目', () => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date('2026-11-24T00:00:00.000Z'));

    const cache = new Cache();
    cache.set('ttl-key', Promise.resolve('ok'), 1000);

    expect(cache.has('ttl-key')).toBe(true);
    vi.advanceTimersByTime(1000);
    expect(cache.has('ttl-key')).toBe(true);

    vi.advanceTimersByTime(1);
    expect(cache.has('ttl-key')).toBe(false);
    expect(cache.get('ttl-key')).toBe(false);
  });
});

describe('services/http/lib/request-error', () => {
  it('继承 Error 并保留 code、message 与 response', () => {
    const response = { status: 403 };
    const err = new RequestError(403, '无权限', response);

    expect(err).toBeInstanceOf(Error);
    expect(err.code).toBe(403);
    expect(err.message).toBe('无权限');
    expect(err.response).toBe(response);
  });
});
