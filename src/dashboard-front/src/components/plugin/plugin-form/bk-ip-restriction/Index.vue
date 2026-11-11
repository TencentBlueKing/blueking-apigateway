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
    <BkFormItem :label="t('类型')">
      <BkRadioGroup
        v-model="listType"
        @change="handleTypeChange"
      >
        <BkRadio
          v-for="option in typeOptions"
          :key="option.value"
          :label="option.value"
        >
          {{ option.label }}
        </BkRadio>
      </BkRadioGroup>
    </BkFormItem>
    <BkFormItem
      :key="listType"
      :label="currentLabel"
      :property="listType"
      :rules="listRules"
      required
    >
      <BkInput
        v-model="formData[listType]"
        type="textarea"
        :rows="10"
        :maxlength="51200"
        :placeholder="t('请输入{inputValue}', { inputValue: currentLabel })"
      />
    </BkFormItem>
  </BkForm>
</template>

<script setup lang="ts">
import type { Form } from 'bkui-vue';

type ListType = 'whitelist' | 'blacklist';

interface IProps {
  data: Record<string, any>
}

const { data } = defineProps<IProps>();

const { t } = useI18n();

// 与后端 schema 的 minLength 保持一致，最短的合法 IP 如 1.1.1.1
const MIN_LENGTH = 7;

const formRef = ref<InstanceType<typeof Form>>();
// 白名单和黑名单分别保留草稿，切换类型时不丢失已填写的内容
const formData = ref<Record<ListType, string>>({
  whitelist: typeof data.whitelist === 'string' ? data.whitelist : '',
  blacklist: typeof data.blacklist === 'string' ? data.blacklist : '',
});
const listType = ref<ListType>(!data.whitelist && data.blacklist ? 'blacklist' : 'whitelist');

const typeOptions = computed(() => [
  {
    label: t('白名单'),
    value: 'whitelist',
  },
  {
    label: t('黑名单'),
    value: 'blacklist',
  },
]);

const currentLabel = computed(() => listType.value === 'whitelist' ? t('白名单') : t('黑名单'));

const listRules = computed(() => [
  {
    required: true,
    message: t('请输入{inputValue}', { inputValue: currentLabel.value }),
    trigger: 'change',
    validator: (value: string) => !!value?.trim(),
  },
  {
    message: t('{inputValue}不应少于{count}个字符', {
      inputValue: currentLabel.value,
      count: MIN_LENGTH,
    }),
    trigger: 'change',
    validator: (value: string) => (value?.trim() ?? '').length >= MIN_LENGTH,
  },
]);

const clearValidate = () => {
  formRef.value?.clearValidate();
};

const handleTypeChange = () => {
  clearValidate();
};

const getValue = async () => {
  await formRef.value?.validate();
  // 只提交当前选中的类型
  return { [listType.value]: formData.value[listType.value] };
};

defineExpose({
  getValue,
  clearValidate,
});
</script>
