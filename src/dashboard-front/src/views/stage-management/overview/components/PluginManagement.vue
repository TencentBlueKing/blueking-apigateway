<template>
  <div>
    <PluginManage :stage-id="stageId" />
  </div>
</template>

<script setup lang="ts">
import PluginManage from '@/components/plugin-manage/Index.vue';

interface IProps { stageId: number }

const { stageId } = defineProps<IProps>();
</script>
