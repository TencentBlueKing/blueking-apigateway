<template>
  <div>
    <!-- 自定义头部 -->
    <stage-top-bar />
    <div class="page-wrapper-padding stage-overview-wrapper">
      <!-- <bk-loading
        :loading="stageStore.realStageMainLoading"
      > -->
      <bk-alert
        v-if="commonStore.curApigwData?.kind === 1"
        :title="t('可编程网关的环境由平台内置，不能修改和新增')"
        class="mb24"
        closable
      />
      <stage-card-list :stage-list="stageStore.stageList" />
      <!-- </bk-loading> -->
    </div>
  </div>
</template>

<script setup lang="ts">
import stageCardList from './comps/stage-card-list.vue';
import stageTopBar from '@/components/stage-top-bar.vue';
import {
  useCommon,
  useStage,
} from '@/store';
import { useI18n } from 'vue-i18n';

// 环境列表
const stageStore = useStage();
const { t } = useI18n();
const commonStore = useCommon();

</script>
