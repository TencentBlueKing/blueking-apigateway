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
      v-for="(header, index) in internalValue"
      :key="index"
      ref="forms"
      :model="header"
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
              v-model="header.key"
              :maxlength="1024"
            />
            <div class="suffix-actions">
              <AgIcon
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

interface IProps { modelValue?: { key: string }[] }

const { modelValue = [] } = defineProps<IProps>();

const emit = defineEmits<{ 'update:modelValue': [{ key: string }[]] }>();

const { t } = useI18n();

const internalValue = ref<{ key: string }[]>([]);

const formRefs = useTemplateRef<InstanceType<typeof Form>[]>('forms');

const rules = {
  key: [
    {
      required: true,
      message: t('请输入键名'),
      trigger: 'blur',
    },
    {
      validator: (value: string) => /^[\w-]+$/.test(value),
      message: t('允许输入：字母、数字、下划线_、连字符-'),
      trigger: 'blur',
    },
    {
      validator: (value: string) => internalValue.value.filter(item => item.key === value).length <= 1,
      message: t('键名已存在'),
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
  internalValue.value.push({ key: '' });
};

const handleRemoveItem = (index: number) => {
  internalValue.value.splice(index, 1);
  nextTick(() => {
    validate();
  });
};

const validate = async () => {
  if (!formRefs.value) return true;

  try {
    await Promise.all(formRefs.value!.map(formRef => formRef.validate()));
    return true;
  }
  catch (error) {
    console.error(error);
    return false;
  }
};

const getValue = async () => {
  return Promise.resolve(internalValue.value?.filter(item => !!item.key) || []);
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
