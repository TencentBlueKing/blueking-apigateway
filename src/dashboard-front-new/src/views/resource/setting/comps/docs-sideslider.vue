<template>
  <div class="docs-sideslider-wrapper">
    <bk-sideslider
      v-model:isShow="isShow"
      quick-close
      width="960"
      ext-cls="stage-sideslider-cls">
      1
    </bk-sideslider>
  </div>
</template>
<script setup lang="ts">
import { toRefs } from 'vue';
const props = defineProps({
  isShow: { type: Boolean, default: false },
});
const { isShow } = toRefs(props);
</script>
