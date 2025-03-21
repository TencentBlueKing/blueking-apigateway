<template>
  <bk-collapse v-model="activeIndex">
    <bk-collapse-panel :name="name">
      <template #header>
        <div class="collapse-panel-header">
          <ag-icon
            :class="{ 'active-icon': isPanelActive }"
            name="down-shape"
          />
          <slot
            v-if="slots.header"
            name="header"
          />
          <span
            v-else
            class="panel-title"
          >
            {{ title }}
          </span>
        </div>
      </template>
      <template #content>
        <div class="collapse-content-wrapper">
          <slot name="default" />
        </div>
      </template>
    </bk-collapse-panel>
  </bk-collapse>
</template>

<script setup lang="ts">
import AgIcon from '@/components/ag-icon.vue';
import {
  ref,
  computed,
  watch,
} from 'vue';

interface Props {
  title?: string;
  name?: string;
}

interface Emits {
  (e: 'toggle', value: boolean): void;
}

interface Slots {
  default: any;
  header: any;
}

interface Exposes {
  show: () => void;
  hide: () => void;
}

const props = withDefaults(defineProps<Props>(), {
  title: '',
  name: 'default',
});

const emits = defineEmits<Emits>();

const slots = defineSlots<Slots>();

const activeIndex = ref([props.name]);

const isPanelActive = computed(() => !activeIndex.value.includes(props.name));

watch(isPanelActive, () => {
  emits('toggle', isPanelActive.value);
});

defineExpose<Exposes>({
  show: () => {
    activeIndex.value = [props.name];
  },
  hide: () => {
    activeIndex.value = [];
  },
});

</script>

<style lang="scss" scoped>

.collapse-panel-header {
  display: flex;
  align-items: center;
  cursor: pointer;
  position: relative;
  background-color: #eaebf0;
  height: 32px;
  padding-left: 12px;

  :deep(.iamcenter-down-shape) {
    color: #313238;
    transform: rotateZ(0deg);
    transition: all 0.5s;
  }

  .panel-title {
    margin-left: 5px;
    font-weight: 700;
    font-size: 14px;
    color: #313238;
  }

  .active-icon {
    transform: rotateZ(-90deg);
    transition: all 0.5s;
  }
}

:deep(.bk-collapse-content) {
  padding: 16px 24px;
  background-color: #fafbfd;
}

.collapse-content-wrapper {
}

</style>
