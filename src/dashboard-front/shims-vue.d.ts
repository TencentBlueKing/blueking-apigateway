import type { Directive } from 'vue';

type CustomDirective = Directive<HTMLElement, any>;

declare module 'vue' {
  export interface ComponentCustomProperties {
    vBkTooltips: CustomDirective
    vBkOverflowTips: CustomDirective
    vBkXssHtml: CustomDirective
  }
}

declare module '@vue/runtime-dom' {
  export interface ComponentCustomProperties {
    'vBkTooltips': CustomDirective
    'vBkOverflowTips': CustomDirective
    'vBkXssHtml': CustomDirective
    'v-bk-tooltips'?: CustomDirective
    'v-bk-overflow-tips'?: CustomDirective
    'v-bk-xss-html'?: CustomDirective
  }
  export interface HTMLAttributes {
    'v-bk-tooltips'?: any
    'v-bk-overflow-tips'?: any
    'v-bk-xss-html'?: any
  }
}
