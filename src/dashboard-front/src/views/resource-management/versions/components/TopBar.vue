<template>
  <div class="resource-version-top">
    <BkTab
      :active="resourceVersionStore.tabActive || 'edition'"
      type="unborder-card"
      @change="handleChange"
    >
      <BkTabPanel
        name="edition"
        :label="t('版本列表')"
      />
      <BkTabPanel
        v-if="featureFlagStore.flags.ALLOW_UPLOAD_SDK_TO_REPOSITORY"
        name="sdk"
        :label="t('SDK 列表')"
      />
    </BkTab>
  </div>
</template>

<script setup lang="ts">
import { useFeatureFlag, useResourceVersion } from '@/stores';

const { t } = useI18n();
const resourceVersionStore = useResourceVersion();
const featureFlagStore = useFeatureFlag();

const handleChange = (key: string) => {
  resourceVersionStore.setTabActive(key);
};
</script>

<style lang="scss">
.resource-version-top {
  display: flex;
  padding: 0 24px;
  margin-top: -10px;
  font-size: 12px;
  background-color: #fff;
  border-bottom: 1px solid #dcdee5;
  box-shadow: 0 3px 4px rgb(64 112 203 / 5.88%);
  justify-content: flex-start;
  align-items: center;

  .bk-tab--top .bk-tab-header-item {
    padding: 0 10px;
    font-size: 14px;
  }

  .bk-tab--unborder-card .bk-tab-header {
    border-bottom: none;
  }

  .bk-tab-content {
    padding: 0;
  }
}
</style>
