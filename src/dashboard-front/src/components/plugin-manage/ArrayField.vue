<!-- src/components/JsonSchemaForm/ArrayField.vue -->
<template>
  <div class="array-field">
    <div
      v-for="(item, index) in modelValue"
      :key="index"
      class="array-item"
    >
      <Field
        v-model="modelValue[index]"
        :schema="schema.items"
        :component-map="componentMap"
        :disabled="disabled"
      />
      <el-button
        type="text"
        icon="el-icon-delete"
        :disabled="disabled"
        @click="removeItem(index)"
      />
    </div>
    <el-button
      type="text"
      icon="el-icon-plus"
      :disabled="disabled"
      class="add-btn"
      @click="addItem()"
    >
      添加{{ schema.title }}
    </el-button>
  </div>
</template>

<script setup lang="ts">
import Field from './SchemaField.vue';

interface IProps {
  schema: any
  modelValue: any[]
  componentMap?: any
  disabled?: boolean
}

// 响应式处理
const modelValue = defineModel('modelValue', {
  required: true,
  type: Array,
});

const { disabled = false, componentMap = {} } = defineProps<IProps>();

interface IProps {
  disabled?: boolean
  schema: any // JSON Schema 字段定义
  componentMap?: any // 自定义组件映射
}

// 初始化数组
if (!modelValue.value) {
  modelValue.value = [];
  // 默认添加一个空项
  if (props.schema.minItems === undefined || props.schema.minItems > 0) {
    addItem();
  }
}

// 添加项
const addItem = () => {
  const defaultValue = props.schema.items.default ?? '';
  modelValue.value.push(defaultValue);
};

// 删除项
const removeItem = (index: number) => {
  modelValue.value.splice(index, 1);
};
</script>

<style scoped>
.array-item {
  display: flex;
  align-items: center;
  margin-bottom: 8px;
}
.add-btn {
  margin-top: 8px;
}
</style>
