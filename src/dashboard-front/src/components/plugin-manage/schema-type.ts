import { type Component, defineAsyncComponent } from 'vue';

import {
  Checkbox,
  Input,
} from 'bkui-vue';

export type ComponentItem = | Component | (() => {
  component: Component
  props: Record<string, any>
});

// Schema 字段类型
export type SchemaType = 'string' | 'number' | 'boolean' | 'object' | 'array' | 'integer' | 'bk-cors' | 'bk-header-rewrite' | 'bk-rate-limit';

// 组件映射配置
export type ComponentMap = Record<SchemaType, Component>;

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
  'object': defineAsyncComponent(() => import('@/components/plugin-manage/components/SchemaObjectField.vue')),
  'array': defineAsyncComponent(() => import('@/components/plugin-manage/components/SchemaObjectField.vue')),
  'bk-cors': defineAsyncComponent(() => import('@/components/plugin-manage/components/CustomAddDelForm.vue')),
  'bk-header-rewrite': defineAsyncComponent(() => import('@/components/plugin-manage/components/CustomAddDelForm.vue')),
  'bk-rate-limit': defineAsyncComponent(() => import('@/components/plugin-form/bk-rate-limit/components/RateLimitForm.vue')),
};

// 以下就是Schema各种插件配置声明
export interface ISchema {
  'type': 'string' | 'number' | 'object' | 'array' | 'integer' | 'boolean'
  'format'?: 'date' | 'time' | 'datetime' | 'select' | 'radio' | 'email' | 'url' | 'ipv4' | 'ipv6'
  'title'?: string
  'description'?: string
  'ui:oneOf'?: { title?: string }
  'oneOf'?: Array<{
    title?: string
    required?: string[]
    properties?: Record<string, any>
    type?: SchemaType
    format?: string
  }>
  'enum'?: any[]
  'minimum'?: number
  'maximum'?: number
  'minLength'?: number
  'maxLength'?: number
  'pattern'?: string
  'properties'?: Record<string, ISchema>
  'items'?: {
    properties?: {
      [key: string]: {
        title?: string
        pattern?: string
        maxLength?: number
      }
    }
  }
  'required'?: string[]
  'ui:group'?: {
    showTitle?: boolean
    type?: string
    style?: Record<string, string>
  }
  'ui:component'?: {
    name: string
    datasource?: {
      label: string
      value: string
    }[]
    min?: number
    clearable?: boolean
  }
  'ui:rules'?: string[]
  'ui:props'?: { labelWidth?: number }
  'default'?: Record<string, unknown>
}

export interface IHeaderWriteFormData {
  set?: Array<{
    key: string
    value: string
  }>
  remove?: Array<{ key: string }>
}

export interface IRateLimitFormData {
  rates: {
    default: {
      tokens: number
      period: number
    }
    specials: Array<{
      tokens: number
      period: number
      bk_app_code: string
    }>
  }
}

export interface ICorsFormData {
  allow_origins_by_regex: string[]
  allow_origins: string
  allow_methods: string
  allow_headers: string
  expose_headers: string
  max_age: number
  allow_credential: boolean
}
