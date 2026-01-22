/*
 * TencentBlueKing is pleased to support the open source community by making
 * 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
 * Copyright (C) 2026 Tencent. All rights reserved.
 * Licensed under the MIT License (the "License"); you may not use this file except
 * in compliance with the License. You may obtain a copy of the License at
 *
 *     http://opensource.org/licenses/MIT
 *
 * Unless required by applicable law or agreed to in writing, software distributed under
 * the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND,
 * either express or implied. See the License for the specific language governing permissions and
 * limitations under the License.
 *
 * We undertake not to change the open source license (MIT license) applicable
 * to the current version of the project delivered to anyone in the future.
 */

<template>
  <div
    :style="descriptionWrapperStyle"
    class="w-full flex flex-col relative description-wrapper"
  >
    <div
      ref="contentRef"
      class="description-content"
      :class="{
        'expanded': isExpanded,
        'has-max-height': dynamicMaxHeight > 0 && !isExpanded
      }"
    >
      <section
        v-bk-tooltips="{
          content: slots?.description,
          disabled: !(isShowExpand && !showExpandIcon),
          extCls: 'max-w-480px'
        }"
      >
        <slot name="description" />
      </section>
    </div>
    <BkButton
      v-if="displayExpand"
      theme="primary"
      text
      class="text-12px toggle-btn"
      @click="toggleExpand"
    >
      <i
        :class="[`apigateway-icon text-20px ${isExpanded ? 'icon-ag-arrows-up' : 'icon-ag-arrows-down'}`]"
      />
      <span>{{ i18n.global.t(isExpanded ? collapseText : expandText) }}</span>
    </BkButton>
  </div>
</template>

<script setup lang="ts">
import i18n from '@/locales';

interface IProps {
  maxLines?: number // 默认显示行数（仅未设置dynamicMaxHeight时生效）
  expandText?: string // 展开按钮文字
  collapseText?: string // 收起按钮文字
  dynamicMaxHeight?: number // 动态最大高度（优先级高于maxLines）
  showExpandIcon?: boolean // 显示展开/收缩按钮
  fontSize?: number | string // 字体大小，支持数字(px)或字符串(如'16px'/'1.2rem')
  lineHeight?: number | string // 字体行高，支持数字(px)或字符串(如'16px'/'1.2rem')
}

const {
  maxLines = 3,
  dynamicMaxHeight = 0,
  expandText = '展开',
  collapseText = '收起',
  showExpandIcon = true,
  fontSize = 14,
  lineHeight = 1.5,
} = defineProps<IProps>();

const slots = useSlots();

const contentRef = ref<HTMLElement | null>(null);
const isExpanded = ref(false);
const isShowExpand = ref(false);

// 处理字体大小格式，统一转为px值
const getFontSizeInPx = computed(() => {
  if (typeof fontSize === 'number') {
    return fontSize;
  }
  const num = parseFloat(fontSize);
  const unit = fontSize.replace(/\d+/g, '').trim();

  if (['rem', 'em'].includes(unit)) {
    return num * 16;
  }

  return num;
});

// 处理行高格式
const getLineHeightValue = computed(() => {
  if (typeof lineHeight === 'number') {
    return lineHeight;
  }

  const num = parseFloat(lineHeight);
  const unit = lineHeight.replace(/\d+/g, '').trim();

  if (['px'].includes(unit)) {
    return num / getFontSizeInPx.value;
  }

  return num;
});

const descriptionWrapperStyle = computed(() => {
  const styleList = [
    `--font-size: ${typeof fontSize === 'number' ? `${fontSize}px` : fontSize}`,
    `--line-height: ${lineHeight}`,
  ];
  if (Number(dynamicMaxHeight) > 0) {
    styleList.push(`--dynamic-max-height: ${dynamicMaxHeight}px`);
  }
  return styleList.join('; ');
});

const displayExpand = computed(() => isShowExpand.value && showExpandIcon);

const toggleExpand = () => {
  isExpanded.value = !isExpanded.value;
};

// 判断是否显示展开按钮
const checkOverflow = () => {
  if (!contentRef.value) return;

  let isOverflow = false;
  // 设置了dynamicMaxHeight, 仅超过该高度才显示按钮
  if (Number(dynamicMaxHeight) > 0) {
    const contentScrollHeight = contentRef.value.scrollHeight;
    isOverflow = contentScrollHeight > Number(dynamicMaxHeight);
  }
  // 未设置dynamicMaxHeight, 按maxLines行数判断
  else {
    // 计算maxLines对应的高度
    const fontSizeInPx = getFontSizeInPx.value;
    const lineHeightValue = getLineHeightValue.value;
    const maxLinesHeight = maxLines * fontSizeInPx * lineHeightValue;
    isOverflow = contentRef.value.scrollHeight > maxLinesHeight;
  }

  isShowExpand.value = isOverflow;
};

onMounted(() => {
  // 先强制渲染一次内容，再判断溢出
  setTimeout(checkOverflow, 0);
});

watchEffect(() => {
  setTimeout(checkOverflow, 0);
});
</script>

<style scoped lang="scss">
.description-wrapper {
  --dynamic-max-height: none;
  --font-size: 14px;
  --line-height: 1.5;
  --single-line-height: calc(var(--font-size) * var(--line-height));

  .description-content {
    display: -webkit-box;
    -webkit-box-orient: vertical;
    -webkit-line-clamp: v-bind(maxLines);
    line-height: var(--line-height);
    font-size: var(--font-size);
    overflow: hidden;
    transition: all 0.2s ease;
    max-height: fit-content;

    // 收起状态 + 设置了dynamicMaxHeight：限制最大高度（优先级高于行数）
    &.has-max-height {
      -webkit-line-clamp: unset !important;
      max-height: var(--dynamic-max-height);
    }

    // 展开状态：完全移除所有限制，高度自适应
    &.expanded {
      -webkit-line-clamp: unset !important;
      max-height: unset !important;
      overflow: visible !important;
    }
  }

  .toggle-btn {
    width: fit-content;
  }
}
</style>
