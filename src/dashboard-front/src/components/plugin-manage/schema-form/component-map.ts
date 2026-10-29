import { defineAsyncComponent } from 'vue';
import { Checkbox, Input } from 'bkui-vue';
import type { ComponentMap } from './types';

// 默认组件映射
export const defaultComponentMap: ComponentMap = {
  'string': () => ({
    component: Input,
    props: { type: 'text' },
  }),
  'number': () => ({
    component: Input,
    props: { type: 'number' },
  }),
  'integer': () => ({
    component: Input,
    props: { type: 'number' },
  }),
  'boolean': ({
    component: Checkbox,
    props: {},
  }),
  'object': defineAsyncComponent(() => import('./components/SchemaObjectField.vue')),
  'array': defineAsyncComponent(() => import('./components/SchemaObjectField.vue')),
  'bk-cors': defineAsyncComponent(() => import('./components/CustomAddDelForm.vue')),
  'bk-header-rewrite': defineAsyncComponent(() => import('./components/CustomAddDelForm.vue')),
  'bk-rate-limit': defineAsyncComponent(() => import('@/components/plugin-form/bk-rate-limit/components/RateLimitForm.vue')),
};
