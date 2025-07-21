<template>
  <div
    v-bk-tooltips="t('问问AI')"
    class="ai-blueking-button"
    :style="{ background: `url(${logo}) center center / 18px 18px no-repeat` }"
    v-bind="$attrs"
  />
</template>

<script lang="ts" setup>
import AIBluekingLogo from '@/images/ai-blueking.svg';

const logo = AIBluekingLogo;

const { t } = useI18n();
</script>

<style lang="scss" scoped>
.ai-blueking-button {
  width: 18px;
  height: 18px;
  margin-right: 8px;
  cursor: pointer;
}
</style>
