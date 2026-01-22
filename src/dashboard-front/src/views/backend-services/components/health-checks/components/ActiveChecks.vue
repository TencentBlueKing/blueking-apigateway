<template>
  <div>
    <CheckboxCollapse
      v-model="enabled"
      :name="t('主动检查')"
      :desc="t('通过预设的探针类型，主动探测上游节点的存活性')"
    >
      <BkForm
        :model="active"
        form-type="vertical"
      >
        <BkFormItem
          :label="t('类型')"
          property="type"
        >
          <BkRadioGroup v-model="active.type">
            <BkRadio label="http" />
            <BkRadio label="https" />
            <BkRadio label="tcp" />
          </BkRadioGroup>
        </BkFormItem>
        <BkFormItem
          v-if="active.type === 'https'"
          :label="t('是否检查证书')"
          property="https_verify_certificate"
        >
          <BkRadioGroup v-model="active.https_verify_certificate">
            <BkRadio label>
              {{ t('是') }}
            </BkRadio>
            <BkRadio :label="false">
              {{ t('否') }}
            </BkRadio>
          </BkRadioGroup>
        </BkFormItem>
        <BkFormItem
          :label="t('超时时间(s)')"
          property="timeout"
        >
          <BkInput
            v-model="active.timeout"
            class="w-260px"
            :precision="0"
            :step="1"
            type="number"
          />
        </BkFormItem>
        <BkFormItem
          :label="t('并行数量')"
          property="concurrency"
        >
          <BkInput
            v-model="active.concurrency"
            class="w-260px"
            :precision="0"
            :step="1"
            type="number"
          />
        </BkFormItem>
        <BkFormItem
          v-if="active.type !== 'tcp'"
          :label="t('健康检查.请求路径')"
          property="http_path"
        >
          <BkInput
            v-model="active.http_path"
          />
        </BkFormItem>

        <h3 class="text-14px color-#313238 font-700 line-height-18px mb-16px">
          {{ t('健康状态') }}
        </h3>

        <BkFormItem
          :label="t('间隔时间(s)')"
          property="healthy.interval"
        >
          <BkInput
            v-model="active.healthy.interval"
            class="w-260px"
            :precision="0"
            :min="1"
            :step="1"
            type="number"
          />
        </BkFormItem>
        <BkFormItem
          v-if="active.type !== 'tcp'"
          :label="t('状态码')"
          property="healthy.http_statuses"
        >
          <BkTagInput
            v-model="active.healthy.http_statuses"
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
            v-model="active.healthy.successes"
            class="w-260px"
            :precision="0"
            :step="1"
            :max="254"
            :min="1"
            type="number"
          />
        </BkFormItem>

        <h3 class="text-14px color-#313238 font-700 line-height-18px mb-16px">
          {{ t('不健康状态') }}
        </h3>

        <BkFormItem
          :label="t('间隔时间(s)')"
          property="unhealthy.interval"
        >
          <BkInput
            v-model="active.unhealthy.interval"
            class="w-260px"
            :precision="0"
            :min="1"
            :step="1"
            type="number"
          />
        </BkFormItem>
        <BkFormItem
          v-if="active.type !== 'tcp'"
          :label="t('状态码')"
          property="unhealthy.http_statuses"
        >
          <BkTagInput
            v-model="active.unhealthy.http_statuses"
            :create-tag-validator="tagValidator"
            :placeholder="t('HTTP 状态码')"
            allow-create
            has-delete-icon
          />
        </BkFormItem>
        <BkFormItem
          v-if="active.type === 'tcp'"
          :label="t('失败次数')"
          property="unhealthy.tcp_failures"
        >
          <BkInput
            v-model="active.unhealthy.tcp_failures"
            class="w-260px"
            :precision="0"
            :step="1"
            :max="254"
            :min="1"
            type="number"
          />
        </BkFormItem>
        <BkFormItem
          v-else
          :label="t('失败次数')"
          property="unhealthy.http_failures"
        >
          <BkInput
            v-model="active.unhealthy.http_failures"
            class="w-260px"
            :precision="0"
            :step="1"
            :max="254"
            :min="1"
            type="number"
          />
        </BkFormItem>
        <BkFormItem
          :label="t('超时时间(s)')"
          property="unhealthy.timeouts"
        >
          <BkInput
            v-model="active.unhealthy.timeouts"
            class="w-260px"
            :precision="0"
            :step="1"
            :max="254"
            :min="1"
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

interface IProps { checks?: IHealthCheck['active'] }

const enabled = defineModel<boolean>('enabled', { default: false });

const { checks = undefined } = defineProps<IProps>();

const { t } = useI18n();

const active = ref<IHealthCheck['active']>({
  type: 'http',
  timeout: 1,
  concurrency: 10,
  http_path: '/',
  https_verify_certificate: true,
  healthy: {
    http_statuses: [200, 302],
    successes: 2,
    interval: 1,
  },
  unhealthy: {
    http_statuses: [429, 404, 500, 501, 502, 503, 504, 505],
    http_failures: 5,
    tcp_failures: 2,
    timeouts: 3,
    interval: 1,
  },
});

watch(() => checks, () => {
  if (checks && isPlainObject(checks)) {
    Object.assign(active.value, cloneDeep(checks));
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
    const checks = cloneDeep(active.value);
    if (checks.type === 'tcp') {
      delete checks.http_path;
      delete checks.healthy.http_statuses;
      delete checks.unhealthy.http_statuses;
      delete checks.unhealthy.http_failures;
    }
    else {
      delete checks.unhealthy.tcp_failures;
    }
    if (checks.type !== 'https') {
      delete checks.https_verify_certificate;
    }
    return checks;
  },
});

</script>
