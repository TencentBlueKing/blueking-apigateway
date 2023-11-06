<template>
    <div class="resource-version-top">
        <bk-tab v-model:active="active" type="unborder-card" @change="handleChange">
            <bk-tab-panel name="edition" label="版本列表">
            </bk-tab-panel>
            <bk-tab-panel name="sdk" label="SDK列表">
            </bk-tab-panel>
        </bk-tab>
    </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useResourceVersion } from '@/store';

const resourceVersionStore = useResourceVersion();

const active = ref(resourceVersionStore.tabActive || 'edition')

const handleChange = (key: string) => {
    console.log('点击了', key)
    resourceVersionStore.setTabActive(key)
    console.log('点击了2', resourceVersionStore.tabActive)
}
</script>

<style lang="scss">
.resource-version-top {
    font-size: 12px;
    display: flex;
    justify-content: flex-start;
    align-items: center;

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