/// <reference types="vite/client" />

interface ImportMetaEnv { readonly VITE_BK_DASHBOARD_FE_URL: string }

interface ImportMeta { readonly env: ImportMetaEnv }

declare module '*.css' {
  const css: string;
  export default css;
}

declare module '*.png' {
  const png: string;
  export default png;
}

declare module '*.js' {
  const js: string;
  export default js;
}

declare module '@blueking/notice-component';

declare module '@blueking/bkui-form';

declare module '@blueking/login-modal' {
  export function showLoginModal(params: { loginUrl: string }): void;
}

declare module '@blueking/release-note';

declare module '@blueking/xss-filter' {
  export const BkXssFilterDirective: any;
  export default function xssFilter(str: string): string;
}

declare module 'mavon-editor';

declare interface Window {
  BKANALYSIS?: { init: (params: { siteName: string }) => void }
  BK_DASHBOARD_URL: string
  BK_SITE_PATH: string
  BK_STATIC_URL: string
}

// eslint-disable-next-line
declare var BK_DASHBOARD_URL: string;
// eslint-disable-next-line
declare var BK_SITE_PATH: string;
// eslint-disable-next-line
declare var BK_STATIC_URL: string;

type CustomDirective = import('vue').Directive<HTMLElement, any>;
