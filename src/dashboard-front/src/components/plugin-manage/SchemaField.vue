<template>
  <Suspense>
    <template #default>
      <div>
        {{ curCom }}
        <component
          :is="curCom"
          v-model="fieldValue"
          v-bind="componentProps"
          @input="handleInput"
        />
      </div>
    </template>
    <template #fallback>
      <!-- 加载占位符 -->
      <div>加载中...</div>
    </template>
  </Suspense>
</template>

<script setup lang="ts">
import { defaultComponentMap, getComponentByFormat } from './schema-type';

interface IProps {
  disabled?: boolean
  schema: any // JSON Schema 字段定义
  componentMap?: any // 自定义组件映射
}
const modelValue = defineModel('modelValue', {
  required: true,
  type: Object,
});

// eslint-disable-next-line vue/define-props-destructuring
const props = defineProps<IProps>();

const emit = defineEmits<{ input: string }>();

const fieldValue = ref(modelValue.value);

// 组件映射
const componentsMap = {
  ...defaultComponentMap,
  ...props.componentMap,
};

const curCom = computed(() => {
  // 优先根据 format 匹配组件
  if (props.schema.format) {
    const formatComponent = getComponentByFormat(props.schema.format);
    if (formatComponent) return formatComponent;
  }
  // 否则根据 type 匹配
  console.log(componentsMap, props.schema);
  return componentsMap[props.schema?.type] || componentsMap.string;
});

// 组件属性
const componentProps = computed(() => {
  const { schema } = props;

  // 处理 string 类型
  if (schema.type === 'string') {
    props.type = schema.format || 'text';
    if (schema.pattern) props.pattern = schema.pattern;
    if (schema.maxLength) props.maxlength = schema.maxLength;
    if (schema.minLength) props.minlength = schema.minLength;
  }

  // 处理 number/integer 类型
  if (['number', 'integer'].includes(schema.type)) {
    if (schema.minimum !== undefined) props.min = schema.minimum;
    if (schema.maximum !== undefined) props.max = schema.maximum;
    if (schema.step !== undefined) props.step = schema.step;
  }

  // 处理 select/radio 类型（通过 enum 定义选项）
  if (schema.enum && ['select', 'radio'].includes(schema.format)) {
    props.options = schema.enum.map((value: any) => ({
      label: value,
      value,
    }));
    // radio 组件需要用 v-model 绑定字符串
    if (schema.format === 'radio') {
      props.modelValue = fieldValue.value;
      props['onUpdate:modelValue'] = (val: any) => {
        fieldValue.value = val;
      };
    }
  }

  // 处理 date/time 类型
  if (schema.format === 'date') {
    props.type = 'date';
    props.valueFormat = 'YYYY-MM-DD';
  }
  if (schema.format === 'time') {
    props.type = 'time';
    props.valueFormat = 'HH:mm:ss';
  }
  if (schema.format === 'datetime') {
    props.type = 'datetime';
    props.valueFormat = 'YYYY-MM-DD HH:mm:ss';
  }

  return props;
});

// 事件处理
const handleInput = (val: any) => {
  fieldValue.value = val;
  modelValue.value = val;
  emit('input', val);
};

watch(
  () => modelValue.value,
  (val) => {
    fieldValue.value = val;
  },
);
</script>

<style lang="scss" scoped>
.field-container {
  margin-bottom: 16px;
}
</style>
