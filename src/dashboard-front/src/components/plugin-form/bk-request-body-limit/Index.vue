<template>
  <BkForm
    ref="formRef"
    :model="form"
    :rules="rules"
  >
    <BkFormItem
      required
      property="max_body_size"
      label="max_body_size"
      :description="t('最大请求体大小（以字节为单位）')"
    >
      <BkInput
        v-model="form.max_body_size"
        :max="33554432"
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

interface IFormModel { max_body_size: number }

interface IProps { data: IFormModel }

const { data } = defineProps<IProps>();

const { t } = useI18n();

const formRef = ref();

const form = ref<IFormModel>({ max_body_size: 33554432 });

const rules = {
  max_body_size: [
    {
      validator: (value: string) => isInteger(Number(value)) && Number(value) >= 1 && Number(value) <= 33554432,
      message: t('必须是介于 1 到 33554432 的正整数'),
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
