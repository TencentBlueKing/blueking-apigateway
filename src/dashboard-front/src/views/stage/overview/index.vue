<template>
  <div>
    <!-- 自定义头部 -->
    <StageTopBar />
    <div class="page-wrapper-padding stage-overview-wrapper">
      <BkAlert
        v-if="commonStore.isProgrammableGateway"
        :title="t('可编程网关的环境由平台内置，不能修改和新增')"
        class="mb24"
        closable
      />
      <StageCardList />
    </div>
  </div>
</template>

<script setup lang="ts">
import StageCardList from './comps/stage-card-list.vue';
import StageTopBar from '@/components/stage-top-bar.vue';
import { useCommon } from '@/store';
import { useI18n } from 'vue-i18n';

const { t } = useI18n();
const commonStore = useCommon();

</script>
