<template>
  <BkForm
    label-position="right"
    label-width="100"
    v-bind="$attrs"
  >
    <BkFormItem
      :label="t('授权期限')"
      required
    >
      <BkRadioGroup v-model="expireDays">
        <BkRadioButton
          v-for="option in EXPIRE_DAYS_CONSTANTS"
          :key="option.value"
          :label="option.value"
          style="width: 90px;"
        >
          {{ option.label }}
        </BkRadioButton>
      </BkRadioGroup>
    </BkFormItem>
  </BkForm>
</template>

<script setup lang="ts">
import { EXPIRE_DAYS_CONSTANTS } from '@/constants';
import { t } from '@/locales';

const expireDays = defineModel('expireDays', {
  type: Number,
  required: true,
  default: 0,
});
</script>
