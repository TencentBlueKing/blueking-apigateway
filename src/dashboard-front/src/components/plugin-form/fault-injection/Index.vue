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
      :label="t('中断')"
    >
      <bk-switcher
        v-model="formData.abort.enabled"
        theme="primary"
      />
    </BkFormItem>
    <template v-if="formData.abort.enabled">
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
    </template>

    <BkFormItem
      :label="t('延迟')"
    >
      <bk-switcher
        v-model="formData.delay.enabled"
        theme="primary"
      />
    </BkFormItem>
    <template v-if="formData.delay.enabled">
      <BkFormItem
        :label="t('延迟时间')"
        property="delay.duration"
        :description="t('延迟时间，单位秒，只能填入整数')"
        required
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
    </template>
  </BkForm>
</template>

<script lang="ts" setup>
import { cloneDeep } from 'lodash-es';
import { Message } from 'bkui-vue';

interface IFormData {
  abort: {
    http_status: number
    body?: string
    percentage?: number
    vars?: string
    enabled?: boolean
  }
  delay: {
    duration: number
    percentage?: number
    vars?: string
    enabled?: boolean
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
    percentage: 100,
    vars: '',
    enabled: true,
  },
  delay: {
    duration: 0,
    percentage: 100,
    vars: '',
    enabled: false,
  },
});

const formData = ref<IFormData>(getDefaultData());

const rules = {
  'abort.http_status': [
    {
      validator: (value: number) => {
        if (value === 0) {
          return true;
        }
        return value >= 200;
      },
      message: t('状态码需要大于等于 200'),
      trigger: 'blur',
    },
  ],
};

watch(
  () => [formData.value.abort.enabled, formData.value.delay.enabled],
  ([v1, v2]) => {
    if (!v1 && !v2) {
      Message({
        theme: 'error',
        message: t('中断信息和延迟信息不能同时为空'),
      });
    }
  },
);

watch(() => data, (newVal) => {
  const data = cloneDeep(newVal);
  if (data?.abort?.http_status || data?.delay?.duration) {
    if (!data?.abort?.http_status) {
      data.abort = getDefaultData()?.abort;
      data.abort.http_status = 0;
      data.abort.enabled = false;
      data.delay.enabled = true;
    }
    if (!data?.delay?.duration) {
      data.delay = getDefaultData()?.delay;
      data.abort.enabled = true;
    }
    if (data?.abort?.http_status && data?.delay?.duration) {
      data.abort.enabled = true;
      data.delay.enabled = true;
    }
    formData.value = data;
  }
  else {
    formData.value = getDefaultData();
  }
}, {
  immediate: true,
  deep: true,
});

// const isDefaultData = (field: string) => {
//   return JSON.stringify(formData.value[field]) === JSON.stringify(getDefaultData()[field]);
// };

// const isEffective = () => {
//   let flag = false;
//   const { abort, delay } = formData.value;

//   if (Object.keys(abort).some(key => (abort[key] !== 0 && abort[key] !== ''))) {
//     flag = true;
//   }
//   if (Object.keys(delay).some(key => (delay[key] !== 0 && delay[key] !== ''))) {
//     flag = true;
//   }
//   return flag;
// };

const validate = async () => {
  try {
    await formRef.value?.validate();

    if (!formData.value.abort.enabled && !formData.value.delay.enabled) {
      Message({
        theme: 'error',
        message: t('中断信息和延迟信息不能同时为空'),
      });
      return Promise.reject(false);
    }

    if (formData.value.abort.enabled && !formData.value?.abort?.http_status) {
      Message({
        theme: 'error',
        message: t('请设置有效的中断状态码'),
      });
      return Promise.reject(false);
    }

    if (formData.value.delay.enabled && !formData.value?.delay?.duration) {
      Message({
        theme: 'error',
        message: t('请设置有效的延迟时间'),
      });
      return Promise.reject(false);
    }
  }
  catch (error) {
    return Promise.reject(error);
  }
};

const getValue = () => {
  return validate()?.then(() => {
    const data = cloneDeep(formData.value);

    if (!data?.delay?.vars) {
      data.delay = {
        ...data.delay,
        vars: undefined,
      };
    }
    if (!data?.abort?.vars) {
      data.abort = {
        ...data.abort,
        vars: undefined,
      };
    }

    if (!data?.delay?.enabled) {
      return {
        abort: {
          ...data.abort,
          enabled: undefined,
        },
        delay: undefined,
      };
    }
    if (!data?.abort?.enabled) {
      return {
        delay: {
          ...data.delay,
          enabled: undefined,
        },
        abort: undefined,
      };
    }
    return {
      abort: {
        ...data.abort,
        enabled: undefined,
      },
      delay: {
        ...data.delay,
        enabled: undefined,
      },
    };
  }).catch(error => Promise.reject(error));
};

defineExpose({
  validate,
  getValue,
});

</script>

<style lang="scss" scoped>
</style>
