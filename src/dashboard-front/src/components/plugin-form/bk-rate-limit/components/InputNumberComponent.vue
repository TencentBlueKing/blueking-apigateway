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
  <BkFormItem
    :label="label"
    :label-width="labelWidth"
    :rules="rules"
    :required="required"
    :property="property"
  >
    <BkInput
      v-model.number="currentValue"
      type="number"
      :min="min"
      :precision="0"
      :step="1"
      :disabled="disabled"
      @input="handleInput"
    />
  </BkFormItem>
</template>

<script setup lang="ts">
interface IProps {
  property: string
  label?: string
  value?: number
  min?: number
  labelWidth?: number
  disabled?: boolean
  required?: boolean
  rules: Array<{
    required?: boolean
    message?: string
    trigger?: string
    validate?: () => boolean
  }>
}

interface IEmits {
  (e: 'input', value: number): void
  (e: 'update:value', value: number): void
}

const {
  label = '',
  labelWidth = 0,
  min = 1,
  value = 0,
  disabled = false,
  required = false,
} = defineProps<IProps>();

const emit = defineEmits<IEmits>();

const currentValue = ref(value ?? min ?? 1);

watch(() => value, (newVal) => {
  if (newVal) {
    currentValue.value = newVal;
  }
}, { immediate: true });

const handleInput = (val: number) => {
  emit('input', val);
  emit('update:value', val);
};
</script>
