<template>
  <div>{{ placeholder }}</div>
</template>

<script lang="ts" setup>
import { ref } from 'vue';
import { useI18n } from 'vue-i18n';

const { t } = useI18n();

const placeholder = ref(t('自动化接入网关'));
</script>

<style lang="scss" scoped></style>
