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
  >
    <div class="schema-form-group grid gap-24px">
      <SchemaField
        ref="defaultSchemaFieldRef"
        v-model="formData"
        :schema="schema?.properties?.rates?.properties?.default"
        :component-map="componentMap"
        :route-mode="routeMode"
        :disabled="disabled"
        :layout="getLayout('default')"
        @update:model-value="updateDefault"
      />

      <SchemaField
        ref="specialsSchemaFieldRef"
        v-model="formData"
        :schema="schema?.properties?.rates?.properties?.specials"
        :component-map="componentMap"
        :route-mode="routeMode"
        :disabled="disabled"
        :layout="getLayout('specials')"
        @update:model-value="updateSpecials"
      />
    </div>
  </BkForm>
</template>

<script setup lang="ts">
import { cloneDeep, isEmpty, isObject } from 'lodash-es';
import { Form } from 'bkui-vue';
import type { IRateLimitFormData, ISchema } from '@/components/plugin-manage/schema-type';
import SchemaField from '@/components/plugin-manage/components/SchemaField.vue';

interface IProps {
  schema?: ISchema
  componentMap?: Record<string, Component>
  disabled?: boolean
  routeMode: string
  layout?: Record<string, any>
}

const formData = defineModel<IRateLimitFormData>('modelValue', {
  required: true,
  type: Object,
});

const {
  schema = {},
  layout = {},
  componentMap = {},
  disabled = false,
} = defineProps<IProps>();

const DEFAULT_FORM_DATA: IRateLimitFormData = reactive({
  rates: {
    default: {
      tokens: 100,
      period: 1,
    },
    specials: [],
  },
});

const formRef = ref<InstanceType<typeof Form> | null>(null);
const defaultSchemaFieldRef = ref<InstanceType<typeof SchemaField> | null>(null);
const specialsSchemaFieldRef = ref<InstanceType<typeof SchemaField> | null>(null); ;

// 获取布局配置
const getLayout = (prop: string) => {
  const ratesLayout = layout?.[0]?.[0]?.group;
  return ratesLayout?.flat(1).find(item => item.prop === prop)?.container || {};
};

// 更新默认限制数据
const updateDefault = (value: {
  tokens: number
  period: number
}) => {
  formData.value.rates.default = value;
};

// 更新特殊限制数据
const updateSpecials = (index: number, value: string | number) => {
  formData.value.rates.specials = formData.value.rates.specials.map((item, i) =>
    i === index ? value : item,
  );
};

const getValue = () => {
  return cloneDeep(formData.value);
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

watch(() => formData.value, (newVal) => {
  clearValidate();
  if (!isObject(newVal) || isEmpty(newVal)) {
    formData.value = { ...DEFAULT_FORM_DATA };
  }
}, { immediate: true });

defineExpose({
  getValue,
  validate,
  clearValidate,
});
</script>
