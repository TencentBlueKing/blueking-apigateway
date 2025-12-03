<template>
  <BkForm
    ref="formRef"
    :model="form"
    :rules="rules"
  >
    <BkFormItem :label="t('类型')">
      <BkRadioGroup v-model="type">
        <BkRadio label="whitelist">
          {{ t('白名单') }}
        </BkRadio>
        <BkRadio label="blacklist">
          {{ t('黑名单') }}
        </BkRadio>
      </BkRadioGroup>
    </BkFormItem>

    <BkFormItem
      v-show="type === 'whitelist'"
      required
      :label="t('白名单')"
    >
      <UserInput
        ref="whitelistInputRef"
        :users="form.whitelist"
      />
    </BkFormItem>

    <BkFormItem
      v-show="type === 'blacklist'"
      required
      :label="t('黑名单')"
    >
      <UserInput
        ref="blacklistInputRef"
        :users="form.blacklist"
      />
    </BkFormItem>

    <BkFormItem
      required
      property="message"
      label="message"
    >
      <BkInput
        v-model="form.message"
        clearable
      />
    </BkFormItem>
  </BkForm>
</template>

<script setup lang="ts">
import UserInput from './components/UserInput.vue';

interface IFormModel {
  whitelist?: { key: string }[]
  blacklist?: { key: string }[]
  message: string
}

interface IProps { data: IFormModel }

const { data } = defineProps<IProps>();

const { t } = useI18n();

const formRef = ref();
const whitelistInputRef = ref();
const blacklistInputRef = ref();

const type = ref('whitelist');

const form = ref<IFormModel>({
  whitelist: [],
  blacklist: [],
  message: 'The bk-user is not allowed',
});

const rules = {
  message: [
    {
      required: true,
      message: t('message 必填'),
      trigger: 'blur',
    },
    {
      validator: (value: string) => value.length >= 1 && value.length <= 1024,
      message: t('长度必须介于 1 到 1024 之间'),
      trigger: 'change',
    },
  ],
};

watch(() => data, () => {
  if (data) {
    if (data.blacklist?.length) {
      type.value = 'blacklist';
    }
    else {
      type.value = 'whitelist';
    }
    form.value.whitelist = data.whitelist || [];
    form.value.blacklist = data.blacklist || [];
    form.value.message = data.message || 'The bk-user is not allowed';
  }
}, {
  immediate: true,
  deep: true,
});

defineExpose({
  getValue: async () => {
    const list = type.value === 'whitelist'
      ? await whitelistInputRef.value.getValue()
      : await blacklistInputRef.value.getValue();
    return formRef.value.validate().then(() => {
      if (type.value === 'whitelist') {
        return {
          whitelist: list,
          message: form.value.message,
        };
      }
      else {
        return {
          blacklist: list,
          message: form.value.message,
        };
      }
    });
  },
});

</script>
