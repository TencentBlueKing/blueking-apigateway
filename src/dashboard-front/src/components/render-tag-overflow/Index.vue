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
  <div class="render-row-wrapper">
    <!-- 第一个标签：自适应宽度，超长省略 -->
    <BkTag
      v-if="visibleData.length > 0"
      :title="visibleData?.[0]"
      class="render-row-item flex-1 truncate"
      @click="emits('click')"
    >
      {{ visibleData?.[0] }}
    </BkTag>

    <!-- 超过1个显示 +n 标签+气泡 -->
    <BkPopover
      v-if="overflowData.length > 0"
      ext-cls="render-row-overflow-popover-main"
      :max-height="500"
      placement="left"
      theme="light"
      arrow
      v-bind="popoverProps"
    >
      <BkTag
        class="overflow-tag"
        @click="emits('click')"
      >
        +{{ overflowData.length }}
      </BkTag>
      <template #content>
        <slot name="popoverContent">
          <div class="flex flex-col gap-4px">
            <BkTag
              v-for="(item, index) of overflowData"
              :key="index"
              :title="item"
              class="render-row-item mb-4px max-w-400px"
            >
              {{ item }}
            </BkTag>
          </div>
        </slot>
      </template>
    </BkPopover>
  </div>
</template>

<script setup lang="ts">
interface IProps {
  data: string[]
  popoverProps?: Record<string, any>
}

const { data, popoverProps = {} } = defineProps<IProps>();
const emits = defineEmits<{ click: [void] }>();

// 只显示第一个
const visibleData = computed(() => data?.length > 1 ? data.slice(0, 1) : data);
// 溢出的全部收起
const overflowData = computed(() => data?.length > 1 ? data.slice(1) : []);
</script>

<style lang="scss" scoped>
.render-row-wrapper {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  max-width: 100%;
  box-sizing: border-box;

  .render-row-item {
    padding: 0 10px;
    flex-shrink: 0;
  }
}
</style>
