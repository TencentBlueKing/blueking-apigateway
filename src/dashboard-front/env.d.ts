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

declare module '@blueking/platform-config' {
  // 需要国际化的字段，根据 blueking_language cookie 自动匹配
  export interface IPlatformConfigI18n {
    name?: string
    productName?: string
    helperText?: string
    brandImg?: string
    brandName?: string
    footerInfoHTML?: string
  }

  export interface IPlatformConfig {
    bkAppCode?: string
    name?: string
    nameEn?: string
    appLogo?: string
    favicon?: string
    productName?: string
    productNameEn?: string
    helperText?: string
    helperTextEn?: string
    helperLink?: string
    brandImg?: string
    brandImgEn?: string
    brandName?: string
    brandNameEn?: string
    // 页脚内容，仅支持 a 的 markdown 格式
    footerInfo?: string
    footerInfoEn?: string
    // 版权信息，支持 {{version}} 变量
    footerCopyright?: string
    version?: string
    // 以下字段由 getPlatformConfig 处理后附加
    footerInfoHTML?: string
    footerInfoHTMLEn?: string
    footerCopyrightContent?: string
    i18n?: IPlatformConfigI18n
  }

  export function getPlatformConfig(defaults: IPlatformConfig): Promise<IPlatformConfig>;
  export function getPlatformConfig(url: string, defaults?: IPlatformConfig): Promise<IPlatformConfig>;
  export function getI18nValue(config: IPlatformConfig, key: string, lang?: string): string | undefined;
  export function setDocumentTitle(i18n?: IPlatformConfigI18n, extra?: string | string[]): void;
  export function setShortcutIcon(url?: string): void;
  export const titleSeparator: string;
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
