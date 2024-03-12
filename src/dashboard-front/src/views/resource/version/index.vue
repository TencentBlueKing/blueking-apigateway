<template>
  <div>
    <resource-version-top-bar />
    <edition v-if="resourceVersionStore.tabActive === 'edition'" />
    <sdk v-else />
  </div>
</template>

<script setup lang="ts">
import { onBeforeUnmount, watch } from 'vue';
import { useResourceVersion } from '@/store';
import resourceVersionTopBar from '@/components/resource-version-top-bar.vue';
import edition from './edition/index.vue';
import sdk from './sdk/index.vue';

const resourceVersionStore = useResourceVersion();

onBeforeUnmount(() => {
  resourceVersionStore.setTabActive('edition');
});

watch(
  () => resourceVersionStore.tabActive,
  (tab) => {
    if (tab === 'edition') {
      resourceVersionStore.setResourceFilter({});
    }
  },
);
</script>
