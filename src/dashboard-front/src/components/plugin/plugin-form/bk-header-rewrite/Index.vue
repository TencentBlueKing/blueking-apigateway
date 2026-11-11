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
    :rules="formRules"
    :label-width="150"
    class="header-rewrite-form"
    @validate="handleValidate"
  >
    <BkFormItem
      :label="t('设置')"
      :description="t('设置的请求头')"
      property="set"
    >
      <KeyValuePairs
        ref="setRef"
        v-model="formData.set"
      />
    </BkFormItem>
    <BkFormItem
      :label="t('删除')"
      :description="t('删除的请求头')"
      property="remove"
    >
      <KeysInput
        ref="removeRef"
        v-model="formData.remove"
      />
    </BkFormItem>
  </BkForm>
</template>

<script setup lang="ts">
import { isPlainObject } from 'lodash-es';
import type { Form } from 'bkui-vue';
import KeyValuePairs from '@/components/plugin/plugin-form/components/KeyValuePairs.vue';
import KeysInput from '@/components/plugin/plugin-form/components/KeysInput.vue';

interface IHeaderPair {
  key: string
  value: string | number
}

interface IFormData {
  set: IHeaderPair[]
  remove: { key: string }[]
}

interface IProps {
  data: Record<string, any>
}

const { data } = defineProps<IProps>();

const { t } = useI18n();

const toSetList = (value: unknown): IHeaderPair[] => (Array.isArray(value) ? value : [])
  .filter(item => isPlainObject(item))
  .map(item => ({
    key: String(item.key ?? ''),
    value: item.value ?? '',
  }));

// 兼容只保存了键名字符串的旧数据
const toRemoveList = (value: unknown): { key: string }[] => (Array.isArray(value) ? value : [])
  .map(item => ({ key: String(isPlainObject(item) ? item.key ?? '' : item ?? '') }));

const formRef = ref<InstanceType<typeof Form>>();
const setRef = useTemplateRef('setRef');
const removeRef = useTemplateRef('removeRef');
const formData = ref<IFormData>({
  set: toSetList(data.set),
  remove: toRemoveList(data.remove),
});
const isRemoveValidated = ref(false);

const formRules = computed(() => ({
  remove: [
    {
      message: t('请求头设置或删除至少需要配置一个'),
      trigger: 'change',
      validator: () => formData.value.set.length > 0 || formData.value.remove.length > 0,
    },
  ],
}));

// 「至少配置一项」的提示展示在删除项下，增删任意一侧的行后同步刷新
watch(() => [formData.value.set.length, formData.value.remove.length], async () => {
  if (!isRemoveValidated.value) {
    return;
  }
  try {
    await formRef.value?.validate('remove');
  }
  catch {
    // 校验失败由表单项展示
  }
});

const handleValidate = (property: string) => {
  if (property === 'remove') {
    isRemoveValidated.value = true;
  }
};

const clearValidate = () => {
  isRemoveValidated.value = false;
  formRef.value?.clearValidate();
};

const getValue = async () => {
  await formRef.value?.validate();
  await Promise.all([
    setRef.value?.validate(),
    removeRef.value?.validate(),
  ]);
  return {
    set: formData.value.set.map(({ key, value }) => ({
      key,
      value,
    })),
    remove: formData.value.remove.map(({ key }) => ({ key })),
  };
};

defineExpose({
  getValue,
  clearValidate,
});
</script>

<style lang="scss" scoped>
.header-rewrite-form {
  --key-value-pairs-actions-padding-top: 8px;
}
</style>
