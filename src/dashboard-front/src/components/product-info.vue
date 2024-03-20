<script setup lang="ts">
import { useI18n } from 'vue-i18n';
import { useGetGlobalProperties } from '@/hooks';

const { t } = useI18n();

const globalProperties = useGetGlobalProperties();
const { GLOBAL_CONFIG } = globalProperties;
</script>

<template>
  <bk-popover
    placement="bottom"
    theme="light"
    :arrow="false"
    :padding="0"
  >
    <div class="info-icon">
      <span class="icon apigateway-icon icon-ag-help-document-fill"></span>
    </div>
    <template #content>
      <bk-link
        class="info-item" :href="GLOBAL_CONFIG.HELPER.href" target="_blank"
        v-if="GLOBAL_CONFIG.HELPER.href && GLOBAL_CONFIG.HELPER.name">
        {{ t(GLOBAL_CONFIG.HELPER.name) }}
      </bk-link>
      <!-- v-if="GLOBAL_CONFIG.BK_FEED_BACK_LINK" -->
      <bk-link class="info-item" :href="GLOBAL_CONFIG.BK_FEED_BACK_LINK" target="_blank">
        {{ t('问题反馈') }}
      </bk-link>
      <!-- v-if="GLOBAL_CONFIG.MARKER" -->
      <bk-link class="info-item" :href="GLOBAL_CONFIG.MARKER" target="_blank">
        {{ t('开源社区') }}
      </bk-link>
    </template>
  </bk-popover>
</template>

<style lang="scss" scoped>
.info-icon {
  cursor: pointer;
  margin-right: 30px;
}
.info-icon:hover {
  color: #fff;
}
.info-item {
  display: block;
  color: #63656E;
  padding: 8px 15px;
  margin-top: 5px;
  font-size: 12px;
}
.info-item:hover {
  background: #f3f6f9;
}
.info-item:nth-of-type(1) {
    margin-top: 0px;
}
</style>
