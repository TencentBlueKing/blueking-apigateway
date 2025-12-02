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
    <BkFormItem :label="schema?.['ui:oneOf']?.title">
      <BkRadioGroup
        v-model="selectedOptionIndex"
        @change="handleOptionChange"
      >
        <BkRadio
          v-for="(option, index) in schema?.oneOf"
          :key="index"
          :label="index"
        >
          {{ option.title }}
        </BkRadio>
      </BkRadioGroup>
    </BkFormItem>

    <SchemaField
      ref="schemaFieldRef"
      v-model="formData"
      :schema="schema"
      :selected-schema="selectedSchema"
      :component-map="componentMap"
      :disabled="disabled"
    />
  </BkForm>
</template>

<script setup lang="ts">
import { cloneDeep } from 'lodash-es';
import { Form } from 'bkui-vue';
import { type ISchema } from '@/components/plugin-manage/schema-type';
import SchemaField from '@/components/plugin-manage/components/SchemaField.vue';

interface IProps {
  schema?: ISchema
  componentMap?: Record<string, Component>
  disabled?: boolean
  routeMode: string
}

interface IEmits { (e: 'update:modelValue', value: any): void }

const formData = defineModel('modelValue', {
  required: true,
  type: [Object, String],
});

const {
  schema = {},
  componentMap = {},
  disabled = false,
} = defineProps<IProps>();

const emit = defineEmits<IEmits>();

const { t } = useI18n();

const formRef = ref<InstanceType<typeof Form> | null>(null);

const schemaFieldRef = ref<InstanceType<typeof SchemaField> | null>(null);

const selectedOptionIndex = ref(0);

const selectedSchema = computed(() => {
  return schema?.oneOf?.[selectedOptionIndex.value];
});

const curSelectType = computed(() => {
  return Object.keys(selectedSchema.value?.properties ?? {})?.[0] ?? '';
});

const formRules = computed(() => {
  const schemaTitle = selectedSchema.value?.title ?? '';
  const requiredField = selectedSchema.value?.required;
  const minLength = Array.isArray(requiredField) && requiredField?.includes(curSelectType.value)
    ? selectedSchema.value?.properties?.[curSelectType.value]?.minLength
    : undefined;
  const commonRules = [
    {
      required: true,
      message: t('请输入{inputValue}', { inputValue: schemaTitle }),
      trigger: 'change',
      validator: (value: string) => {
        return !!value?.trim();
      },
    },
  ];

  const extraRules: any[] = [];
  if (minLength && typeof minLength === 'number' && minLength > 0) {
    extraRules.push({
      message: t('{inputValue}不应少于{count}个字符', {
        inputValue: schemaTitle,
        count: minLength,
      }),
      trigger: 'change',
      validator: (value: string) => {
        const trimmedValue = value?.trim() || '';
        return trimmedValue.length >= minLength;
      },
    });
  }

  const mergedRules = [...commonRules, ...extraRules];

  return {
    whitelist: mergedRules,
    blacklist: mergedRules,
  };
});

const getValue = () => {
  return cloneDeep(formData.value);
};

const validate = async () => {
  try {
    const isValid = await formRef.value?.validate(); ;
    if (!isValid) {
      schemaFieldRef.value?.comRef?.schemaFieldRef?.[0]?.comRef?.focus();
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

// 切换类型时重置模型值
const handleOptionChange = () => {
  clearValidate();
  emit('update:modelValue', {});
};

watch(
  () => formData.value,
  (newVal) => {
    clearValidate();
    if (newVal?.whitelist) selectedOptionIndex.value = 0;
    if (newVal?.blacklist) selectedOptionIndex.value = 1;
  },
  { immediate: true },
);

defineExpose({
  getValue,
  validate,
  clearValidate,
});
</script>
