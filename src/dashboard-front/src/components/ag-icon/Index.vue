<template>
  <i
    v-if="!svg"
    :class="`icon-ag-${name}`"
    :style="{ fontSize: `${size}px` }"
    class="icon apigateway-icon"
  />
  <svg
    v-else
    :style="{ width: `${size}px`, height: `${size}px` }"
    class="icon svg-icon"
  >
    <use :xlink:href="`#icon-ag-${name}`" />
  </svg>
</template>

<script lang="ts" setup>
interface IProps {
  name: string
  size?: string
  svg?: boolean
}

const { name, size = '14', svg = false } = defineProps<IProps>();
</script>
