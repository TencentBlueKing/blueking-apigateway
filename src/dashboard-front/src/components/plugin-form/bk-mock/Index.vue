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
    :rules="rules"
  >
    <BkFormItem
      :label="t('响应状态码')"
      property="response_status"
      required
    >
      <BkInput
        v-model="formData.response_status"
        :min="100"
        type="number"
      />
    </BkFormItem>
    <BkFormItem
      :label="t('响应体')"
      property="response_example"
    >
      <BkInput
        v-model="formData.response_example"
        :placeholder="t('请输入')"
        :rows="10"
        type="textarea"
      />
    </BkFormItem>
    <BkFormItem
      :label="t('响应头')"
      property="response_headers"
      :description="t('设置响应头')"
    >
      <KeyValuePairs
        ref="keyValueRef"
        v-model="formData.response_headers"
      />
    </BkFormItem>
  </BkForm>
</template>

<script lang="ts" setup>
import { cloneDeep } from 'lodash-es';
import KeyValuePairs from '@/components/plugin-form/api-breaker/components/KeyValuePairs.vue';

interface IFormData {
  response_status: number
  response_example: string
  response_headers: Array<{
    key: string
    value: string
  }>
}

interface IProps { data: IFormData }

const { data } = defineProps<IProps>();

const { t } = useI18n();

const formRef = useTemplateRef('formRef');
const keyValueRef = useTemplateRef('keyValueRef');

const getDefaultData = () => ({
  response_status: 200,
  response_example: '',
  response_headers: [],
});

const formData = ref<IFormData>(getDefaultData());

const rules = {};

watch(() => data, () => {
  if (data && Object.keys(data).length) {
    formData.value = cloneDeep(data);
  }
  else {
    formData.value = getDefaultData();
  }
}, {
  immediate: true,
  deep: true,
});

const validate = async () => {
  try {
    await formRef.value?.validate();
    await keyValueRef.value?.validate();
  }
  catch (error) {
    return Promise.reject(error);
  }
};

const getValue = () => validate()?.then(() => formData.value).catch(error => Promise.reject(error));

defineExpose({
  validate,
  getValue,
});

</script>

<style lang="scss" scoped>
</style>
