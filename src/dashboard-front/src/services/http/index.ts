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
