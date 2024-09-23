<template>
  <div class="resource-top-bar" :style="stage.getNotUpdatedStages?.length ? 'top: 42px' : 'top: -1px'">
    <div class="top-title-wrapper">
      <div class="title">{{ t('在线调试') }}</div>
      <div class="history" @click="showHistory">
        <i class="apigateway-icon icon-ag-cc-history history-icon"></i>
        <span>{{ t('请求记录') }}</span>
      </div>
    </div>
  </div>

  <!-- 调用历史 -->
  <request-record ref="requestRecordRef" />
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { useI18n } from 'vue-i18n';
import { useStage } from '@/store';
import requestRecord from '@/views/online-debug/components/request-record.vue';

const { t } = useI18n();
const stage = useStage();
const requestRecordRef = ref(null);

const showHistory = () => {
  requestRecordRef.value?.show();
};
</script>

<style lang="scss" scoped>
.resource-top-bar {
  position: absolute;
  width: 100%;
  height: 52px;
  box-sizing: border-box;
  padding: 0 24px;
  background: #FFFFFF;
  display: flex;
  align-items: center;
  justify-content: space-between;
  //min-width: 1280px;
  .top-title-wrapper {
    display: flex;
    align-items: center;
    justify-content: space-between;
    width: 100%;
    .title {
      font-size: 16px;
      color: #313238;
      margin-right: 8px;
    }
    .history {
      color: #3A84FF;
      cursor: pointer;
      .history-icon {
        font-size: 16px;
      }
      span {
        font-size: 12px;
      }
    }
  }
}
</style>
