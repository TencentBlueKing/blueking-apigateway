<template>
  <BkForm
    ref="formRef"
    :model="formData"
    :rules="rules"
    label-width="120px"
    @confirm="handleSubmit"
  >
    {{ formData }}
    <SchemaField
      v-model="formData"
      :schema="schema"
      :component-map="componentMap"
      :disabled="disabled"
    />
  </BkForm>
</template>

<script setup lang="ts">
// import { useAsyncValidator } from '@vueuse/async';
import SchemaField from './SchemaField.vue';

interface IProps {
  schema?: any
  componentMap?: any
  disabled?: boolean
}

const formData = defineModel('modelValue', {
  required: true,
  type: Object,
});
const {
  schema = {},
  componentMap = {},
  disabled = false,
} = defineProps<IProps>();

const formRef = ref(null);

const rules = computed(() => {
  // const validator = new useAsyncValidator(schema);
  return {};
});

const handleSubmit = async () => {
  if (!formRef.value) return;
  try {
    await formRef.value.validate();
    emit('submit', formData.value);
  }
  catch (error) {
    console.error('表单校验失败：', error);
  }
};
</script>
