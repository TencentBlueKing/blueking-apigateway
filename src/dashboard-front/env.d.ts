/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_BK_DASHBOARD_FE_URL: string
  readonly VITE_BK_API_RESOURCE_URL_TMPL: string
  readonly VITE_BK_APP_CODE: string
  readonly VITE_BK_COMPONENT_API_URL: string
  readonly VITE_BK_DASHBOARD_CSRF_COOKIE_NAME: string
  readonly VITE_BK_DASHBOARD_URL: string
  readonly VITE_BK_DEFAULT_TEST_APP_CODE: string
  readonly VITE_BK_PAAS_APP_REPO_URL_TMPL: string
  readonly VITE_BK_USER_WEB_API_URL: string
  readonly VITE_EDITION: string
  // 更多环境变量...
}

interface ImportMeta { readonly env: ImportMetaEnv }

declare module '*.css' {
  const css: string;
  export default css;
}

declare module '*.png' {
  const css: string;
  export default png;
}

declare module '*.js' {
  const css: string;
  export default js;
}

declare module '@blueking/notice-component';

declare module '@blueking/bkui-form';

declare module '@blueking/login-modal' {
  export function showLoginModal(params: { loginUrl: string }): void;
}

declare interface Window {
  APIGW_ENV: {
    BK_DASHBOARD_FE_URL: string
    BK_API_RESOURCE_URL_TMPL: string
    BK_APP_CODE: string
    BK_COMPONENT_API_URL: string
    BK_DASHBOARD_CSRF_COOKIE_NAME: string
    BK_DASHBOARD_URL: string
    BK_DEFAULT_TEST_APP_CODE: string
    BK_PAAS_APP_REPO_URL_TMPL: string
    BK_USER_WEB_API_URL: string
    EDITION: string
  }
}
