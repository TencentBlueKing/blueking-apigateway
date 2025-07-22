<template>
  <div
    class="card-container"
    :class="{'has-hover-shadow': hoverShadow}"
  >
    <slot />
  </div>
</template>

<script setup lang="ts">
interface IProps { hoverShadow?: boolean }
const { hoverShadow = true } = defineProps<IProps>();
</script>

<style scoped lang="scss">
.card-container {
  background: #fff;;
  border-radius: 2px;
  box-shadow: 0 2px 4px 0 #1919290d;

  &.has-hover-shadow:hover {
    box-shadow: 0 2px 4px 0 #0000001a, 0 2px 4px 0 #1919290d;
  }
}
</style>
