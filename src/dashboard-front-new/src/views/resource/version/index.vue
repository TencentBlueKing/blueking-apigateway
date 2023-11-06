<template>
  <div>
    <edition v-if="resourceVersionStore.tabActive === 'edition'" />
    <sdk v-else />
  </div>
</template>

<script setup lang="ts">
import { useResourceVersion } from '@/store';
import edition from './edition/index.vue';
import sdk from './sdk/index.vue';

const resourceVersionStore = useResourceVersion();
</script>
