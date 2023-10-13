<template>
  <div class="stage-overview-wrapper">
    <stage-card-list :stage-list="stageList" />
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { getStageList }  from '@/http';
import stageCardList from './comps/stage-card-list.vue';

// 环境列表
const stageList = ref([]);
// 获取环境列表
getStageList({ id: 1 }).then((data) => {
  stageList.value = data;
});

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

