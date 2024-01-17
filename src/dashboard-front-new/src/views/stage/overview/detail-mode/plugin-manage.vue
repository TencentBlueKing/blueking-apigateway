<template>
  <div class="plugin-manage-container">
    <plugin-manage :stage-id="props.stageId"></plugin-manage>
  </div>
</template>

<script setup lang="ts">
import PluginManage from '@/views/components/plugin-manage/index.vue';

const props = defineProps({
  stageId: Number,
});
</script>

<style lang="scss" scoped></style>
