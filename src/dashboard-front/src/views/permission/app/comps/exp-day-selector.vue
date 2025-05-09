<template>
  <bk-form label-position="right" label-width="100" v-bind="$attrs">
    <bk-form-item :label="t('授权期限')" required>
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

const expireDays = defineModel<0 | 180 | 360>({
  required: true,
  default: 0,
});

const { t } = useI18n();

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

