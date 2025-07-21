<template>
  <div>
    <TopBar />
    <VersionList
      v-if="resourceVersionStore.tabActive === 'edition'"
      :version="curQueryVersion"
    />
    <SDKList
      v-else
      @on-show-version="handleShowVersion"
    />
  </div>
</template>

<script setup lang="ts">
import { useResourceVersion } from '@/stores';
import TopBar from './components/TopBar.vue';
import VersionList from './components/VersionList.vue';
import SDKList from './components/SDKList.vue';

const route = useRoute();
const resourceVersionStore = useResourceVersion();

const curQueryVersion = ref('');

watch(
  () => route,
  (payload: any) => {
    curQueryVersion.value = payload.query.version || '';
  },
  {
    immediate: true,
    deep: true,
  },
);

watch(
  () => resourceVersionStore.tabActive,
  (tab) => {
    if (tab === 'edition') {
      resourceVersionStore.setResourceFilter({});
    }
  },
);

const handleShowVersion = (version: string) => {
  resourceVersionStore.setTabActive('edition');
  curQueryVersion.value = version;
};

onBeforeUnmount(() => {
  resourceVersionStore.setTabActive('edition');
});

</script>
