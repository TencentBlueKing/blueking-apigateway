<template>
  <BkForm
    ref="formRef"
    :model="form"
    :rules="rules"
  >
    <BkFormItem
      required
      property="uri"
      :label="t('重定向 URI')"
      :description="t('要重定向到的 URI，可以包含 NGINX 变量。例如：/test/index.html，$uri/index.html，${uri}/index.html，https://example.com/foo/bar。如果你引入了一个不存在的变量，它不会报错，而是将其视为一个空变量。')"
    >
      <BkInput
        v-model="form.uri"
        clearable
      />
    </BkFormItem>
    <BkFormItem
      property="ret_code"
      :label="t('HTTP 响应码')"
    >
      <BkInput
        v-model="form.ret_code"
        :max="599"
        :min="200"
        :precision="0"
        type="number"
        clearable
      />
    </BkFormItem>
  </BkForm>
</template>

<script setup lang="ts">
import { isInteger } from 'lodash-es';

interface IFormModel {
  uri: string
  ret_code: number
}

interface IProps { data: IFormModel }

const { data } = defineProps<IProps>();

const { t } = useI18n();

const formRef = ref();

const form = ref<IFormModel>({
  uri: '',
  ret_code: 302,
});

const rules = {
  uri: [
    {
      validator: (value: string) => /(\\\$[0-9a-zA-Z_]+)|\$\{([0-9a-zA-Z_]+)\}|\$([0-9a-zA-Z_]+)|(\$|[^$\\]+)/.test(value),
      message: t('需要符合规则 (\\\\\\$[0-9a-zA-Z_]+)\\|\\$\\{([0-9a-zA-Z_]+)\\}\\|\\$([0-9a-zA-Z_]+)\\|(\\$|[^$\\\\]+)'),
      trigger: 'change',
    },
  ],
  ret_code: [
    {
      validator: (value: string) =>
        !value || (isInteger(Number(value)) && Number(value) >= 200 && Number(value) <= 599),
      message: t('必须是介于 200 到 599 的正整数'),
      trigger: 'change',
    },
  ],
};

watch(() => data, () => {
  if (data) {
    form.value = { ...data };
  }
}, {
  immediate: true,
  deep: true,
});

defineExpose({ getValue: () => formRef.value.validate().then(() => form.value) });

</script>
