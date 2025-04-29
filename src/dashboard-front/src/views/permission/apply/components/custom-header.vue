<template>
  <div class="top-bar">
    <div class="top-left-wrapper">
      <div class="title">{{ t('权限审批') }}</div>
    </div>
    <div class="top-right-wrapper">
      <BkButton text theme="primary" @click="goToRecordPage">
        <AgIcon name="cc-history" style="margin-right: 6px;" />
        {{ t('审批历史') }}
      </BkButton>
    </div>
  </div>
</template>

<script lang="ts" setup>
import { useI18n } from 'vue-i18n';
import AgIcon from '@/components/ag-icon.vue';
import { useRouter } from 'vue-router';

const { t } = useI18n();
const router = useRouter();

const goToRecordPage = () => {
  router.push({ name: 'apigwPermissionRecords' });
};

</script>

<style lang="scss" scoped>

.top-bar {
  position: absolute;
  width: 100%;
  height: 52px;
  box-sizing: border-box;
  padding: 0 24px;
  background: #fff;
  display: flex;
  align-items: center;
  justify-content: space-between;
  top: -1px;

  .top-left-wrapper {
    display: flex;
    align-items: center;

    .title {
      font-size: 16px;
      color: #313238;
    }
  }

  .top-right-wrapper {
    display: flex;
    align-items: center;
    font-size: 12px;
  }
}
</style>
