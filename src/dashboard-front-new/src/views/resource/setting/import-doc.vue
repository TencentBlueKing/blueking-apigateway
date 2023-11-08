<template>
  <div class="import-docs-container p20">
    <bk-form :label-width="100">
      <bk-form-item class="mb0" :label="t('文档类型')" :label-width="120">
        <bk-radio-group v-model="docType">
          <bk-radio label="zh">{{ t('压缩包') }}</bk-radio>
          <bk-radio label="en">Swagger</bk-radio>
        </bk-radio-group>
      </bk-form-item>
    </bk-form>
  </div>
</template>
<script setup lang="ts">
import { ref } from 'vue';
import { useI18n } from 'vue-i18n';

const { t } = useI18n();
const docType = ref<string>('archive');
</script>
