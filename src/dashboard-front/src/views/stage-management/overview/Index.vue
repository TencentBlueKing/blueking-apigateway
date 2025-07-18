<template>
  <div class="py-20px px-24px">
    <!-- 自定义头部 -->
    <TopBar
      v-model:mode="mode"
      v-model:stage-id="stageId"
    />
    <OverviewMode v-if="mode === 'overview'" />
    <DetailMode
      v-else-if="mode === 'detail' && stageId"
      :stage-id="stageId"
    />
  </div>
</template>

<script lang="ts" setup>
import OverviewMode from './components/OverviewMode.vue';
import TopBar from './components/TopBar.vue';
import DetailMode from './components/DetailMode.vue';

const mode = ref('overview');
const stageId = ref(0);
</script>
