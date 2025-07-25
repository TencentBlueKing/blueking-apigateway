/*
 * TencentBlueKing is pleased to support the open source community by making
 * 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
 * Copyright (C) 2025 Tencent. All rights reserved.
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

import type { AxiosError, AxiosInterceptorManager, AxiosResponse } from 'axios';
import { Message } from 'bkui-vue';

import { downloadFile, messageError, parseURL } from '@/utils';

import { showLoginModal } from '@blueking/login-modal';

import RequestError from '../lib/request-error';

import { t } from '@/locales';

// 标记已经登录过状态
// 第一次登录跳转登录页面，之后弹框登录
let hasLoggedIn = false;
// 错误代码映射
const errorMessageMap = {
  INVALID_ARGUMENT: {
    overview: t('参数错误。'),
    suggestion: t('请检查提交的内容是否正确。'),
  },
  NO_PERMISSION: {
    overview: t('没有权限。'),
    suggestion: t('您没有执行该操作的权限。'),
  },
};

const redirectLogin = (loginUrl: string) => {
  const { protocol, host, pathname } = parseURL(loginUrl);
  const domain = `${protocol}://${host}${pathname}`;

  if (hasLoggedIn) {
    showLoginModal({
      loginUrl:
        `${domain}?is_from_logout=1&c_url=${decodeURIComponent(`${window.location.origin}login-success.html`)}`,
    });
  }
  else {
    window.location.href = `${domain}?is_from_logout=1&c_url=${decodeURIComponent(window.location.href)}`;
  }
};

export default (interceptors: AxiosInterceptorManager<AxiosResponse>) => {
  interceptors.use(
    (response: AxiosResponse) => {
      if (['application/octet-stream'].includes(response.headers['content-type'])) {
        downloadFile(response);
        return response.data;
      }
      if (response.data.data !== undefined || response.status < 400) {
        hasLoggedIn = true;
        return response.data;
      }
      // 后端逻辑处理报错
      const { code, message = '系统错误' } = response.data;
      throw new RequestError(code, message, response);
    },
    (
      error: AxiosError<{
        error: {
          code: string
          message: string
          data: any
        }
      }> & { __CANCEL__: any },
    ) => {
      // 超时取消

      if (error.__CANCEL__) {
        return Promise.reject(new RequestError('CANCEL', '请求已取消'));
      }
      // 处理 http 错误响应逻辑
      if (error.response) {
        // 登录状态失效
        if (error.response.data.error.code === 'UNAUTHENTICATED') {
          return Promise.reject(new RequestError(401, '登录状态失效', error.response));
        }
        // 默认使用 http 错误描述，如果有自定义错误描述优先使用
        let errorMessage = error.response.statusText;
        if (error.response.data && error.response.data.error.code) {
          errorMessage = error.response.data.error.message;
        }
        return Promise.reject(new RequestError(error.response.status || -1, errorMessage, error.response));
      }
      return Promise.reject(new RequestError(-1, `${window.BK_DASHBOARD_FE_URL} 无法访问`));
    },
  );

  // 统一错误处理逻辑
  interceptors.use(undefined, (error: RequestError) => {
    const errorObj = error.response.data.error;
    switch (error.code) {
      // 未登陆
      case 401:
        redirectLogin(errorObj.data.login_url);
        break;
      case 'CANCEL':
        return Promise.reject(error);
      // 网络超时
      case 'ECONNABORTED':
        messageError(t('请求超时'));
        break;
      default:
        if (!error.response.config.payload.catchError) {
          Message({
            theme: 'error',
            actions: [
              {
                id: 'assistant',
                disabled: true,
              },
            ],
            message: {
              code: errorObj.code,
              overview: errorMessageMap[errorObj.code as keyof typeof errorMessageMap]?.overview || t('系统错误'),
              suggestion: errorObj.message
                ? JSON.stringify(errorObj.message)
                : errorMessageMap[errorObj.code as keyof typeof errorMessageMap]?.suggestion || '',
              type: 'json',
              details: errorObj,
              assistant: '',
            },
          });
        }
    }
    return Promise.reject(error.response.data);
  });
};
