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
      :label="t('熔断响应状态码')"
      property="break_response_code"
      required
      :description="t('当上游服务处于不健康状态时返回的 HTTP 错误码。')"
    >
      <BkInput
        v-model="formData.break_response_code"
        type="number"
      />
    </BkFormItem>
    <BkFormItem
      :label="t('熔断响应体')"
      property="break_response_body"
      :description="t('当上游服务处于不健康状态时返回的 HTTP 响应体信息。')"
    >
      <BkInput
        v-model="formData.break_response_body"
        :placeholder="t('请输入')"
        type="textarea"
        :rows="10"
      />
    </BkFormItem>
    <BkFormItem
      :label="t('熔断响应头')"
      property="break_response_headers"
      :description="t('当上游服务处于不健康状态时返回的 HTTP 响应头信息。')"
    >
      <KeyValuePairs
        ref="keyValueRef"
        v-model="formData.break_response_headers"
      />
    </BkFormItem>
    <BkFormItem
      :label="t('最大熔断时间')"
      property="max_breaker_sec"
      :description="t('上游服务熔断的最大持续时间，以秒为单位，最小 3 秒。')"
    >
      <BkInput
        v-model="formData.max_breaker_sec"
        type="number"
        :min="3"
      />
    </BkFormItem>
    <BkFormItem
      :label="t('不健康状态码')"
      property="unhealthy.http_statuses"
      :description="t('上游服务处于不健康状态时的 HTTP 状态码。')"
    >
      <StatusCodes
        ref="unhealthyStatusCodesRef"
        v-model="formData.unhealthy.http_statuses"
        :min="500"
        :max="599"
        :default-val="503"
      />
    </BkFormItem>
    <BkFormItem
      :label="t('不健康次数')"
      property="unhealthy.failures"
      :description="t('上游服务在一定时间内触发不健康状态的异常请求次数')"
    >
      <BkInput
        v-model="formData.unhealthy.failures"
        type="number"
        :min="1"
      />
    </BkFormItem>
    <BkFormItem
      :label="t('健康状态码')"
      property="healthy.http_statuses"
      :description="t('上游服务处于健康状态时的 HTTP 状态码。')"
    >
      <StatusCodes
        ref="healthyStatusCodesRef"
        v-model="formData.healthy.http_statuses"
        :min="200"
        :max="499"
        :default-val="200"
      />
    </BkFormItem>
    <BkFormItem
      :label="t('健康次数')"
      property="healthy.successes"
      :description="t('上游服务触发健康状态的连续正常请求次数。')"
    >
      <BkInput
        v-model="formData.healthy.successes"
        :placeholder="t('请输入')"
        type="number"
        :min="1"
      />
    </BkFormItem>
  </BkForm>
</template>

<script lang="ts" setup>
import { cloneDeep } from 'lodash-es';
import KeyValuePairs from '@/components/plugin-form/api-breaker/components/KeyValuePairs.vue';
import StatusCodes from '@/components/plugin-form/api-breaker/components/StatusCodes.vue';

interface KeyValuePair {
  key: string
  value: string
}

interface IFormData {
  break_response_code: number
  break_response_body: string
  break_response_headers: KeyValuePair[]
  max_breaker_sec: number
  unhealthy: {
    http_statuses: number[]
    failures: number
  }
  healthy: {
    http_statuses: number[]
    successes: number
  }
}

interface IProps { data: IFormData }

const { data } = defineProps<IProps>();

const { t } = useI18n();

const formRef = useTemplateRef('formRef');

const keyValueRef = useTemplateRef('keyValueRef');
const unhealthyStatusCodesRef = useTemplateRef('unhealthyStatusCodesRef');
const healthyStatusCodesRef = useTemplateRef('healthyStatusCodesRef');

const getDefaultData = () => ({
  break_response_code: 502,
  break_response_body: '',
  break_response_headers: [],
  max_breaker_sec: 300,
  unhealthy: {
    http_statuses: [503],
    failures: 3,
  },
  healthy: {
    http_statuses: [200],
    successes: 3,
  },
});

const formData = ref<IFormData>(getDefaultData());

const rules = {};

watch(() => data, () => {
  if (data?.unhealthy?.http_statuses) {
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
    await healthyStatusCodesRef.value?.validate();
    await unhealthyStatusCodesRef.value?.validate();
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
