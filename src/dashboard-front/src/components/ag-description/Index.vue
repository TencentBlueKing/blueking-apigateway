<template>
  <div class="description-wrapper">
    <div
      ref="contentRef"
      class="description-content"
      :class="{ 'expanded': isExpanded }"
    >
      <slot name="description" />
    </div>

    <BkButton
      v-if="isShowExpand"
      theme="primary"
      text
      class="toggle-btn"
      @click="toggleExpand"
    >
      <i
        :class="[`apigateway-icon text-20px ${isExpanded ? 'icon-ag-arrows-up' : 'icon-ag-arrows-down'}`]"
      />
      <span>{{ isExpanded ? collapseText : expandText }}</span>
    </BkButton>
  </div>
</template>

<script setup lang="ts">
interface IProps {
  maxLines?: number // 默认显示行数
  expandText?: string // 展开按钮文字
  collapseText?: string // 收起按钮文字
}
const {
  maxLines = 3,
  expandText = '展开',
  collapseText = '收起',
} = defineProps<IProps>();

const contentRef = ref<HTMLElement | null>(null);
const isExpanded = ref(false);
const isShowExpand = ref(false);

const toggleExpand = () => {
  isExpanded.value = !isExpanded.value;
};
const checkOverflow = () => {
  if (!contentRef.value) return;
  const isOverflow = contentRef.value.scrollHeight > contentRef.value.clientHeight;
  isShowExpand.value = isOverflow;
};

onMounted(() => {
  checkOverflow();
});

watchEffect(() => {
  setTimeout(checkOverflow, 0);
});
</script>

<style scoped lang="scss">
.description-wrapper {
  position: relative;
  width: 100%;

  .description-content {
    display: -webkit-box;
    -webkit-box-orient: vertical;
    -webkit-line-clamp: v-bind(maxLines);
    overflow: hidden;
    line-height: 1.5;
    transition: max-height 0.2s ease;
  }

  .description-content.expanded {
    -webkit-line-clamp: unset;
  }

  .toggle-btn {
    margin-top: 4px;
    float: right;
    font-size: 14px;
  }
}

</style>
