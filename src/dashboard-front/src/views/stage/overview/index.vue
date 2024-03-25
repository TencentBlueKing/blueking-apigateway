<template>
  <div>
    <!-- 自定义头部 -->
    <stage-top-bar />
    <div class="page-wrapper-padding stage-overview-wrapper">
      <!-- <bk-loading
        :loading="stageStore.realStageMainLoading"
      > -->
      <stage-card-list :stage-list="stageStore.stageList" />
      <!-- </bk-loading> -->
    </div>
  </div>
</template>

<script setup lang="ts">
import stageCardList from './comps/stage-card-list.vue';
import stageTopBar from '@/components/stage-top-bar.vue';
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
</style>
