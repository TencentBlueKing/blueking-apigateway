<template>
  <div class="app-exception">
    <bk-exception
      :title="t('页面不存在')"
      type="404"
    >
    </bk-exception>
  </div>
</template>

<script lang="ts" setup>
import { useI18n } from 'vue-i18n';

const { t } = useI18n();
</script>

<style lang="scss" scoped>
.app-exception {
  display: flex;
  width: 100%;
  height: 100%;
  align-items: center;
  justify-content: center;
}
</style>
