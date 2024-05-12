import type { IFetchConfig } from './index';
import { Message } from 'bkui-vue';
// import mitt from '@/common/event-bus';
import { showLoginModal } from '@blueking/login-modal';
// import { showLoginModal } from '@/common/auth';
const { BK_LOGIN_URL } = window;

// 请求执行失败拦截器
export default (errorData: any, config: IFetchConfig) => {
  const {
    status,
    error,
  } = errorData;
  const loginCallbackURL = `${window.BK_DASHBOARD_FE_URL}/static/login_success.html?is_ajax=1`;
  const siteLoginUrl = BK_LOGIN_URL || '';
  const loginUrl = `${BK_LOGIN_URL}?app_code=1&c_url=${encodeURIComponent(loginCallbackURL)}`;
  let iframeWidth = 400;
  let iframeHeight = 380;
  switch (status) {
    // 参数错误
    case 400:
      console.log('参数错误', error.message);
      break;
      // 用户登录状态失效
    case 401:
      console.log('401', error);
      // if (error?.data?.login_plain_url) {
      // const { width, height, login_url, login_plain_url } = error.data;
      //   mitt.emit('show-login-modal', {
      //     width,
      //     height,
      //     login_url,
      //     login_plain_url,
      //   });
      // } else {
      // 兼容本地开发后台没有重定向地址，直接跳转登录页
      //   window.location.href = `${BK_LOGIN_URL}/?c_url=${window.location.href}`;
      // }
      if (error?.data?.login_plain_url) {
        const { width, height } = error.data;
        iframeWidth = width;
        iframeHeight = height;
      }
      if (!siteLoginUrl) {
        console.error('Login URL not configured!');
        return;
      }
      // 增加encodeURIComponent防止回调地址特殊字符被转义
      showLoginModal({ loginUrl, width: iframeWidth, height: iframeHeight });
      break;
  }
  // 全局捕获错误给出提示
  if (config.globalError) {
    if (error.code !== 'UNAUTHENTICATED') {
      Message({ theme: 'error', message: error.message });
    }
  }
  return Promise.reject(error);
};
