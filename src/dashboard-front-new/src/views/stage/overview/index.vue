<template>
  <div class="stage-overview-wrapper">
    <stage-card-list :stage-list="stageStore.stageList" />
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import stageCardList from './comps/stage-card-list.vue';
import { useStage } from '@/store';

// 环境列表
const stageStore = useStage();

</script>

<style lang="scss" scoped>
.test {
    display: flex;
    .test-item {
        flex: 1;
        height: 100px;
        background: red;
        margin: 0 10px;
    }
}
.stage-overview-wrapper {
  padding: 20px;
}
</style>

