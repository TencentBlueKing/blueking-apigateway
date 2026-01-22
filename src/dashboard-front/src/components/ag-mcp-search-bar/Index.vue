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
  <div class="w-full flex items-center gap-12px mcp-server-top-bar">
    <!-- 新建按钮模板 -->
    <slot name="mcpServerAdd" />
    <!-- tab选项模板 -->
    <slot name="mcpServerTab" />
    <!-- 搜索组件 -->
    <div class="flex-1">
      <BkSearchSelect
        v-model="searchValue"
        class="bg-#fff"
        :data="searchData"
        :placeholder="placeholder"
        :value-split-code="'+'"
        value-behavior="need-key"
        unique-select
      />
    </div>
    <!-- 发布时间 -->
    <div
      v-if="isShowPublishTime"
      class="mcp-publish-time"
    >
      <BkSelect
        v-model="publishTime"
        :input-search="false"
        :multiple="false"
        @toggle="handlePublishToggle"
        @change="handleSortChange"
      >
        <template #trigger="{ selected }">
          <BkButton class="flex items-center justify-between p-8px!">
            <div class="flex items-center justify-around">
              <AgIcon
                name="paixu"
                size="16"
                class="icon-ag-paixu mr-8px"
              />
              <div class="text-12px">
                {{ selected?.[0]?.label }}
              </div>
            </div>
            <AgIcon
              name="down-small"
              class="apigateway-select-icon color-#979ba5 ml-10px"
              :class="[{ 'is-open': isOpen }]"
            />
          </BkButton>
        </template>
        <BkOption
          v-for="item of publishTimeDropData"
          :id="item.value"
          :key="item.value"
          :name="item.label"
        />
      </BkSelect>
    </div>
    <!-- mcp视图切换 -->
    <slot name="mcpServerPreview" />
  </div>
</template>

<script lang="ts" setup>
import { t } from '@/locales';
import type { ISearchSelectData } from '@/types/common';

interface IProps {
  placeholder?: string
  isShowPublishTime?: boolean
  searchData?: ISearchSelectData[]
}

interface IEmits { 'sort-change': [sort: string] }

const searchValue = defineModel('searchValue', {
  required: true,
  type: Array,
});

const publishTime = defineModel('publishTime', {
  required: true,
  type: String,
  default: '-updated_time',
});

const {
  placeholder = '',
  isShowPublishTime = true,
  searchData = [],
} = defineProps<IProps>();

const emit = defineEmits<IEmits>();

const isOpen = ref(false);

// 发布时间选项
const publishTimeDropData = ref([
  {
    label: t('发布时间'),
    value: '-updated_time',
  },
  {
    label: t('字母 A-Z'),
    value: '-name',
  },
]);

const handlePublishToggle = (isVisible: boolean) => {
  isOpen.value = isVisible;
};

const handleSortChange = (value: string) => {
  publishTime.value = value;
  isOpen.value = false;
  emit('sort-change', value);
};
</script>

<style lang="scss" scoped>
.mcp-server-top-bar {
  line-height: 32px;
  box-sizing: border-box;

  :deep(.mcp-server-tab) {
    display: flex;
    align-items: center;
    height: 32px;
    padding: 4px;
    border-radius: 2px;
    background-color: #eaebf0;

    .mcp-server-tab-item {
      position: relative;
      min-width: 24px;
      height: 24px;
      padding: 0 12px;
      font-size: 12px;
      display: flex;
      align-items: center;
      justify-content: center;
      color: #4d4f56;
      cursor: pointer;

      &:not(:first-of-type) {
        min-width: 78px;

        &::before {
          position: absolute;
          top: 50%;
          left: 0;
          display: block;
          width: 1px;
          height: 12px;
          margin-top: -6px;
          background-color: #c4c6cc;
          content: '';
        }
      }

      &.is-active {
        border-radius: 2px;
        color: #3a84ff;
        background-color: #ffffff;
        box-shadow: 1px 1px 4px 0 #0000001a;

        &::before,
        & + .mcp-server-tab-item::before {
          display: none;
        }
      }
    }
  }

  :deep(.apigateway-select-icon) {
    font-size: 20px !important;
    transition: transform .3s;

    &.is-open {
      transform: rotate(180deg);
    }
  }
}
</style>
