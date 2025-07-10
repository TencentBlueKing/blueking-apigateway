import type { AxiosInterceptorManager, AxiosRequestConfig } from 'axios';

export default (interceptors: AxiosInterceptorManager<AxiosRequestConfig>) => {
  interceptors.use(request => request, undefined);
};
