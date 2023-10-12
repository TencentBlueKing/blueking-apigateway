import type { IFetchConfig } from './index';

interface IErrorInfo {
  status?: Number;
  error?: any
}

// 请求成功执行拦截器
export default async (response: any, config: IFetchConfig) => {
  const responseInfo =  await response[config.responseType]();
  if (response.ok) {
    const reg = RegExp(/20/);
    // 包含20x 代表请求成功
    if (reg.test(response.status)) {
      return Promise.resolve(responseInfo.data);
    }
    return Promise.reject(response);
  }
  // 处理 http 非 200 异常
  const errorInfo: IErrorInfo  = {
    status: response.status,
    error: responseInfo.error,
  };
  return Promise.reject(errorInfo);
};
