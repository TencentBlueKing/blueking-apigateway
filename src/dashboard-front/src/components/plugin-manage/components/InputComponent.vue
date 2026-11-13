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
  <BkFormItem
    :label="label"
    :label-width="labelWidth"
    :rules="rules"
    :required="required"
    :property="property"
  >
    <BkInput
      :model-value="currentValue"
      :disabled="disabled"
      :maxlength="max"
      :show-word-limit="showWordLimit"
      @input="!syncCommittedValue && emitValue($event)"
      @update:model-value="updateCurrentValue"
      @compositionend="handleCompositionEnd"
    />
  </BkFormItem>
</template>

<script setup lang="ts">
interface IProps {
  label?: string
  value?: string
  property: string
  disabled?: boolean
  required?: boolean
  showWordLimit?: boolean
  syncCommittedValue?: boolean
  max?: number
  labelWidth?: number
  rules?: Array<{
    required?: boolean
    message?: string
    trigger?: string
    validate?: () => boolean
  }>
}

const {
  label = '',
  value = '',
  labelWidth = 0,
  max = 4096,
  disabled = false,
  required = false,
  showWordLimit = false,
  syncCommittedValue = false,
  rules = [],
} = defineProps<IProps>();

const emit = defineEmits<{
  'input': [value: string]
  'update:value': [value: string]
}>();

const currentValue = shallowRef('');

watch(() => value, (newValue) => {
  if (syncCommittedValue || newValue) {
    currentValue.value = newValue;
  }
}, { immediate: true });

const emitValue = (newValue: string) => {
  emit('input', newValue);
  emit('update:value', newValue);
};

const updateCurrentValue = (newValue: string) => {
  if (newValue === currentValue.value) return;

  currentValue.value = newValue;
  if (syncCommittedValue) {
    emitValue(newValue);
  }
};

const handleCompositionEnd = (event: CompositionEvent) => {
  if (syncCommittedValue && event.target instanceof HTMLInputElement) {
    // Match BkInput's trimming when composition ends without a final input event.
    updateCurrentValue(event.target.value.trim());
  }
};
</script>
