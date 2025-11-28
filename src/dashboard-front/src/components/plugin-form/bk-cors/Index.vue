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
    class="mt-20px bk-cors-plugin-form"
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
import { cloneDeep, isEmpty, isObject } from 'lodash-es';
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

const getSchemaForm = () => {
  return schemaFieldRef.value?.comRef?.getFormData() ?? {};
};

const formRules = computed(() => ({
  allow_origins: [
    {
      message: t('format_bk_cors_allow_origins'),
      trigger: 'change',
      validator: (value: string) => {
        const allowOrigins = value || getSchemaForm().allow_origins || '';
        if (!allowOrigins) return true;
        const originRegexStr = '^(?:\\*|\\*\\*|null|https?:\\/\\/[-a-zA-Z0-9:\\[\\]\\.\\/\\?&=]+)(?:,\\s*https?:\\/\\/[-a-zA-Z0-9:\\[\\]\\.\\/\\?&=]+)*$';
        const originRegex = new RegExp(originRegexStr);
        return originRegex.test(allowOrigins);
      },
    },
  ],
  allow_origins_by_regex: [
    {
      message: t('allow_origins 与 allow_origins_by_regex 不能同时为空'),
      trigger: 'change',
      validator: () => {
        const { allow_origins, allow_origins_by_regex } = getSchemaForm();
        if (allow_origins.length < 1 && allow_origins_by_regex.length < 1) {
          return false;
        };
        return true;
      },
    },
  ],
  allow_methods: [
    {
      message: t('format_bk_cors_allow_methods'),
      trigger: 'change',
      validator: (value: string) => {
        const allowMethods = value || getSchemaForm().allow_methods || '';
        if (!allowMethods) return true;
        const methodRegex = /^(?:\*|\*\*|(?:GET|POST|PUT|DELETE|PATCH|HEAD|OPTIONS|CONNECT|TRACE)(?:,\s*(?:GET|POST|PUT|DELETE|PATCH|HEAD|OPTIONS|CONNECT|TRACE))*)$/;
        return methodRegex.test(allowMethods);
      },
    },
  ],
  allow_headers: [
    {
      message: t('format_bk_cors_allow_headers'),
      trigger: 'change',
      validator: (value: string) => {
        const allowHeaders = value || getSchemaForm().allow_methods || '';
        if (!allowHeaders) return true;
        const headersRegex = /^(\*|\*\*|[-a-zA-Z0-9]+(,[-a-zA-Z0-9]+)*)$/;
        return headersRegex.test(allowHeaders);
      },
    },
  ],
  allow_credential: [
    {
      message: t('format_bk_cors_allow_credential'),
      trigger: 'change',
      validator: () => {
        const {
          allow_origins,
          allow_methods,
          allow_headers,
          expose_headers,
          allow_credential,
        } = getSchemaForm();
        if (!allow_credential) return true;

        // allow_credential开启时, allow_origins、allow_methods, allow_headers、expose_header字段不能设置为*
        const fieldsToCheck = [
          allow_origins,
          allow_methods,
          allow_headers,
          expose_headers,
        ];
        const hasAsterisk = fieldsToCheck.some((field) => {
          if (typeof field === 'string') {
            return field === '*';
          }
          if (Array.isArray(field)) {
            return field.some(item => item.key === '*' || item === '*');
          }
          return false;
        });
        return !hasAsterisk;
      },
    },
  ],
}));

const handleAddItem = (row) => {
  clearValidate();
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
    const schemaForm = cloneDeep(getSchemaForm());
    const allowOriginsByRegex = schemaForm?.allow_origins_by_regex ?? [];
    // 单独处理下allowOriginsByRegex字段传给后端参数格式
    if (allowOriginsByRegex.length) {
      formData.value.allow_origins_by_regex = allowOriginsByRegex.map(item => item.key ?? '');
    }
    return isValid;
  }
  catch (err) {
    console.error('error', err);
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
    if (newVal?.allow_origins_by_regex?.length) {
      formData.value.allow_origins_by_regex = newVal.allow_origins_by_regex.map(key => ({ key }));
    }
  },
  { immediate: true },
);

defineExpose({
  validate,
  clearValidate,
});
</script>
