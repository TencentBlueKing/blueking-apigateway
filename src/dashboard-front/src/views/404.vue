<template>
  <div class="app-exception">
    <BkException
      :title="t('页面不存在')"
      type="404"
    />
  </div>
</template>

<script setup lang="ts">
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
