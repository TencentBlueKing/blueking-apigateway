<template>
  <BkForm
    ref="formRef"
    :model="form"
    :rules="rules"
  >
    <BkFormItem
      required
      :label="t('拦截规则')"
      :description="t('需要拦截的 URI 列表，支持正则表达式')"
    >
      <RuleInput
        ref="blockRulesInputRef"
        :block-rules="form.block_rules"
      />
    </BkFormItem>
    <BkFormItem
      property="case_insensitive"
      :label="t('忽略大小写')"
    >
      <BkSwitcher
        v-model="form.case_insensitive"
        theme="primary"
      />
    </BkFormItem>
    <BkFormItem
      property="rejected_code"
      :label="t('拒绝状态码')"
      :description="t('请求被拦截时返回的 HTTP 状态码')"
    >
      <BkInput
        v-model="form.rejected_code"
        :max="599"
        :precision="0"
        type="number"
        clearable
      />
    </BkFormItem>
    <BkFormItem
      property="rejected_msg"
      :label="t('拒绝消息')"
      :description="t('请求被拦截时返回的消息')"
    >
      <BkInput
        v-model="form.rejected_msg"
        :placeholder="t('请输入拒绝消息')"
        clearable
      />
    </BkFormItem>
  </BkForm>
</template>

<script setup lang="ts">
import { isInteger } from 'lodash-es';
import { Form } from 'bkui-vue';
import type { IFormMethod } from '@/types/common';
import RuleInput from './components/RuleInput.vue';

interface IFormModel {
  block_rules: string[]
  case_insensitive?: boolean
  rejected_code?: number
  rejected_msg?: string
}

interface IProps { data: IFormModel }

const { data } = defineProps<IProps>();

const { t } = useI18n();

const formRef = ref<InstanceType<typeof Form> & IFormMethod>();
const blockRulesInputRef = ref();

const form = ref<IFormModel>({
  block_rules: [''],
  case_insensitive: false,
  rejected_code: 403,
  rejected_msg: '',
});

const rules = {
  rejected_code: [
    {
      validator: (value: string) =>
        !value || (isInteger(Number(value)) && Number(value) >= 200 && Number(value) <= 599),
      message: t('必须是介于 200 到 599 的正整数'),
      trigger: 'change',
    },
  ],
  rejected_msg: [
    {
      validator: (value: string) => !value || value.length >= 1,
      message: t('拒绝消息不能为空'),
      trigger: 'blur',
    },
  ],
};

watch(
  () => data,
  () => {
    if (data) {
      form.value = {
        block_rules: data.block_rules?.length ? [...data.block_rules] : [''],
        case_insensitive: data.case_insensitive ?? false,
        rejected_code: data.rejected_code ?? 403,
        rejected_msg: data.rejected_msg ?? '',
      };
    }
  },
  {
    immediate: true,
    deep: true,
  },
);

defineExpose({
  getValue: async () => {
    const rules = await blockRulesInputRef.value?.getValue();
    await formRef.value!.validate();
    const result: IFormModel = {
      block_rules: rules,
    };
    if (form.value.case_insensitive === true) {
      result.case_insensitive = form.value.case_insensitive;
    }
    if (form.value.rejected_code !== 403) {
      result.rejected_code = form.value.rejected_code;
    }
    if (form.value.rejected_msg) {
      result.rejected_msg = form.value.rejected_msg;
    }
    return result;
  },
});

</script>
