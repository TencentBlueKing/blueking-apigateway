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
  <div>
    <BkForm
      v-for="(code, index) in internalValue"
      :key="index"
      ref="forms"
      :model="{key: code}"
      :rules="rules"
      v-bind="$attrs"
    >
      <BkFormItem
        :class="{ 'mb-0px': internalValue?.length > 1 && index === internalValue.length - 1 }"
        class="form-item w-630px"
        property="key"
      >
        <div class="multi-line-wrapper">
          <section class="multi-line-item has-suffix">
            <BkInput
              v-model="internalValue[index]"
              type="number"
              :min="min"
              :max="max"
            />
            <div class="suffix-actions">
              <AgIcon
                v-if="internalValue.length > 1"
                class="icon-btn cursor-pointer"
                color="#979BA5"
                name="minus-circle-shape"
                size="18"
                @click="() => handleRemoveItem(index)"
              />
              <AgIcon
                v-if="index === internalValue.length - 1"
                class="icon-btn cursor-pointer"
                color="#979BA5"
                name="plus-circle-shape"
                size="18"
                @click="handleAddItem"
              />
            </div>
          </section>
        </div>
      </BkFormItem>
    </BkForm>
    <AgIcon
      v-if="internalValue?.length === 0"
      class="icon-btn"
      color="#979BA5"
      name="plus-circle-shape"
      size="18"
      @click="handleAddItem"
    />
  </div>
</template>

<script lang="ts" setup>
import { Form } from 'bkui-vue';
import { cloneDeep } from 'lodash-es';

interface IProps {
  modelValue?: number[]
  min?: number
  max?: number
  defaultVal?: number
}

const { modelValue = [], min = 0, max = 999, defaultVal = 0 } = defineProps<IProps>();

const emit = defineEmits<{ 'update:modelValue': [number[]] }>();

const { t } = useI18n();

const internalValue = ref<number[]>([]);

const formRefs = useTemplateRef<InstanceType<typeof Form>[]>('forms');

const rules = {
  key: [
    {
      validator: (value: number) => internalValue.value.filter(item => item === value).length <= 1,
      message: t('状态码已存在'),
      trigger: 'blur',
    },
  ],
};

watch(
  () => modelValue,
  (newVal) => {
    if (JSON.stringify(newVal) !== JSON.stringify(internalValue.value)) {
      internalValue.value = newVal.length > 0 ? cloneDeep(newVal) : [];
    }
  },
  {
    immediate: true,
    deep: true,
  },
);

watch(internalValue, (newVal) => {
  emit('update:modelValue', newVal);
}, { deep: true });

const handleAddItem = () => {
  internalValue.value.push(defaultVal || 0);
};

const handleRemoveItem = (index: number) => {
  internalValue.value.splice(index, 1);
  nextTick(() => {
    validate();
  });
};

const validate = async () => {
  if (!formRefs.value) return Promise.resolve(true);

  try {
    await Promise.all(formRefs.value!.map(formRef => formRef.validate()));
    return Promise.resolve(true);
  }
  catch (error) {
    return Promise.reject(error);
  }
};

const getValue = () => {
  return internalValue.value || [];
};

defineExpose({
  validate,
  getValue,
});

</script>

<style lang="scss" scoped>

.multi-line-wrapper {
  display: flex;
  flex-direction: column;
  gap: 12px;

  .multi-line-item {
    display: flex;
    align-items: center;
    gap: 6px;
  }
}

.has-suffix {
  position: relative;

  .suffix-actions {
    position: absolute;
    right: -12px;
    display: flex;
    align-items: center;
    transform: translateX(100%);
    gap: 12px;
  }
}

.form-item {

  :deep(.bk-form-error) {
    position: relative;
  }
}

</style>
