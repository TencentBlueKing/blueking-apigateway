import type { IFetchConfig } from './index';
import { Message } from 'bkui-vue';
import mitt from '@/common/event-bus';
// import { showLoginModal } from '@/common/auth';
const { BK_LOGIN_URL } = window;

// 请求执行失败拦截器
export default (errorData: any, config: IFetchConfig) => {
  const {
    status,
    error,
    response,
  } = errorData;
  const loginPlainUrl = response?.data?.data?.login_plain_url;
  switch (status) {
    // 参数错误
    case 400:
      console.log('参数错误', error.message);
      break;
    // 用户登录状态失效
    case 401:
      mitt.emit('show-login-modal', loginPlainUrl || `${BK_LOGIN_URL}/?c_url=${window.location.href}`);
      // window.location.href = `${BK_LOGIN_URL}/?c_url=${window.location.href}`;
      break;
  }
  // 全局捕获错误给出提示
  if (config.globalError) {
    Message({ theme: 'error', message: error.message });
  }
  return Promise.reject(error);
};
