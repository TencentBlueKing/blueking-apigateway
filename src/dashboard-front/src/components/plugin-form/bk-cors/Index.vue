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
    class="mt-20px"
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
import type { ICorsFormData, ISchema } from '@/components/plugin-manage/schema-type';
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
});

const {
  schema = {},
  componentMap = {},
  disabled = false,
} = defineProps<IProps>();

const { t } = useI18n();

const DEFAULT_FORM_DATA: ICorsFormData = reactive({
  allow_origins: '',
  allow_origins_by_regex: [],
  allow_methods: '**',
  allow_headers: '**',
  expose_headers: '',
  max_age: 86400,
  allow_credential: true,
});

const formRef = ref<InstanceType<typeof Form> | null>(null);

const schemaFieldRef = ref<InstanceType<typeof SchemaField> | null>(null);

const formRules = computed(() => ({
  allow_origins: [
    {
      message: t('format_bk_cors_allow_origins'),
      trigger: 'change',
      validator: () => {
        const originRegex = /^(|\*|\*\*|null|http(s)?:\/\/[-a-zA-Z0-9:\[\]\.]+(,http(s)?:\/\/[-a-zA-Z0-9:\[\]\.]+)*)$/;
        const fieldData = schemaFieldRef.value?.comRef?.getFormData();
        const allowOrigins = fieldData?.allow_origins;
        if (!allowOrigins) return true;
        return originRegex.test(allowOrigins);
      },
    },
  ],
  allow_methods: [
    {
      message: t('format_bk_cors_allow_headers'),
      trigger: 'change',
      validator: () => {
        const fieldData = schemaFieldRef.value?.comRef?.getFormData();
        const allowMethods = fieldData?.allow_methods;
        if (!allowMethods) return true;
        const methodRegex = /^(\*|\*\*|(GET|POST|PUT|DELETE|PATCH|HEAD|OPTIONS|CONNECT|TRACE)(,(GET|POST|PUT|DELETE|PATCH|HEAD|OPTIONS|CONNECT|TRACE))*)$/;
        return methodRegex.test(formData.value.allow_methods);
      },
    },
  ],
  allow_headers: [
    {
      message: t('format_bk_cors_allow_methods'),
      trigger: 'change',
      validator: () => {
        const fieldData = schemaFieldRef.value?.comRef?.getFormData();
        const allowMethods = fieldData?.allow_headers;
        if (!allowMethods) return true;
        const headersRegex = /^(\*|\*\*|[-a-zA-Z0-9]+(,[-a-zA-Z0-9]+)*)$/;
        return headersRegex.test(formData.value.allow_headers);
      },
    },
  ],
}));

const handleAddItem = (row) => {
  formData.value[row.name]?.push({ key: '' });
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

<style lang="scss" scoped>
:deep(.bk-form-error) {
  position: relative;
}
</style>
