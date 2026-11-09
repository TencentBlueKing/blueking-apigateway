/*
 * TencentBlueKing is pleased to support the open source community by making
 * 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
 * Copyright (C) Tencent. All rights reserved.
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
      <RateLimitForm
        v-model="formData"
        :schema="schema?.properties?.rates?.properties?.default"
        :disabled="disabled"
        :layout="getLayout('default')"
      />

      <RateLimitForm
        v-model="formData"
        :schema="schema?.properties?.rates?.properties?.specials"
        :disabled="disabled"
        :layout="getLayout('specials')"
      />
    </div>
  </BkForm>
</template>

<script setup lang="ts">
import { cloneDeep, isEmpty, isObject } from 'lodash-es';
import { Form } from 'bkui-vue';
import type { IRateLimitFormData, ISchema } from '@/components/plugin/plugin-manage/schema-form/types';
import RateLimitForm from './components/RateLimitForm.vue';

interface IProps {
  schema?: ISchema
  disabled?: boolean
  // schema 编辑协议的公共入参，本表单不使用
  routeMode: string
  layout?: Record<string, any>
}

const formData = defineModel<IRateLimitFormData>('modelValue', {
  required: true,
  type: Object,
});

const {
  schema = {} as ISchema,
  layout = {} as Record<string, any>,
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

// 获取布局配置
const getLayout = (prop: string) => {
  const ratesLayout = layout?.[0]?.[0]?.group;
  return ratesLayout?.flat(1).find((item: any) => item.prop === prop)?.container || {};
};

const getValue = () => {
  return cloneDeep(formData.value);
};

const validate = async (): Promise<boolean> => {
  try {
    const isValid = await (formRef.value as any)?.validate();
    if (!isValid) {
      // @ts-ignore
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

watch(() => formData.value, (newVal: any) => {
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
