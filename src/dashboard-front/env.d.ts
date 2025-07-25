/// <reference types="vite/client" />

interface ImportMetaEnv { readonly VITE_BK_DASHBOARD_FE_URL: string }

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

declare module '@blueking/release-note';

declare interface Window {
  BKANALYSIS?: { init: (params: { siteName: string }) => void }
  BK_DASHBOARD_FE_URL: string
}

declare global {
  var runtimeEnv: RuntimeEnv;
}

export type RuntimeEnv = { BK_DASHBOARD_FE_URL: string };
