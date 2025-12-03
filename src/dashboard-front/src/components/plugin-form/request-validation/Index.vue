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
      :label="t('请求体 JSON Schema')"
      property="body_schema"
      :description="t('request body 数据的 JSON Schema')"
      required
    >
      <BkInput
        v-model="formData.body_schema"
        :placeholder="t('请输入')"
        type="textarea"
        :maxlength="51200"
        :rows="10"
      />
    </BkFormItem>
    <BkFormItem
      :label="t('请求头 JSON Schema')"
      property="header_schema"
      :description="t('request header 数据的 JSON Schema')"
      required
    >
      <BkInput
        v-model="formData.header_schema"
        :placeholder="t('请输入')"
        type="textarea"
        :maxlength="51200"
        :rows="10"
      />
    </BkFormItem>
    <BkFormItem
      :label="t('拒绝状态码')"
      property="rejected_code"
    >
      <BkInput
        v-model="formData.rejected_code"
        type="number"
        :min="200"
      />
    </BkFormItem>
    <BkFormItem
      :label="t('拒绝信息')"
      property="rejected_msg"
    >
      <BkInput
        v-model="formData.rejected_msg"
        :placeholder="t('请输入')"
        type="textarea"
        :rows="10"
      />
    </BkFormItem>
  </BkForm>
</template>

<script lang="ts" setup>
import { cloneDeep } from 'lodash-es';

interface IFormData {
  body_schema: string
  header_schema: string
  rejected_code: number
  rejected_msg: string
}

interface IProps { data: IFormData }

const { data } = defineProps<IProps>();

const { t } = useI18n();

const formRef = useTemplateRef('formRef');

const getDefaultData = () => ({
  body_schema: '',
  header_schema: '',
  rejected_code: 400,
  rejected_msg: '',
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
