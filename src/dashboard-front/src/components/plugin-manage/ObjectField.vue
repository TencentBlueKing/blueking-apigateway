<template>
  <div class="object-field">
    <template
      v-for="(item, key) in schema.properties"
      :key="key"
    >
      <BkFormItem
        :label="item.title || key"
        :property="key"
        :rules="getRules(item, key)"
      >
        <SchemaField
          v-model="modelValue[key]"
          :schema="item"
          :component-map="componentMap"
          :disabled="disabled"
        />
      </BkFormItem>
    </template>
  </div>
</template>

<script setup lang="ts">
import SchemaField from './SchemaField.vue';

interface IProps {
  disabled?: boolean
  schema: any // JSON Schema 字段定义
  componentMap?: any // 自定义组件映射
}

const { disabled = false, componentMap = {} } = defineProps<IProps>();

// 初始化嵌套对象
if (!modelValue.value) {
  modelValue.value = {};
  // 初始化 required 字段
  props.schema.required?.forEach((key: string) => {
    modelValue.value[key] = props.schema.properties[key].default ?? '';
  });
}

// 校验规则
const getRules = (schema: any, key: string) => {
  const rules: any[] = [];
  // 必填项
  if (props.schema.required?.includes(key)) {
    rules.push({
      required: true,
      message: `请输入${schema.title || key}`,
      trigger: 'blur',
    });
  }
  // 自定义校验
  if (schema.pattern) {
    rules.push({
      pattern: new RegExp(schema.pattern),
      message: schema.description || `请输入正确的${schema.title}`,
      trigger: 'blur',
    });
  }
  return rules;
};
</script>

<style scoped>
.object-field {
  padding: 16px;
  border: 1px solid #ebeef5;
  border-radius: 4px;
}
</style>
