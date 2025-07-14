<template>
  <BkButton
    v-bind="$attrs"
  >
    <AgIcon
      v-if="icon"
      :name="icon"
      :size="size"
      :svg="svg"
      class="mr-8px"
    />
    <span>
      <slot />
    </span>
  </BkButton>
</template>

<script setup lang="ts">
interface IProps {
  icon?: string
  size?: string
  svg?: boolean
}

const { icon = '', size = '14', svg = false } = defineProps<IProps>();
</script>
