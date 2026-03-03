<template>
  <div>
    <CheckboxCollapse
      v-model="enabled"
      :name="t('被动检查')"
      :desc="t('通过实际请求的响应状态判断节点健康情况，无需额外探针请求，但可能会延迟问题发现，导致部分请求失败。')
        + t('由于不健康的节点无法收到请求，仅使用被动健康检查策略无法重新将节点标记为健康，因此通常需要结合主动健康检查策略。')"
      :disabled="disabled"
    >
      <BkForm
        :model="passive"
        form-type="vertical"
      >
        <BkFormItem
          :label="t('类型')"
          property="type"
        >
          <BkRadioGroup v-model="passive.type">
            <BkRadio label="http" />
            <BkRadio label="https" />
            <BkRadio label="tcp" />
          </BkRadioGroup>
        </BkFormItem>

        <h3 class="text-14px color-#313238 font-700 line-height-18px mb-16px">
          {{ t('健康状态') }}
        </h3>

        <BkFormItem
          v-if="passive.type !== 'tcp'"
          :label="t('状态码')"
          property="healthy.http_statuses"
        >
          <BkTagInput
            v-model="passive.healthy.http_statuses"
            :create-tag-validator="tagValidator"
            :placeholder="t('HTTP 状态码')"
            allow-create
            has-delete-icon
          />
        </BkFormItem>
        <BkFormItem
          :label="t('成功次数')"
          property="healthy.successes"
        >
          <BkInput
            v-model="passive.healthy.successes"
            class="w-260px"
            :precision="0"
            :step="1"
            :max="254"
            :min="0"
            type="number"
          />
        </BkFormItem>

        <h3 class="text-14px color-#313238 font-700 line-height-18px mb-16px">
          {{ t('不健康状态') }}
        </h3>

        <BkFormItem
          v-if="passive.type !== 'tcp'"
          :label="t('状态码')"
          property="unhealthy.http_statuses"
        >
          <BkTagInput
            v-model="passive.unhealthy.http_statuses"
            :create-tag-validator="tagValidator"
            :placeholder="t('HTTP 状态码')"
            allow-create
            has-delete-icon
          />
        </BkFormItem>
        <BkFormItem
          v-if="passive.type === 'tcp'"
          :label="t('失败次数')"
          property="unhealthy.tcp_failures"
        >
          <BkInput
            v-model="passive.unhealthy.tcp_failures"
            class="w-260px"
            :precision="0"
            :step="1"
            :max="254"
            :min="0"
            type="number"
          />
        </BkFormItem>
        <BkFormItem
          v-else
          :label="t('失败次数')"
          property="unhealthy.http_failures"
        >
          <BkInput
            v-model="passive.unhealthy.http_failures"
            class="w-260px"
            :precision="0"
            :step="1"
            :max="254"
            :min="0"
            type="number"
          />
        </BkFormItem>
        <BkFormItem
          :label="t('超时时间(s)')"
          property="unhealthy.timeouts"
        >
          <BkInput
            v-model="passive.unhealthy.timeouts"
            class="w-260px"
            :precision="0"
            :step="1"
            :max="254"
            :min="0"
            type="number"
          />
        </BkFormItem>
      </BkForm>
    </CheckboxCollapse>
  </div>
</template>

<script setup lang="ts">
import { Message } from 'bkui-vue';
import CheckboxCollapse from './CheckboxCollapse.vue';
import type { IHealthCheck } from '@/services/source/backend-services.ts';
import {
  cloneDeep,
  isPlainObject,
} from 'lodash-es';

interface IProps {
  checks?: IHealthCheck['passive']
  disabled?: boolean
}

const enabled = defineModel<boolean>('enabled', { default: false });

const {
  checks = undefined,
  disabled = false,
} = defineProps<IProps>();

const { t } = useI18n();

const passive = ref<IHealthCheck['passive']>({
  type: 'http',
  healthy: {
    http_statuses: [200, 201, 202, 203, 204, 205, 206, 207, 208, 226, 300, 301, 302, 303, 304, 305, 306, 307, 308],
    successes: 5,
  },
  unhealthy: {
    http_statuses: [429, 500, 503],
    http_failures: 5,
    tcp_failures: 2,
    timeouts: 7,
  },
});

watch(() => checks, () => {
  if (checks && isPlainObject(checks)) {
    Object.assign(passive.value, cloneDeep(checks));
  }
}, {
  immediate: true,
  deep: true,
});

const tagValidator = (value: string) => {
  if (!/^[1-5][0-9][0-9]$/g.test(value)) {
    Message({
      theme: 'warning',
      message: t('{code} 不是合法的 HTTP 状态码', { code: value }),
    });
    return false;
  }

  return true;
};

defineExpose({
  getValue: () => {
    const checks = cloneDeep(passive.value);
    if (checks.type === 'tcp') {
      delete checks.healthy.http_statuses;
      delete checks.unhealthy.http_statuses;
      delete checks.unhealthy.http_failures;
    }
    else {
      delete checks.unhealthy.tcp_failures;
    }
    return checks;
  },
});

</script>
