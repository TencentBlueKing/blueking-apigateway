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
  <div class="render-row-wrapper">
    <!-- 第一个标签：自适应宽度，超长省略 -->
    <template v-if="visibleData?.length > 0">
      <AgUserDisplayName
        :is-enable-display-name="isEnableDisplayName"
        :user-id="visibleData[0]"
        class="flex-1 flex-shrink-0 truncate"
      />
    </template>

    <!-- 超过1个显示 +n 标签+气泡 -->
    <BkPopover
      v-if="overflowData.length > 0"
      :max-height="500"
      :popover-delay="0"
      placement="left"
      theme="light"
      arrow
      v-bind="popoverProps"
    >
      <BkTag class="overflow-tag">
        +{{ overflowData.length }}
      </BkTag>
      <template #content>
        <div class="flex flex-col gap-4px">
          <AgUserDisplayName
            :is-enable-display-name="isEnableDisplayName"
            :class="`flex flex-col flex-shrink-0 gap-4px max-w-800px max-h-${popoverMaxHeight}px overflow-y-auto`"
          >
            <template #customDisplayName>
              <BkTag
                v-for="(item, index) of overflowData"
                :key="index"
              >
                <bk-user-display-name
                  v-if="isEnableDisplayName"
                  :user-id="item"
                />
                <span v-else>
                  {{ item }}
                </span>
              </BkTag>
            </template>
          </AgUserDisplayName>
        </div>
      </template>
    </BkPopover>
  </div>
</template>

<script setup lang="ts">
import { useFeatureFlag } from '@/stores';
import AgUserDisplayName from '@/components/ag-user-display-name/Index.vue';

interface IProps {
  data: string[]
  popoverProps?: Record<string, any>
  isMember?: boolean
  popoverMaxHeight?: number
}

const {
  data,
  popoverProps = {},
  isMember = false,
  popoverMaxHeight = 300,
} = defineProps<IProps>();

const featureFlagStore = useFeatureFlag();

// 只显示第一个
const visibleData = computed(() => data?.length > 1 ? data.slice(0, 1) : data);
// 溢出的数据
const overflowData = computed(() => data?.length > 1 ? data.slice(1) : []);
// 控制是否展示用户名称组件
const isEnableDisplayName = computed(() => featureFlagStore.isEnableDisplayName && isMember);
</script>

<style lang="scss" scoped>
.render-row-wrapper {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  max-width: 100%;
  box-sizing: border-box;
}
</style>
