<template>
  <span
    class="plugin-icon"
    aria-hidden="true"
  >
    <AgIcon
      v-if="icon"
      :name="icon"
      size="48"
      svg
    />
    <span
      v-else
      class="plugin-initial"
    >
      {{ initial }}
    </span>
  </span>
</template>

<script lang="ts" setup>
import { PLUGIN_ICONS } from '@/constants';

interface IProps {
  code?: string
}

const { code = '' } = defineProps<IProps>();

const icon = computed(() => PLUGIN_ICONS.get(code));
const initial = computed(() => code.replace(/^bk-/, '').charAt(0).toUpperCase());
</script>

<style lang="scss" scoped>
.plugin-icon {
  width: 48px;
  height: 48px;
  flex: 0 0 48px;
}

.plugin-initial {
  display: grid;
  width: 100%;
  height: 100%;
  font-size: 24px;
  font-weight: 700;
  color: #3a84f6;
  background-color: #e2edfd;
  border-radius: 50%;
  place-items: center;
}
</style>
