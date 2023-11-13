import { deepMerge } from '@/common/util';
import successInterceptor from './success-interceptor';
import errorInterceptor from './error-interceptor';
import RequestError from './request-error';
import cookie from 'cookie';


export interface IFetchConfig extends RequestInit {
  responseType?: 'json' | 'text' | 'arrayBuffer' | 'blob' | 'formData',
  globalError?: Boolean,
}

type HttpMethod = (url: string, payload?: any, config?: IFetchConfig) => Promise<any>;

interface IHttp {
  get?: HttpMethod;
  post?: HttpMethod;
  put?: HttpMethod;
  delete?: HttpMethod;
  head?: HttpMethod;
  options?: HttpMethod;
  patch?: HttpMethod;
}

// Content-Type
const contentTypeMap: any = {
  json: 'application/json',
  text: 'text/plain',
  formData: 'multipart/form-data',
};
const methodsWithoutData = ['get', 'head', 'options'];
const methodsWithData = ['post', 'put', 'patch', 'delete'];
const allMethods = [...methodsWithoutData, ...methodsWithData];

// 拼装发送请求配置
const getFetchConfig = (method: string, payload: any, config: IFetchConfig) => {
  // 合并配置
  let fetchConfig: IFetchConfig = deepMerge(
    {
      method: method.toLocaleUpperCase(),
      mode: 'cors',
      cache: 'default',
      credentials: 'include',
      headers: {
        'X-Requested-With': 'fetch',
        'Content-Type': contentTypeMap[config.responseType] || 'application/json',
      },
      redirect: 'follow',
      referrerPolicy: 'no-referrer-when-downgrade',
      responseType: 'json',
      globalError: true,
    },
    config,
  );
  // merge payload
  if (methodsWithData.includes(method)) {
    fetchConfig = deepMerge(fetchConfig, { body: JSON.stringify(payload) });
  } else {
    fetchConfig = deepMerge(fetchConfig, payload);
  }
  if (config.responseType === 'formData') { // 导入文件
    fetchConfig = {
      method: 'POST',
      body: payload,
      credentials: 'include',
      headers: {},
      globalError: true,
      responseType: 'json',
    };
  }
  return fetchConfig;
};

// 拼装发送请求 url
const getFetchUrl = (url: string, method: string, payload = {}) => {
  try {
    // 基础 url
    const baseUrl = location.origin + window.SITE_URL + process.env.BK_AJAX_URL_PREFIX;
    // 构造 url 对象
    const urlObject: URL = new URL(url, baseUrl);
    // get 请求需要将参数拼接到url上
    if (methodsWithoutData.includes(method)) {
      Object.keys(payload).forEach((key) => {
        // @ts-ignore
        const value = payload[key];
        if (!['', undefined, null].includes(value)) {
          urlObject.searchParams.append(key, value);
        }
      });
    }
    return urlObject.href;
  } catch (error: any) {
    throw new RequestError(-1, error.message);
  }
};

// 在自定义对象 http 上添加各请求方法
const http: IHttp = {};
allMethods.forEach((method) => {
  Object.defineProperty(http, method, {
    get() {
      return async (url: string, payload: any, config: IFetchConfig = {}) => {
        const fetchConfig: IFetchConfig = getFetchConfig(method, payload, config);
        // 向 http header 注入 CSRFToken，CSRFToken key 值与后端一起协商制定
        const CSRFToken = cookie.parse(document.cookie)[window.BK_DASHBOARD_CSRF_COOKIE_NAME || `${window.BK_PAAS_APP_ID}_csrftoken`];
        if (CSRFToken !== undefined) {
          // @ts-ignore
          fetchConfig.headers['X-CSRFToken'] = CSRFToken;
        } else {
          console.warn('Can not find csrftoken in document.cookie');
          // return;
        }
        try {
          const fetchUrl = getFetchUrl(url, method, payload);
          // blob下载
          if (fetchConfig.responseType === 'blob') {
            return fetch(fetchUrl, fetchConfig);
          }
          const response = await fetch(fetchUrl, fetchConfig);
          return await successInterceptor(response, fetchConfig);
        } catch (err) {
          return errorInterceptor(err, fetchConfig);
        }
      };
    },
  });
});

export default http;
