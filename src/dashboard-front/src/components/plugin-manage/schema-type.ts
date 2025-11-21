import { type Component } from 'vue';
import {
  // Checkbox,
  DatePicker,
  Input,
  Radio,
  Select,
  TimePicker,
} from 'bkui-vue';

// Schema 字段类型
export type SchemaType = 'string' | 'number' | 'boolean' | 'object' | 'array' | 'integer';

// 组件映射配置
export interface ComponentMap { [key in SchemaType]: Component }

// 默认组件映射
export const defaultComponentMap: ComponentMap = {
  string: () => Input,
  object: () => import('./ObjectField.vue'),
  array: () => import('./ArrayField.vue'),
};

// 扩展：根据 format 映射组件（如 date、time、select）
export const getComponentByFormat = (format?: string): Component | undefined => {
  switch (format) {
    case 'date':
      return DatePicker;
    case 'time':
      return TimePicker;
    case 'datetime':
      return DatePicker;
    case 'select':
      return Select;
    case 'radio':
      return Radio;
    default:
      return undefined;
  }
};
