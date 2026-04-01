/**
 * 统一 HTTP 请求封装
 * 基于 Axios，包含拦截器、错误处理、Loading 状态管理
 */

import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse } from 'axios';
import { Message } from 'bkui-vue';

// 响应数据结构
interface ApiResponse<T = any> {
  code: number;
  data: T;
  message: string;
}

// 请求配置扩展
interface RequestConfig extends AxiosRequestConfig {
  // 是否显示全局 Loading
  showLoading?: boolean;
  // 是否显示错误提示
  showError?: boolean;
  // 自定义错误处理
  handleError?: boolean;
}

// 创建实例
const createInstance = (): AxiosInstance => {
  const instance = axios.create({
    baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
    timeout: 30000,
    headers: {
      'Content-Type': 'application/json'
    }
  });

  // 请求拦截器
  instance.interceptors.request.use(
    (config) => {
      // 注入认证 Token
      const token = localStorage.getItem('token');
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
      return config;
    },
    (error) => Promise.reject(error)
  );

  // 响应拦截器
  instance.interceptors.response.use(
    (response: AxiosResponse<ApiResponse>) => {
      const { code, data, message } = response.data;

      // 业务成功
      if (code === 0) {
        return data;
      }

      // 业务错误
      const error = new Error(message || '请求失败');
      (error as any).code = code;
      return Promise.reject(error);
    },
    (error) => {
      // HTTP 错误处理
      const status = error.response?.status;
      let message = '网络错误，请稍后重试';

      if (status === 401) {
        message = '登录已过期，请重新登录';
        // TODO: 跳转登录页
      } else if (status === 403) {
        message = '没有权限访问该资源';
      } else if (status === 404) {
        message = '请求的资源不存在';
      } else if (status >= 500) {
        message = '服务器错误，请稍后重试';
      }

      error.message = message;
      return Promise.reject(error);
    }
  );

  return instance;
};

const http = createInstance();

// 封装请求方法
export const request = async <T = any>(config: RequestConfig): Promise<T> => {
  const { showError = true, ...axiosConfig } = config;

  try {
    const result = await http.request<any, T>(axiosConfig);
    return result;
  } catch (error: any) {
    if (showError) {
      Message({
        theme: 'error',
        message: error.message || '请求失败'
      });
    }
    throw error;
  }
};

// 便捷方法
export const get = <T = any>(url: string, params?: any, config?: RequestConfig) =>
  request<T>({ ...config, method: 'GET', url, params });

export const post = <T = any>(url: string, data?: any, config?: RequestConfig) =>
  request<T>({ ...config, method: 'POST', url, data });

export const put = <T = any>(url: string, data?: any, config?: RequestConfig) =>
  request<T>({ ...config, method: 'PUT', url, data });

export const del = <T = any>(url: string, config?: RequestConfig) =>
  request<T>({ ...config, method: 'DELETE', url });

export default http;
