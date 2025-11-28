/*
 * TencentBlueKing is pleased to support the open source community by making
 * 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
 * Copyright (C) 2025 Tencent. All rights reserved.
 * Licensed under the MIT License (the "License"); you may not use this file except
 * in compliance with the License. You may obtain a copy of the License at
 *
 *     http://opensource.org/licenses/MIT
 *
 * Unless required by applicable law or agreed to in writing, software distributed under
 * the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND,
 * either express or implied. See the License for the specific language governing permissions and
 * limitations under the License.
 *
 * We undertake not to change the open source license (MIT license) applicable
 * to the current version of the project delivered to anyone in the future.
 */
<template>
  <BkForm
    ref="formRef"
    :model="formData"
    :rules="formRules"
  >
    <SchemaField
      ref="schemaFieldRef"
      v-model="formData"
      :schema="schema"
      :component-map="componentMap"
      :route-mode="routeMode"
      :disabled="disabled"
      @add="handleAddItem"
      @remove="handleRemoveItem"
    />
  </BkForm>
</template>

<script setup lang="ts">
import { isEmpty, isObject } from 'lodash-es';
import { Form } from 'bkui-vue';
import type { IHeaderWriteFormData, ISchema } from '@/components/plugin-manage/schema-type';
import SchemaField from '@/components/plugin-manage/components/SchemaField.vue';

interface IProps {
  schema?: ISchema
  componentMap?: Record<string, Component>
  disabled?: boolean
  routeMode: string
}

const formData = defineModel('modelValue', {
  required: true,
  type: Object,
  default: () => {
    return {
      set: [],
      remove: [],
    };
  },
});

const {
  schema = {},
  componentMap = {},
  disabled = false,
} = defineProps<IProps>();

const DEFAULT_FORM_DATA: IHeaderWriteFormData = reactive({
  set: [],
  remove: [],
});

const formRef = ref<InstanceType<typeof Form> | null>(null);

const schemaFieldRef = ref<InstanceType<typeof SchemaField> | null>(null);

const formRules = computed(() => ({
  remove: [
    {
      required: true,
      message: schema?.properties?.set?.['ui:rules']?.[0]?.message,
      trigger: 'change',
      validator: () => {
        const isExistSet = formData.value.set?.length > 0;
        const isExistRemove = formData.value.remove?.length > 0;
        if (!isExistSet && !isExistRemove) {
          return false;
        }
        return true;
      },
    },
  ],
}));

const handleAddItem = (row) => {
  const typeMap = {
    set: () => {
      formData.value[row.name]?.push({
        key: '',
        value: '',
      });
    },
    remove: () => {
      formData.value[row.name]?.push({ key: '' });
    },
  };
  return typeMap[row?.name]?.();
};

const handleRemoveItem = (row) => {
  const { field, index } = row;
  formData.value[field.name]?.splice(index, 1);
};

const validate = async () => {
  try {
    const isValid = await formRef.value?.validate();
    if (!isValid) {
      return;
    }
    return isValid;
  }
  catch {
    return false;
  }
};

const clearValidate = () => {
  return formRef.value?.clearValidate();
};

watch(
  () => formData.value,
  (newVal) => {
    clearValidate();
    if (isObject(newVal) && isEmpty(newVal)) {
      formData.value = { ...DEFAULT_FORM_DATA };
    }
  },
  { immediate: true },
);

defineExpose({
  validate,
  clearValidate,
});
</script>
