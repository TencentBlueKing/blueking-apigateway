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
    <BkFormItem
      property="allow_fallback"
      :label="t('允许降级')"
      :description="t('是否允许调用方没有使用新的认证头的情况下，不报错降级使用 X-Bkapi-Authorization 认证头')"
    >
      <BkSwitcher
        v-model="form.allow_fallback"
        theme="primary"
      />
    </BkFormItem>
  </BkForm>
</template>

<script setup lang="ts">

interface IFormModel {
  source: 'bearer' | 'api_key'
  allow_fallback: boolean
}

interface IProps { data: IFormModel }

const { data } = defineProps<IProps>();

const { t } = useI18n();

const formRef = ref();

const form = ref<IFormModel>({
  source: 'bearer',
  allow_fallback: true,
});

watch(() => data, () => {
  if (data) {
    form.value.source = data.source || 'bearer';
    form.value.allow_fallback = data.allow_fallback ?? true;
  }
}, {
  immediate: true,
  deep: true,
});

defineExpose({ getValue: () => formRef.value.validate().then(() => form.value) });

</script>
