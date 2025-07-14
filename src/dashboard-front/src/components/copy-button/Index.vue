<template>
  <AgIcon
    class="copy-icon"
    name="copy-info"
    size="16"
    @click.self.stop="handleClick"
  />
</template>

<script setup lang="ts">
import { copy } from '@/utils';

interface IProps { source: string }

const { source } = defineProps<IProps>();

const emit = defineEmits<{ click: [void] }>();

const handleClick = () => {
  copy(source);
  emit('click');
};
</script>

<style scoped lang="scss">
.copy-icon {
  color: #3A84FF;
  cursor: pointer;
}
</style>
