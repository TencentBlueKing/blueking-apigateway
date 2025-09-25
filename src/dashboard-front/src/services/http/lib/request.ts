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

import { has } from 'lodash-es';
import axios, { type AxiosRequestConfig, type CancelTokenSource } from 'axios';
import Cookie from 'js-cookie';

import { setCancelTokenSource } from '../index';
import requestMiddleware from '../middleware/request';
import responseMiddleware from '../middleware/response';

import Cache, { type CacheExpire, type CacheValue } from './cache';
import { paramsSerializer } from './utils';
import { useEnv } from '@/stores';

const cacheHandler = new Cache();

export type Method = 'get' | 'delete' | 'post' | 'put' | 'download' | 'patch';
export interface Config {
  url: string
  method: Method
  params?: Record<string, any>
  payload?: {
    timeout?: number
    cache?: string | number | boolean
    onUploadProgress?: (params: CancelTokenSource) => void
    permission?: 'page' | 'dialog' | 'catch'
    catchError?: boolean
  } & AxiosRequestConfig
}

/* @ts-expect-error */
if (axios.interceptors.response.handlers.length < 1) {
  requestMiddleware(axios.interceptors.request);
  responseMiddleware(axios.interceptors.response);
}

const { CancelToken } = axios;

axios.defaults.headers.common['X-Requested-With'] = 'XMLHttpRequest';
// if (CSRFToken !== undefined) {
//   axios.defaults.headers.common['X-CSRFToken'] = CSRFToken;
// } else {
//   console.warn('Can not find csrftoken in document.cookie');
// }
const defaultConfig: Record<string, any> = {
  timeout: 60000,
  headers: {},
  withCredentials: true,
  paramsSerializer,
};

export default class Request {
  static supportMethods = ['get', 'post', 'delete', 'put', 'patch'];
  static willCachedMethods = ['get'];
  static bodyDataMethods = ['post', 'put', 'delete', 'patch'];

  cache: Cache;
  config: Config;

  constructor(config = {} as Config) {
    this.cache = cacheHandler;
    this.config = config;
  }

  get taskKey() {
    return `${this.config.method}_${this.config.url}_${JSON.stringify(this.config.params)}`;
  }

  get isCachedable() {
    if (!Request.willCachedMethods.includes(this.config.method)) {
      return false;
    }
    if (!this.config.payload || !has(this.config.payload, 'cache')) {
      return false;
    }
    return true;
  }

  get axiosConfig() {
    const envStore = useEnv();
    const CSRF_TOKEN_KEY = envStore.env?.BK_DASHBOARD_CSRF_COOKIE_NAME || 'bk_apigw_dashboard_csrftoken';
    const CSRFToken = Cookie.get(CSRF_TOKEN_KEY);

    if (!CSRFToken) {
      console.warn('Can not find csrftoken in document.cookie');
    }
    else {
      defaultConfig.headers['X-CSRFToken'] = CSRFToken;
    }

    const config: Record<string, any> = Object.assign({}, defaultConfig, {
      baseURL: window.BK_DASHBOARD_URL,
      url: this.config.url,
      method: this.config.method,
      payload: this.config.payload || {},
    });

    if (this.config.params) {
      if (Request.bodyDataMethods.includes(this.config.method)) {
        config.data = this.config.params;
      }
      else {
        config.params = this.config.params;
      }
    }

    if (this.config.payload) {
      const configPayload = this.config.payload;
      Object.keys(configPayload).forEach((configExtend) => {
        config[configExtend] = configPayload[configExtend as keyof Config['payload']];
      });
    }
    return config;
  }

  checkCache() {
    return this.isCachedable && this.cache.has(this.taskKey);
  }

  setCache(data: CacheValue) {
    this.isCachedable && this.cache.set(this.taskKey, data, this.config.payload?.cache as CacheExpire);
  }

  deleteCache() {
    this.cache.delete(this.taskKey);
  }

  run() {
    if (this.checkCache()) {
      return this.cache.get(this.taskKey);
    }

    const source = CancelToken.source();
    setCancelTokenSource(source);

    const requestHandler = axios({
      ...this.axiosConfig,
      cancelToken: source.token,
    }).then((data) => {
      this.setCache(requestHandler);
      return data.data;
    });
    this.setCache(requestHandler);
    return requestHandler;
  }
}
