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
      :label="t('中断状态码')"
      property="abort.http_status"
      :description="t('返回给客户端的 HTTP 状态码')"
      required
    >
      <BkInput
        v-model="formData.abort.http_status"
        type="number"
      />
    </BkFormItem>
    <BkFormItem
      :label="t('中断响应体')"
      property="abort.body"
      :description="t('返回给客户端的响应数据。支持使用 NGINX 变量，如 client addr: $remote_addr')"
    >
      <BkInput
        v-model="formData.abort.body"
        :placeholder="t('请输入')"
        type="textarea"
        :rows="10"
      />
    </BkFormItem>
    <BkFormItem
      :label="t('中断请求占比')"
      property="abort.percentage"
      :description="t('将被中断的请求占比，0-100')"
    >
      <BkInput
        v-model="formData.abort.percentage"
        type="number"
        :min="0"
        :max="100"
      />
    </BkFormItem>
    <BkFormItem
      :label="t('中断规则')"
      property="abort.vars"
      :description="t('执行故障注入的规则，当规则匹配通过后才会执行故障注。vars 是一个表达式的列表，来自 lua-resty-expr。')"
    >
      <BkInput
        v-model="formData.abort.vars"
        :placeholder="t('请输入')"
        type="textarea"
        :rows="10"
      />
    </BkFormItem>
    <BkFormItem
      :label="t('延迟时间')"
      property="delay.duration"
      :description="t('延迟时间，单位秒，只能填入整数')"
    >
      <BkInput
        v-model="formData.delay.duration"
        type="number"
      />
    </BkFormItem>
    <BkFormItem
      :label="t('延迟请求占比')"
      property="delay.percentage"
      :description="t('将被延迟的请求占比，0-100')"
    >
      <BkInput
        v-model="formData.delay.percentage"
        type="number"
        :min="0"
        :max="100"
      />
    </BkFormItem>
    <BkFormItem
      :label="t('延迟规则')"
      property="delay.vars"
      :description="t('执行请求延迟的规则，当规则匹配通过后才会延迟请求。vars 是一个表达式列表，来自 lua-resty-expr。')"
    >
      <BkInput
        v-model="formData.delay.vars"
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
  abort: {
    http_status: number
    body: string
    percentage: number
    vars: string
  }
  delay: {
    duration: number
    percentage: number
    vars: string
  }
}

interface IProps { data: IFormData }

const { data } = defineProps<IProps>();

const { t } = useI18n();

const formRef = useTemplateRef('formRef');

const getDefaultData = () => ({
  abort: {
    http_status: 400,
    body: '',
    percentage: 0,
    vars: '',
  },
  delay: {
    duration: 0,
    percentage: 0,
    vars: '',
  },
});

const formData = ref<IFormData>(getDefaultData());

const rules = {};

watch(() => data, () => {
  if (data?.abort?.http_status) {
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
