<template>
  <div class="flex items-center justify-between top-bar">
    <div class="flex items-center top-left-wrapper">
      <div class="title">
        {{ t('权限审批') }}
      </div>
    </div>
    <div class="flex items-center top-right-wrapper">
      <BkButton
        text
        theme="primary"
        @click="handleNavRecordPage"
      >
        <AgIcon
          name="cc-history"
          class="m-r-6px"
        />
        {{ t('审批历史') }}
      </BkButton>
    </div>
  </div>
</template>

<script lang="ts" setup>
import AgIcon from '@/components/ag-icon/Index.vue';

const { t } = useI18n();
const router = useRouter();

const handleNavRecordPage = () => {
  router.push({ name: 'PermissionRecord' });
};

</script>

<style lang="scss" scoped>
.top-bar {
  position: absolute;
  width: 100%;
  height: 52px;
  box-sizing: border-box;
  padding: 0 24px;
  background: #ffffff;
  top: -1px;

  .top-left-wrapper {
    .title {
      font-size: 16px;
      color: #313238;
    }
  }

  .top-right-wrapper {
    font-size: 12px;
  }
}
</style>
