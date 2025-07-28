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
  max-height: calc(100vh - 54px);
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
