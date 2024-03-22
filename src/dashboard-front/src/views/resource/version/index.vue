<template>
  <div>
    <resource-version-top-bar />
    <edition v-if="resourceVersionStore.tabActive === 'edition'" :version="curQueryVersion" />
    <sdk v-else @on-show-version="handleShowVersion" />
  </div>
</template>

<script setup lang="ts">
import { onBeforeUnmount, watch, ref } from 'vue';
import { useRoute } from 'vue-router';

import { useResourceVersion } from '@/store';
import resourceVersionTopBar from '@/components/resource-version-top-bar.vue';
import edition from './edition/index.vue';
import sdk from './sdk/index.vue';

const route = useRoute();

const resourceVersionStore = useResourceVersion();

const curQueryVersion = ref('');
const handleShowVersion = (version: string) => {
  resourceVersionStore.setTabActive('edition');
  curQueryVersion.value = version;
};

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
watch(
  () => route,
  (payload: any) => {
    curQueryVersion.value = payload.query.version || '';
  },
  { immediate: true, deep: true },
);

</script>
