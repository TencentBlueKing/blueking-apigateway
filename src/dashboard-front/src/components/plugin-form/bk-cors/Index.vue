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
import { getDuplicateKeys } from '@/utils/duplicateKeys';
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

// 是否同时存在allow_origins和allow_origins_regex
const isExistMultiAllowOrigin = () => {
  const { allow_origins, allow_origins_by_regex } = getSchemaForm();
  const allowOrigins = allow_origins?.trim();
  let isExistRegex = false;
  let duplicateList = [];
  if (Array.isArray(allow_origins_by_regex) && allow_origins_by_regex.length > 0) {
    isExistRegex = allow_origins_by_regex.some(item => item?.key !== '');
    if (allow_origins_by_regex?.length > 1) {
      duplicateList = getDuplicateKeys(allow_origins_by_regex, 'key');
    }
  }
  // 满足以下几种情况直接跳过校验
  // 1. allow_origins或者allow_origins_regex任意一项没值
  // 2. 子项表单校验失败则不需要校验
  // 3. allow_origins_by_regex存在重复的key
  if (!allowOrigins || !isExistRegex || duplicateList.length > 0) {
    return false;
  }
  return !!allowOrigins && isExistRegex;
};

const formRules = computed(() => ({
  allow_origins: [
    {
      message: t('format_bk_cors_allow_origins'),
      trigger: 'change',
      validator: (value: string) => {
        const { allow_origins } = getSchemaForm();
        const allowOrigins = value || allow_origins || '';
        if (!allowOrigins) return true;
        const originRegexStr = '^(?:\\*|\\*\\*|null|https?:\\/\\/[-a-zA-Z0-9:\\[\\]\\.\\/\\?&=]+)(?:,\\s*https?:\\/\\/[-a-zA-Z0-9:\\[\\]\\.\\/\\?&=]+)*$';
        const originRegex = new RegExp(originRegexStr);
        return originRegex.test(allowOrigins);
      },
    },
    {
      message: t('allow_origins 与 allow_origins_by_regex 只能一个有效'),
      trigger: 'change',
      validator: () => {
        const results = isExistMultiAllowOrigin();
        return !results;
      },
    },
  ],
  allow_origins_by_regex: [
    {
      message: t('allow_origins 与 allow_origins_by_regex 不能同时为空'),
      trigger: 'change',
      validator: () => {
        const { allow_origins, allow_origins_by_regex } = getSchemaForm();
        if (!allow_origins && allow_origins_by_regex?.length < 1) {
          return false;
        };
        return true;
      },
    },
    {
      message: t('allow_origins 与 allow_origins_by_regex 只能一个有效'),
      trigger: 'change',
      validator: () => {
        const results = isExistMultiAllowOrigin();
        return !results;
      },
    },
  ],
  allow_methods: [
    {
      message: t('format_bk_cors_allow_methods'),
      trigger: 'change',
      validator: (value: string) => {
        const { allow_methods } = getSchemaForm();
        const allowMethods = value || allow_methods || '';
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
        const { allow_headers } = getSchemaForm();
        const allowHeaders = value || allow_headers || '';
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

const getValue = () => {
  return cloneDeep(getSchemaForm());
};

const handleAddItem = (row) => {
  formData.value[row.name]?.push({ key: '' });
  formRef.value?.validate(row.name);
};

const handleRemoveItem = (row) => {
  const { field, index } = row;
  formData.value[field.name]?.splice(index, 1);
  formRef.value?.validate(row.name);
};

const validate = async (): Promise<boolean> => {
  try {
    const isValid = await formRef.value?.validate();
    if (!isValid) {
      return;
    }
    const schemaForm = getValue();
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
    if (Array.isArray(newVal?.allow_origins_by_regex)) {
      formData.value.allow_origins_by_regex = newVal.allow_origins_by_regex.map(item =>
        typeof item === 'string' ? { key: item } : (item || { key: '' }),
      );
    }
  },
  { immediate: true },
);

defineExpose({
  getValue,
  validate,
  clearValidate,
});
</script>

<style lang="scss" scoped>
:deep(.custom-plugin-form-wrapper) {

    >.is-error {

      .form-allow_origins_by_regex {

        ~ .bk-form-error {
          position: relative;
        }

        .custom-plugin-form-item {

          &:last-of-type {
            margin-bottom: 0;

            .bk-form-item {
              margin-bottom: 0;
            }

            .default-operate-btn {
              margin-bottom: 0;
            }
          }

          ~.default-operate-btn {
            margin-bottom: 0;
          }
        }

        &:has(.bk-form-item.is-error) {
          margin-bottom: 8px;

        ~ .bk-form-error {
          display: none;
        }
        }
      }
    }
}

:deep(.form-allow_origins_by_regex) {
  &:has(.bk-form-item.is-error) ~ .bk-form-error {
    display: none;
  }
}
</style>
