/*
* TencentBlueKing is pleased to support the open source community by making
* 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
* Copyright (C) 2025 Tencent. All rights reserved.
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
  <div>
    <span v-show="!data.length">--</span>
    <div
      ref="rowRef"
      class="render-row-wrapper"
    >
      <p
        ref="textRef"
        class="render-row"
      >
        <BkTag
          v-for="(item, index) in data"
          :key="index"
          class="render-row-item"
          @click="emits('click')"
        >
          {{ item }}
        </BkTag>
        <BkTag
          class="overflow-tag"
          @click="emits('click')"
        >
          +{{ overflowData.length }}
        </BkTag>
      </p>
      <p class="visible-content">
        <BkTag
          v-for="(item, index) in visibleData"
          :key="index"
          class="render-row-item"
          @click="emits('click')"
        >
          {{ item }}
        </BkTag>
        <BkPopover
          v-if="overflowData.length > 0"
          ext-cls="render-row-overflow-popover-main"
          :max-height="500"
          placement="left"
          theme="light"
        >
          <span class="overflow-tag">
            <BkTag
              @click="emits('click')"
            >
              {{ overflowData?.[0] }}
            </BkTag>
            <BkTag
              v-if="overflowData.length > 1"
              class="ml-4px"
              @click="emits('click')"
            >
              +{{ overflowData.length - 1 }}
            </BkTag>
          </span>
          <template #content>
            <slot name="popoverContent">
              <div class="flex flex-column">
                <BkTag
                  v-for="(item, index) in overflowData"
                  :key="index"
                  v-bk-tooltips="item"
                  class="render-row-item mb-4px"
                >
                  {{ item }}
                </BkTag>
              </div>
            </slot>
          </template>
        </BkPopover>
      </p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { debounce } from 'lodash-es';

import { useResizeObserver } from '@vueuse/core';

interface Props {
  data: string[]
  // 容器右侧不能占用的预留空间
  right?: number
}

const { data, right = 0 } = defineProps<Props>();

const emits = defineEmits<{ click: [void] }>();

const findOverflowIndex = () => {
  overflowIndex.value = null;

  nextTick(() => {
    if (textRef.value) {
      const { left, width } = textRef.value.getBoundingClientRect();
      // 计算可用宽度，需要减去右侧预留的空间
      const max = left + width - right;
      const htmlArr: Element[] = Array.from(textRef.value.getElementsByClassName('render-row-item'));

      for (let i = 0; i < htmlArr.length; i++) {
        const item = htmlArr[i];
        const { left: itemLeft, width: itemWidth } = item.getBoundingClientRect();
        if (itemLeft + itemWidth > max) {
          overflowIndex.value = i;
          break;
        }
      }
      const colTag = textRef.value.getElementsByClassName('overflow-tag');
      if (colTag.length) {
        const { left: colTagLeft, width: colTagWidth } = colTag[0].getBoundingClientRect();
        if (colTagLeft + colTagWidth > max && overflowIndex.value) {
          overflowIndex.value = overflowIndex.value - 1;
        }
      }
    }
  });
};

const rowRef = ref<HTMLDivElement>();
useResizeObserver(rowRef, debounce(findOverflowIndex, 300));

const textRef = ref<HTMLParagraphElement>();
const overflowIndex = ref<number | null>(null);

const overflowData = computed(() => {
  if (overflowIndex.value === null) {
    return [];
  }
  return data.slice(overflowIndex.value);
});
const visibleData = computed(() => {
  if (overflowIndex.value === null) {
    return data;
  }
  return data.slice(0, overflowIndex.value);
});

watch(() => data, findOverflowIndex, { immediate: true });
</script>

<style lang="scss" scoped>
.render-row-wrapper {
  position: relative;
  display: inline-flex;
  max-width: 100%;
  align-items: center;

  .render-row {
    display: flex;
    overflow: hidden;
    opacity: 0%;
    gap: 4px;
  }

  .visible-content {
    position: absolute;
    display: flex;
    gap: 4px;
  }

}

.render-row-item {
  padding: 0 10px;
  max-width: max-content;
}
</style>

<style lang="scss">
.render-row-overflow-popover-main {
  overflow-y: auto;

  .bk-pop2-arrow {
    display: none;
  }
}
</style>
