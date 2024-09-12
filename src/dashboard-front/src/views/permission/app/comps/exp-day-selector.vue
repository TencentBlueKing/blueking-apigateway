<template>
  <bk-form v-bind="$attrs">
    <bk-form-item :label="t('授权期限')" label-width="90" label-position="left" required>
      <bk-radio-group v-model="expireDays">
        <bk-radio-button
          v-for="option in radioOptions"
          :key="option.label"
          :label="option.label"
          style="width: 90px;"
        >{{ option.text }}</bk-radio-button>
      </bk-radio-group>
    </bk-form-item>
  </bk-form>
</template>

<script setup lang="ts">
import { useI18n } from 'vue-i18n';
import { ref } from 'vue';

const { t } = useI18n();

const expireDays = defineModel<0 | 180 | 360>({
  required: true,
  default: 0,
});

const radioOptions = ref([
  {
    text: t('永久'),
    label: 0,
  },
  {
    text: t('6个月'),
    label: 180,
  },
  {
    text: t('12个月'),
    label: 360,
  },
]);

</script>

