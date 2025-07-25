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

import type { CancelTokenSource } from 'axios';

import Request, { type Config, type Method } from './lib/request';

export type IRequestPayload = Config['payload'];

// type IRequestConfig = Pick<Config, 'params' | 'payload'>

export type IRequestResponseData<T> = T;
export interface IRequestResponsePaginationData<T> {
  results: Array<T>
  page: number
  num_pages: number
  total: number
}

const methodList: Array<Method> = ['get', 'delete', 'post', 'put', 'download', 'patch'];

let cancelTokenSource: CancelTokenSource;

export const setCancelTokenSource = (source: CancelTokenSource) => {
  cancelTokenSource = source;
};

export const getCancelTokenSource = () => cancelTokenSource;

const handler = {} as {
  [n in Method]: <T = any>(url: string, params?: Record<string, any>, payload?: IRequestPayload) => Promise<T>;
};

methodList.forEach((method) => {
  Object.defineProperty(handler, method, {
    get() {
      return function (url: string, params: Record<string, any>, payload: IRequestPayload) {
        const handler = new Request({
          url,
          method,
          params,
          payload,
        });
        return handler.run();
      };
    },
  });
});

export default handler;
