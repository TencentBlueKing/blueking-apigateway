<template>
  <BkForm
    ref="formRef"
    :model="formData"
    :rules="rules"
  >
    <BkFormItem
      :label="t('请求体 JSON Schema')"
      property="body_schema"
      :description="t('request body 数据的 JSON Schema')"
      required
    >
      <BkInput
        v-model="formData.body_schema"
        :placeholder="t('请输入')"
        type="textarea"
        :maxlength="51200"
        :rows="10"
      />
    </BkFormItem>
    <BkFormItem
      :label="t('请求头 JSON Schema')"
      property="header_schema"
      :description="t('request header 数据的 JSON Schema')"
      required
    >
      <BkInput
        v-model="formData.header_schema"
        :placeholder="t('请输入')"
        type="textarea"
        :maxlength="51200"
        :rows="10"
      />
    </BkFormItem>
    <BkFormItem
      :label="t('拒绝状态码')"
      property="rejected_code"
    >
      <BkInput
        v-model="formData.rejected_code"
        type="number"
        :min="200"
      />
    </BkFormItem>
    <BkFormItem
      :label="t('拒绝信息')"
      property="rejected_msg"
    >
      <BkInput
        v-model="formData.rejected_msg"
        :placeholder="t('请输入')"
        type="textarea"
        :rows="10"
      />
    </BkFormItem>
  </BkForm>
</template>

<script lang="ts" setup>
import { cloneDeep } from 'lodash-es';

interface IFormData {
  body_schema: string
  header_schema: string
  rejected_code: number
  rejected_msg: string
}

interface IProps { data: IFormData }

const { data } = defineProps<IProps>();

const { t } = useI18n();

const formRef = useTemplateRef('formRef');

const getDefaultData = () => ({
  body_schema: '',
  header_schema: '',
  rejected_code: 400,
  rejected_msg: '',
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
