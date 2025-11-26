<template>
  <BkForm
    ref="formRef"
    :model="formData"
    :rules="formRules"
  >
    <BkFormItem :label="schema?.['ui:oneOf']?.title">
      <BkRadioGroup
        v-model="selectedOptionIndex"
        @change="handleOptionChange"
      >
        <BkRadio
          v-for="(option, index) in schema?.oneOf"
          :key="index"
          :label="index"
        >
          {{ option.title }}
        </BkRadio>
      </BkRadioGroup>
    </BkFormItem>

    <SchemaField
      ref="schemaFieldRef"
      v-model="formData"
      :schema="schema"
      :selected-schema="selectedSchema"
      :component-map="componentMap"
      :disabled="disabled"
    />
  </BkForm>
</template>

<script setup lang="ts">
import { Form } from 'bkui-vue';
import { type ISchema } from '@/components/plugin-manage/schema-type';
import SchemaField from '@/components/plugin-manage/components/SchemaField.vue';

interface IProps {
  schema?: ISchema
  componentMap?: Record<string, Component>
  disabled?: boolean
  routeMode: string
}

interface IEmits { (e: 'update:modelValue', value: any): void }

const formData = defineModel('modelValue', {
  required: true,
  type: [Object, String],
});

const {
  schema = {},
  componentMap = {},
  disabled = false,
} = defineProps<IProps>();

const emit = defineEmits<IEmits>();

const { t } = useI18n();

// IPv4 CIDR 正则
const ipv4CidrRegex = /^((25[0-5]|(2[0-4]|1\d|[1-9]|)\d)\.?\b){4}(\/([0-9]|[12]\d|3[0-2]))?$/;

// IPv6 CIDR 正则
const ipv6CidrRegex
  = /^(([0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}|([0-9a-fA-F]{1,4}:){1,7}:|([0-9a-fA-F]{1,4}:){1,6}:[0-9a-fA-F]{1,4}|([0-9a-fA-F]{1,4}:){1,5}(:[0-9a-fA-F]{1,4}){1,2}|([0-9a-fA-F]{1,4}:){1,4}(:[0-9a-fA-F]{1,4}){1,3}|([0-9a-fA-F]{1,4}:){1,3}(:[0-9a-fA-F]{1,4}){1,4}|([0-9a-fA-F]{1,4}:){1,2}(:[0-9a-fA-F]{1,4}){1,5}|[0-9a-fA-F]{1,4}:((:[0-9a-fA-F]{1,4}){1,6})|:((:[0-9a-fA-F]{1,4}){1,7}|:))(\/([0-9]|[1-9]\d|1[01]\d|12[0-8]))?$/;

const formRef = ref<InstanceType<typeof Form> | null>(null);

const schemaFieldRef = ref<InstanceType<typeof SchemaField> | null>(null);

const selectedOptionIndex = ref(0);

const selectedSchema = computed(() => {
  return schema?.oneOf?.[selectedOptionIndex.value];
});

const curSelectType = computed(() => {
  return Object.keys(selectedSchema.value?.properties ?? {})?.[0] ?? '';
});

const formRules = computed(() => {
  const schemaTitle = selectedSchema.value?.title ?? '';
  const requiredField = selectedSchema.value?.required;
  const minLength = Array.isArray(requiredField) && requiredField?.includes(curSelectType.value)
    ? selectedSchema.value?.properties?.[curSelectType.value]?.minLength
    : undefined;
  const commonRules = [
    {
      required: true,
      message: t('请输入{inputValue}', { inputValue: schemaTitle }),
      trigger: 'change',
      validator: (value: string) => {
        return !!value?.trim();
      },
    },
    // 格式校验（IPv4/CIDR 或 IPv6/CIDR）
    {
      message: t('{ipTitle}格式不符合IPv4/CIDR或IPv6/CIDR规范', { ipTitle: schemaTitle }),
      trigger: 'change',
      validator: (value: string) => {
        if (!value?.trim()) return true;
        return ipv4CidrRegex.test(value) || ipv6CidrRegex.test(value);
      },
    },
  ];

  const extraRules: any[] = [];
  if (minLength && typeof minLength === 'number' && minLength > 0) {
    extraRules.push({
      message: t('{inputValue}不应少于{count}个字符', {
        inputValue: schemaTitle,
        count: minLength,
      }),
      trigger: 'change',
      validator: (value: string) => {
        const trimmedValue = value?.trim() || '';
        return trimmedValue.length >= minLength;
      },
    });
  }

  const mergedRules = [...commonRules, ...extraRules];

  return {
    whitelist: mergedRules,
    blacklist: mergedRules,
  };
});

const validate = async () => {
  try {
    const isValid = await formRef.value?.validate(); ;
    if (!isValid) {
      schemaFieldRef.value?.comRef?.schemaFieldRef?.[0]?.comRef?.focus();
      return;
    }
    return isValid;
  }
  catch {
    return false;
  }
};

const clearValidate = () => {
  return formRef.value?.clearValidate();
};

// 切换类型时重置模型值
const handleOptionChange = () => {
  clearValidate();
  emit('update:modelValue', {});
};

watch(
  () => formData.value,
  (newVal) => {
    clearValidate();
    if (newVal?.whitelist) selectedOptionIndex.value = 0;
    if (newVal?.blacklist) selectedOptionIndex.value = 1;
  },
  { immediate: true },
);

defineExpose({
  validate,
  clearValidate,
});
</script>
