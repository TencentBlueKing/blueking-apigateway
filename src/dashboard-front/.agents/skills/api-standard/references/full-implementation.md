# 完整 Axios 封装实现

> 详细的代码实现和说明

## 标准封装代码 (`src/api/http.ts`)

```typescript
import axios, { type AxiosResponse, type InternalAxiosRequestConfig } from 'axios';
import { Message } from 'bkui-vue';

// --- 类型定义 ---

// 旧版响应结构
interface LegacyResponse<T = any> {
  code: number;
  result: boolean;
  message: string;
  data: T;
}

// 新版标准响应结构
interface StandardResponse<T = any> {
  data: T;
}

// 新版错误结构
interface StandardError {
  error: {
    code: string;
    message: string;
    system?: string;
    data?: any; // 可能包含权限申请数据等
    details?: any[];
  };
}

// --- 实例初始化 ---

const http = axios.create({
  baseURL: window.PROJECT_CONFIG?.API_URL || '/api',
  timeout: 60000,
  withCredentials: true,
  headers: {
    'X-Requested-With': 'XMLHttpRequest', // 标记 AJAX 请求，部分后端需要
  },
});

// --- 请求拦截器 ---

http.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    // 可以在这里注入 CSRF Token
    const token = getCookie('bk_token'); // 需自行实现 getCookie
    if (token) {
      // 蓝鲸网关通常要求 X-CSRFToken 或 Authorization
      // config.headers['X-CSRFToken'] = token;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// --- 响应拦截器 ---

http.interceptors.response.use(
  (response: AxiosResponse) => {
    const { data, status } = response;

    // [兼容逻辑] 判定是否为旧版协议 (存在 code 且不为 undefined)
    const isLegacyProtocol = data && typeof data.code !== 'undefined';

    // 场景 A: 旧版协议处理
    if (isLegacyProtocol) {
      const legacyData = data as LegacyResponse;
      if (legacyData.code !== 0) {
        // 业务错误
        const errorMessage = legacyData.message || '系统错误';

        // 特殊：旧版 401 (虽然状态码是 200，但 code 可能是 401 或特定值)
        if (legacyData.code === 401 || legacyData.code === 40100) {
          handleLoginRedirect(legacyData.data?.login_url);
          return Promise.reject(new Error('Login Expired'));
        }

        Message({ theme: 'error', message: errorMessage });
        return Promise.reject(new Error(errorMessage));
      }
      // 成功：剥壳返回 data
      return legacyData.data;
    }

    // 场景 B: 新版协议处理 (2xx 状态码)
    // 根据规范，正常响应体为 { data: ... }
    if (status >= 200 && status < 300) {
      return data.data !== undefined ? data.data : data;
    }

    return data;
  },
  (error) => {
    // 处理 HTTP 错误 (非 2xx) -> 主要是新版协议的错误处理
    const { response } = error;

    if (response) {
      const { status, data } = response;
      const errorBody = data as StandardError; // 尝试解析标准错误体

      // 优先使用后端返回的详细错误信息
      const serverMsg = errorBody?.error?.message;
      const serverCode = errorBody?.error?.code;

      // 1. 401 未登录
      if (status === 401) {
        const loginUrl = errorBody?.error?.data?.login_url;
        handleLoginRedirect(loginUrl);
        return Promise.reject(new Error('Login Expired'));
      }

      // 2. 403 无权限
      if (status === 403) {
        // 新版协议中，403 可能包含权限申请数据 (IAM_NO_PERMISSION)
        if (serverCode === 'IAM_NO_PERMISSION') {
           // TODO: 唤起权限申请弹窗 (需结合具体的权限组件)
           console.warn('需申请权限:', errorBody.error.data);
           Message({ theme: 'warning', message: '您没有访问权限，请申请。' });
           return Promise.reject(errorBody.error);
        }
      }

      // 3. 通用错误提示
      const displayMsg = serverMsg || getHttpErrorMessage(status);
      Message({ theme: 'error', message: displayMsg });
    } else {
      // 网络层面错误 (断网、超时)
      Message({ theme: 'error', message: error.message || '网络连接异常' });
    }

    return Promise.reject(error);
  }
);

// --- 辅助函数 ---

function handleLoginRedirect(backendLoginUrl?: string) {
  // 优先使用后端返回的登录地址，其次使用配置，最后兜底
  const loginUrl = backendLoginUrl
    || window.PROJECT_CONFIG?.LOGIN_URL
    || 'https://paas.bk.tencent.com/login/';

  // 避免死循环跳转
  if (window.location.href.startsWith(loginUrl)) return;

  const referer = window.location.href;
  window.location.href = `${loginUrl}?c_url=${encodeURIComponent(referer)}`;
}

function getHttpErrorMessage(status: number): string {
  const map: Record<number, string> = {
    400: '请求参数错误 (400)',
    403: '无权限访问 (403)',
    404: '资源不存在 (404)',
    500: '服务器内部错误 (500)',
    502: '网关错误 (502)',
    503: '服务不可用 (503)',
  };
  return map[status] || `请求异常 (${status})`;
}

// 简单的 Cookie 获取实现
function getCookie(name: string): string | null {
  const match = document.cookie.match(new RegExp('(^| )' + name + '=([^;]+)'));
  return match ? decodeURIComponent(match[2]) : null;
}

export default http;
```

## API 定义示例

在 `src/api/modules/` 下按模块定义 API：

```typescript
import http from '@/api/http';
import type { Host } from '@/types/host';

// 泛型参数：<ResponseData, ReturnData>
// 通常我们不关心 ResponseData (AxiosResponse)，只关心最终剥壳后的 ReturnData
export const getHosts = () => {
  return http.get<any, Host[]>('/api/v2/hosts');
};

export const createHost = (data: Partial<Host>) => {
  return http.post<any, Host>('/api/v2/hosts', data);
};

export const updateHost = (id: number, data: Partial<Host>) => {
  return http.put<any, Host>(`/api/v2/hosts/${id}`, data);
};

export const deleteHost = (id: number) => {
  return http.delete(`/api/v2/hosts/${id}`);
};
```

## 高级用法

### 自定义错误处理

```typescript
try {
  const data = await getHosts();
  // 处理数据
} catch (error) {
  // 自定义错误处理
  console.error('获取主机列表失败:', error);
}
```

### 请求/响应转换

```typescript
http.interceptors.request.use((config) => {
  // 统一添加时间戳防止缓存
  if (config.method === 'get') {
    config.params = {
      ...config.params,
      _t: Date.now()
    };
  }
  return config;
});
```

### Loading 状态管理

```typescript
import { ref } from 'vue';

const loading = ref(false);

export const getHostsWithLoading = async () => {
  loading.value = true;
  try {
    return await getHosts();
  } finally {
    loading.value = false;
  }
};
```
