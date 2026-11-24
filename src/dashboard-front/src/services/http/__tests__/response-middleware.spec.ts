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

const {
  bkMessageMock,
  downloadFileMock,
  envState,
  messageErrorMock,
  showLoginModalMock,
} = vi.hoisted(() => ({
  bkMessageMock: vi.fn(),
  downloadFileMock: vi.fn(),
  envState: { BK_DASHBOARD_FE_URL: '' },
  messageErrorMock: vi.fn(),
  showLoginModalMock: vi.fn(),
}));

vi.mock('bkui-vue', () => ({ Message: bkMessageMock }));
vi.mock('@blueking/login-modal', () => ({ showLoginModal: showLoginModalMock }));
vi.mock('@/locales', () => ({ t: (key: string) => key }));
vi.mock('@/stores', () => ({ useEnv: () => ({ env: envState }) }));
vi.mock('@/utils', async () => {
  const { parseURL } = await vi.importActual<typeof import('@/utils/url')>('@/utils/url');
  return {
    downloadFile: downloadFileMock,
    messageError: messageErrorMock,
    parseURL,
  };
});

interface IInterceptorPair {
  onFulfilled?: (val: any) => any
  onRejected?: (err: any) => any
}

const setupInterceptors = async () => {
  const handlers: IInterceptorPair[] = [];
  const fakeManager = {
    use: (onFulfilled?: (val: any) => any, onRejected?: (err: any) => any) => {
      handlers.push({
        onFulfilled,
        onRejected,
      });
      return handlers.length - 1;
    },
  };

  const [
    { default: registerResponseMiddleware },
    { default: RequestError },
  ] = await Promise.all([
    import('@/services/http/middleware/response'),
    import('@/services/http/lib/request-error'),
  ]);
  registerResponseMiddleware(fakeManager as any);

  const runFulfilled = async (response: any) => {
    let current = response;
    for (const h of handlers) {
      if (h.onFulfilled) {
        current = await h.onFulfilled(current);
      }
    }
    return current;
  };

  const runRejected = async (error: any) => {
    let current = error;
    for (const h of handlers) {
      if (h.onRejected) {
        try {
          return await h.onRejected(current);
        }
        catch (nextError) {
          current = nextError;
        }
      }
    }
    throw current;
  };

  return {
    RequestError,
    runFulfilled,
    runRejected,
  };
};

