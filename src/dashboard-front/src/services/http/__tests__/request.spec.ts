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
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

const { axiosMock, cancelSource, cookieGetMock } = vi.hoisted(() => {
  const source = {
    token: { reason: undefined },
    cancel: vi.fn(),
  };
  const mockFn = vi.fn();
  Object.assign(mockFn, {
    defaults: { headers: { common: {} as Record<string, string> } },
    interceptors: {
      request: {
        handlers: [],
        use: vi.fn(),
      },
      response: {
        handlers: [{}],
        use: vi.fn(),
      },
    },
    CancelToken: {
      source: vi.fn(() => source),
    },
  });

  return {
    axiosMock: mockFn,
    cancelSource: source,
    cookieGetMock: vi.fn(),
  };
});

vi.mock('axios', () => ({ default: axiosMock }));
vi.mock('js-cookie', () => ({
  default: {
    get: cookieGetMock,
  },
}));
vi.mock('@/services/http/middleware/response', () => ({ default: vi.fn() }));

import { getCancelTokenSource } from '@/services/http';
import Request from '@/services/http/lib/request';
import { useEnv } from '@/stores/useEnv';

describe('services/http/lib/request', () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    window.BK_DASHBOARD_URL = 'https://apigw.example.com/api';
    axiosMock.mockReset();
    cookieGetMock.mockReset();
    vi.spyOn(console, 'warn').mockImplementation(() => undefined);
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('按方法类型区分 query 参数与 body 数据，并从自定义 CSRF Cookie 注入请求头', async () => {
    const envStore = useEnv();
    envStore.env.BK_DASHBOARD_CSRF_COOKIE_NAME = 'custom_csrf_cookie';
    cookieGetMock.mockReturnValue('token-xyz');
    axiosMock.mockResolvedValue({ data: { items: [1] } });

    const getReq = new Request({
      url: '/gateways/',
      method: 'get',
      params: { limit: 10 },
      payload: { timeout: 5000 },
    });
    const getResult = await getReq.run();

    expect(getResult).toEqual({ items: [1] });
    expect(cookieGetMock).toHaveBeenCalledWith('custom_csrf_cookie');
    expect(axiosMock).toHaveBeenCalledWith(expect.objectContaining({
      baseURL: 'https://apigw.example.com/api',
      url: '/gateways/',
      method: 'get',
      params: { limit: 10 },
      timeout: 5000,
      cancelToken: cancelSource.token,
      headers: expect.objectContaining({ 'X-CSRFToken': 'token-xyz' }),
    }));
    expect(getCancelTokenSource()).toBe(cancelSource);

    // POST 请求应将 params 放入 data 字段
    axiosMock.mockResolvedValue({ data: { id: 99 } });
    const postReq = new Request({
      url: '/gateways/',
      method: 'post',
      params: { name: 'demo' },
    });
    const postResult = await postReq.run();

    expect(postResult).toEqual({ id: 99 });
    expect(axiosMock).toHaveBeenLastCalledWith(expect.objectContaining({
      method: 'post',
      data: { name: 'demo' },
    }));
  });

  it('仅 GET 请求启用 payload.cache，缓存期内复用 Promise，过期后重新请求', async () => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date('2026-11-24T00:00:00.000Z'));

    axiosMock.mockResolvedValueOnce({ data: 'first-response' });
    axiosMock.mockResolvedValueOnce({ data: 'second-response' });

    const createGet = () => new Request({
      url: '/gateways/1/cached/',
      method: 'get',
      params: { page: 1 },
      payload: { cache: 5000 },
    });

    const r1 = createGet();
    expect(r1.isCachedable).toBe(true);
    expect(await r1.run()).toBe('first-response');

    // 缓存有效期内直接命中缓存，不再触发 axios
    const r2 = createGet();
    expect(r2.checkCache()).toBe(true);
    expect(await r2.run()).toBe('first-response');
    expect(axiosMock).toHaveBeenCalledTimes(1);

    // 超过 TTL 后重新发起请求
    vi.advanceTimersByTime(5001);
    const r3 = createGet();
    expect(r3.checkCache()).toBe(false);
    expect(await r3.run()).toBe('second-response');
    expect(axiosMock).toHaveBeenCalledTimes(2);

    r3.deleteCache();
  });

  it('POST 等写请求即使传了 payload.cache 也不启用缓存', () => {
    const postReq = new Request({
      url: '/gateways/1/',
      method: 'post',
      payload: { cache: 5000 },
    });
    expect(postReq.isCachedable).toBe(false);
    expect(postReq.checkCache()).toBe(false);
  });
});
