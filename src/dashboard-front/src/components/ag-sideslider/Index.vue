<template>
  <BkSideslider
    v-model:is-show="isShow"
    :title="title"
    :width="width"
    :quick-close="quickClose"
    :show-mask="showMask"
    :esc-close="escClose"
    :ext-cls="extCls"
    :direction="direction"
    :before-close="handleBeforeClose"
    @closed="emit('closed')"
  >
    <template
      v-if="!title"
      #header
    >
      <slot name="header" />
    </template>
    <template #default>
      <div class="drawer-container">
        <div class="drawer-content">
          <slot name="default" />
        </div>
        <div class="drawer-footer">
          <slot name="footer" />
        </div>
      </div>
    </template>
  </BkSideslider>
</template>

<script setup lang="ts">
import { useSidebar } from '@/hooks';

interface IProps {
  title?: string
  width?: number
  quickClose?: boolean
  showMask?: boolean
  escClose?: boolean
  direction?: 'left' | 'right'
  extCls?: string
  initData?: object | undefined
}

const isShow = defineModel<boolean>({
  required: true,
  default: false,
});

const {
  title = '标题',
  width = 960,
  quickClose = true,
  showMask = true,
  escClose = true,
  direction = 'right',
  extCls = '',
  initData = undefined,
} = defineProps<IProps>();

const emit = defineEmits<{
  closed: [void]
  compare: [data: (data: object) => void]
}>();

const { isSidebarClosed, initSidebarFormData } = useSidebar();

watch(
  () => initData,
  () => {
    initSidebarFormData(initData);
  },
  {
    immediate: true,
    deep: true,
  },
);

const handleBeforeClose = async () => {
  if (!initData) {
    return true;
  }

  return new Promise<boolean>((resolve) => {
    emit('compare', async (data: object) => {
      const result = await isSidebarClosed(JSON.stringify(data));
      resolve(result as boolean);
    });
  });
};

</script>

<style lang="scss" scoped>
:deep(.bk-modal-content) {
  height: calc(100vh - 52px) !important;
  scrollbar-gutter: auto !important;
}

:deep(.bk-modal-footer) {
  display: none;
}

.drawer-container {
  display: flex;
  flex-direction: column;
  max-height: calc(100vh - 52px);
  overflow: hidden;
}

.drawer-content {
  overflow-y: auto;
  scrollbar-gutter: stable;
}

.drawer-footer {
  height: 54px;
  display: flex;
  align-items: center;
  flex-shrink: 0;
}

</style>