describe('services/http/middleware/response', () => {
  const originalLocation = window.location;

  beforeEach(() => {
    vi.resetModules();
    setActivePinia(createPinia());
    envState.BK_DASHBOARD_FE_URL = '';
    bkMessageMock.mockReset();
    downloadFileMock.mockReset();
    messageErrorMock.mockReset();
    showLoginModalMock.mockReset();
    window.BK_DASHBOARD_URL = 'https://apigw.example.com/api';

    Object.defineProperty(window, 'location', {
      configurable: true,
      writable: true,
      value: {
        href: 'https://apigw.example.com/gateways',
        origin: 'https://apigw.example.com',
      },
    });
  });

  afterEach(() => {
    Object.defineProperty(window, 'location', {
      configurable: true,
      writable: true,
      value: originalLocation,
    });
  });

  it('正常解包成功响应，并在响应为 application/octet-stream 时触发下载', async () => {
    const { runFulfilled } = await setupInterceptors();

    const jsonRes = await runFulfilled({
      status: 200,
      headers: { 'content-type': 'application/json' },
      config: { url: '/gateways/' },
      data: { data: { id: 1 } },
    });
    expect(jsonRes).toEqual({ data: { id: 1 } });

    const blob = new Blob(['demo']);
    const streamRes = {
      status: 200,
      headers: { 'content-type': 'application/octet-stream' },
      config: { url: '/gateways/1/export/' },
      data: blob,
    };
    expect(await runFulfilled(streamRes)).toBe(blob);
    expect(downloadFileMock).toHaveBeenCalledWith(streamRes);
  });

  it('取消请求穿透两层拦截器返回 CANCEL RequestError 且不弹任何全局提示', async () => {
    const { RequestError, runRejected } = await setupInterceptors();

    const err = await runRejected({ __CANCEL__: true }).catch(e => e);

    expect(err).toBeInstanceOf(RequestError);
    expect(err.code).toBe('CANCEL');
    expect(err.message).toBe('请求已取消');
    expect(bkMessageMock).not.toHaveBeenCalled();
    expect(messageErrorMock).not.toHaveBeenCalled();
  });

  it('超时、断网及非标准网关响应（无 data.error）安全降级提示而不抛 TypeError', async () => {
    const { RequestError, runRejected } = await setupInterceptors();

    // 1. 请求超时（无 response）
    const timeoutErr = await runRejected({ code: 'ECONNABORTED' }).catch(e => e);
    expect(timeoutErr).toBeInstanceOf(RequestError);
    expect(timeoutErr.code).toBe('ECONNABORTED');
    expect(messageErrorMock).toHaveBeenCalledWith('请求超时');

    messageErrorMock.mockClear();

    // 2. 网络不可达（无 response）
    const networkErr = await runRejected({ message: 'Network Error' }).catch(e => e);
    expect(networkErr).toBeInstanceOf(RequestError);
    expect(networkErr.code).toBe(-1);
    expect(messageErrorMock).toHaveBeenCalledWith('https://apigw.example.com/api 无法访问');

    messageErrorMock.mockClear();

    // 3. 非标准 502 HTML 响应且未配置 payload
    const badGatewayRes = {
      response: {
        status: 502,
        statusText: 'Bad Gateway',
        config: {},
        data: '<html>502 Bad Gateway</html>',
      },
    };
    await expect(runRejected(badGatewayRes)).rejects.toBe('<html>502 Bad Gateway</html>');
    expect(bkMessageMock).not.toHaveBeenCalled();
    expect(messageErrorMock).toHaveBeenCalledWith('Bad Gateway');
  });

  it('未登录遇到 401 整页跳转登录；经过鉴权接口后遇到 401 弹出登录小窗；免鉴权接口不标记登录态', async () => {
    const { runFulfilled, runRejected } = await setupInterceptors();

    const unauthError = {
      response: {
        status: 401,
        statusText: 'Unauthorized',
        config: { payload: {} },
        data: {
          error: {
            code: 'UNAUTHENTICATED',
            message: 'please login',
            data: { login_url: 'https://login.example.com/plain' },
          },
        },
      },
    };

    // 免鉴权接口成功不应标记为已登录
    await runFulfilled({
      status: 200,
      headers: {},
      config: { url: '/ping/' },
      data: { data: 'pong' },
    });

    await expect(runRejected(unauthError)).rejects.toEqual(unauthError.response.data);
    expect(showLoginModalMock).not.toHaveBeenCalled();
    expect(window.location.href).toBe(
      'https://login.example.com/plain/?is_from_logout=1&c_url=https://apigw.example.com/gateways',
    );

    // 业务接口成功后标记为已登录，再次 401 改弹登录小窗
    await runFulfilled({
      status: 200,
      headers: {},
      config: { url: '/gateways/' },
      data: { data: [] },
    });

    await expect(runRejected(unauthError)).rejects.toEqual(unauthError.response.data);
    expect(showLoginModalMock).toHaveBeenCalledWith({
      loginUrl:
        'https://login.example.com/plain/?is_from_logout=1&c_url=https://apigw.example.com/login-success.html',
    });
  });

  it('普通接口报错默认弹出 Message，开启 catchError 时静默抛给调用方', async () => {
    const { runRejected } = await setupInterceptors();

    const baseError = {
      response: {
        status: 400,
        statusText: 'Bad Request',
        config: { payload: {} },
        data: {
          error: {
            code: 'INVALID_ARGUMENT',
            message: 'name is required',
            data: null,
          },
        },
      },
    };

    await expect(runRejected(baseError)).rejects.toEqual(baseError.response.data);
    expect(bkMessageMock).toHaveBeenCalledTimes(1);
    expect(bkMessageMock).toHaveBeenCalledWith(expect.objectContaining({
      theme: 'error',
      message: expect.objectContaining({
        code: 'INVALID_ARGUMENT',
        overview: '参数错误。',
      }),
    }));

    bkMessageMock.mockClear();

    const silentError = {
      response: {
        ...baseError.response,
        config: { payload: { catchError: true } },
      },
    };
    await expect(runRejected(silentError)).rejects.toEqual(silentError.response.data);
    expect(bkMessageMock).not.toHaveBeenCalled();
  });
});
