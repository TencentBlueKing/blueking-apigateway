<template>
  <BkForm
    ref="formRef"
    :model="form"
    :rules="rules"
  >
    <BkFormItem
      required
      property="cache_method"
      label="cache_method"
      :description="t('缓存方法，仅支持：GET, HEAD')"
    >
      <BkCheckboxGroup v-model="form.cache_method">
        <BkCheckbox
          label="GET"
          :checked="form.cache_method.includes('GET')"
          :disabled="form.cache_method.includes('GET') && form.cache_method.length === 1"
        />
        <BkCheckbox
          label="HEAD"
          :checked="form.cache_method.includes('HEAD')"
          :disabled="form.cache_method.includes('HEAD') && form.cache_method.length === 1"
        />
      </BkCheckboxGroup>
    </BkFormItem>
    <BkFormItem
      property="cache_ttl"
      label="cache_ttl"
      :description="t('缓存时间，最大值 3600 秒')"
    >
      <BkInput
        v-model="form.cache_ttl"
        :max="3600"
        :min="1"
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
  cache_method: ('GET' | 'HEAD')[]
  cache_ttl: number
}

interface IProps {
  data: {
    cache_method: { key: 'GET' | 'HEAD' }[]
    cache_ttl: number
  }
}

const { data } = defineProps<IProps>();

const { t } = useI18n();

const formRef = ref();

const form = ref<IFormModel>({
  cache_method: ['GET'],
  cache_ttl: 300,
});

const rules = {
  cache_method: [
    {
      required: true,
      validator: (value: string[]) => value.length >= 1 && value.length <= 2,
      message: t('必填，只能选择 GET 或 HEAD 方法'),
      trigger: 'change',
    },
  ],
  cache_ttl: [
    {
      validator: (value: string) => isInteger(Number(value)) && Number(value) >= 1 && Number(value) <= 3600,
      message: t('必须是介于 1 到 3600 的正整数'),
      trigger: 'change',
    },
  ],
};

watch(() => data, () => {
  if (data) {
    form.value.cache_method = data.cache_method?.map(method => method.key) || ['GET'];
    form.value.cache_ttl = data.cache_ttl || 300;
  }
}, {
  immediate: true,
  deep: true,
});

defineExpose({
  getValue: () => formRef.value.validate().then(() => ({
    cache_ttl: form.value.cache_ttl,
    cache_method: form.value.cache_method.map(key => ({ key })),
  })),
});

</script>
