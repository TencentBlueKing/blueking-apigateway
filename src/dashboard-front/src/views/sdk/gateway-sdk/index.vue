<template>
  <div class="gateway-container">
    <sdk-detail :cur-type="type"></sdk-detail>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import sdkDetail from '../components/sdk-detail.vue';
const type = ref('apigateway');
</script>

<style lang="scss" scoped></style>
