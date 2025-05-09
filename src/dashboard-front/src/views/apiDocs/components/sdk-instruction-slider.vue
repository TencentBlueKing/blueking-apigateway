<template>
  <!--  SDK使用说明 Slider  -->
  <div class="sdk-instruction-slider">
    <bk-sideslider
      v-model:is-show="isShow"
      width="960"
      :title="t('SDK 使用说明')"
      quick-close
    >
      <template #default>
        <div class="content-wrap">
          <SdkInstructionContent></SdkInstructionContent>
        </div>
      </template>
    </bk-sideslider>
  </div>
</template>

<script setup lang="ts">
import { useI18n } from 'vue-i18n';
import { defineModel } from 'vue';

import SdkInstructionContent from '@/views/apiDocs/components/sdk-instruction-content.vue';

const isShow = defineModel<boolean>({
  required: true,
  default: false,
});

const { t } = useI18n();

</script>

<style scoped lang="scss">
.sdk-instruction-slider {
  .content-wrap {
    padding: 24px 24px 0 24px;
  }
}
</style>
