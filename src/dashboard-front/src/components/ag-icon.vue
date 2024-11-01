<template>
  <i v-if="!svg" :class="`icon-ag-${name}`" :style="{ fontSize: `${size}px` }" class="icon apigateway-icon"></i>
  <svg v-else :style="{ width: `${size}px`, height: `${size}px` }" class="icon svg-icon">
    <use :xlink:href="`#icon-ag-${name}`"></use>
  </svg>
</template>

<script lang="ts" setup>

defineProps({
  name: {
    type: String,
    require: true,
  },
  size: {
    type: String,
    default: '14',
  },
  svg: {
    type: Boolean,
    default: false,
  },
});

</script>
