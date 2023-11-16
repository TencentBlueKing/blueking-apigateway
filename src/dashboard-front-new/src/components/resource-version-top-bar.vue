<template>
  <div class="resource-version-top">
    <bk-tab :active="resourceVersionStore.tabActive || 'edition'" type="unborder-card" @change="handleChange">
      <bk-tab-panel name="edition" label="版本列表">
      </bk-tab-panel>
      <bk-tab-panel name="sdk" label="SDK列表">
      </bk-tab-panel>
    </bk-tab>
  </div>
</template>

<script setup lang="ts">
import { useResourceVersion } from '@/store';

const resourceVersionStore = useResourceVersion();

const handleChange = (key: string) => {
  resourceVersionStore.setTabActive(key);
};
</script>

<style lang="scss">
.resource-version-top {
    font-size: 12px;
    display: flex;
    justify-content: flex-start;
    align-items: center;
    background-color: #ffffff;
    padding: 0 24px;
    margin-top: -10px;
    border-bottom: 1px solid #dcdee5;
    box-shadow: 0 3px 4px rgba(64, 112, 203, 0.05882);

    .bk-tab--top .bk-tab-header-item {
        padding: 0 10px;
    }

    .bk-tab--unborder-card .bk-tab-header {
        border-bottom: none;
    }

    .bk-tab-content {
        padding: 0px;
    }
}
</style>
