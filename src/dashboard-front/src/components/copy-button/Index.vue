<template>
  <AgIcon
    class="copy-icon"
    name="copy-info"
    size="16"
    v-bind="$attrs"
    @click="handleClick"
  />
</template>

<script setup lang="ts">
import { copy } from '@/utils';

interface IProps {
  // 复制的内容，不传入就使用自定义的事件处理器，需要在外部监听 click 事件
  source?: string
}

const { source = '' } = defineProps<IProps>();

const handleClick = () => {
  if (source) {
    copy(source);
  }
};
</script>

<style scoped lang="scss">
.copy-icon {
  color: #3A84FF;
  cursor: pointer;
}
</style>
