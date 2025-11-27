<template>
  <BkForm
    ref="formRef"
    :model="formData"
    :rules="rules"
  >
    <BkFormItem
      :label="t('响应状态码')"
      property="response_status"
      required
    >
      <BkInput
        v-model="formData.response_status"
        :min="100"
        type="number"
      />
    </BkFormItem>
    <BkFormItem
      :label="t('响应体')"
      property="response_example"
    >
      <BkInput
        v-model="formData.response_example"
        :placeholder="t('请输入')"
        :rows="10"
        type="textarea"
      />
    </BkFormItem>
    <BkFormItem
      :label="t('响应头')"
      property="response_headers"
      :description="t('设置响应头')"
    >
      <KeyValuePairs
        ref="keyValueRef"
        v-model="formData.response_headers"
      />
    </BkFormItem>
  </BkForm>
</template>

<script lang="ts" setup>
import { cloneDeep } from 'lodash-es';
import KeyValuePairs from '@/components/plugin-form/api-breaker/components/KeyValuePairs.vue';

interface IFormData {
  response_status: number
  response_example: string
  response_headers: Array<{
    key: string
    value: string
  }>
}

interface IProps { data: IFormData }

const { data } = defineProps<IProps>();

const { t } = useI18n();

const formRef = useTemplateRef('formRef');
const keyValueRef = useTemplateRef('keyValueRef');

const getDefaultData = () => ({
  response_status: 200,
  response_example: '',
  response_headers: [],
});

const formData = ref<IFormData>(getDefaultData());

const rules = {};

watch(() => data, () => {
  if (data && Object.keys(data).length) {
    formData.value = cloneDeep(data);
  }
  else {
    formData.value = getDefaultData();
  }
}, {
  immediate: true,
  deep: true,
});

const validate = () => formRef.value?.validate();

const getValue = () => validate()?.then(() => formData.value);

defineExpose({
  validate,
  getValue,
});

</script>

<style lang="scss" scoped>
</style>
