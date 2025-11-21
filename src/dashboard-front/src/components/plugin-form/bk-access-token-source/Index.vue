<template>
  <BkForm
    ref="formRef"
    :model="form"
  >
    <BkFormItem
      required
      property="source"
      :label="t('来源')"
      :description="t('认证令牌的来源，默认是 bearer')"
    >
      <BkRadioGroup v-model="form.source">
        <BkRadio
          label="bearer"
        />
        <BkRadio
          label="api_key"
        />
      </BkRadioGroup>
    </BkFormItem>
  </BkForm>
</template>

<script setup lang="ts">

interface IFormModel { source: 'bearer' | 'api_key' }

interface IProps { data: IFormModel }

const { data } = defineProps<IProps>();

const { t } = useI18n();

const formRef = ref();

const form = ref<IFormModel>({ source: 'bearer' });

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
