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
  <BkCollapse v-model="activeIndex">
    <BkCollapsePanel :name="name">
      <template #header>
        <div class="collapse-panel-header">
          <AgIcon
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
    </BkCollapsePanel>
  </BkCollapse>
</template>

<script setup lang="ts">
import AgIcon from '@/components/ag-icon/Index.vue';

interface IProps {
  title?: string
  name?: string
}

interface Slots {
  default: any
  header: any
}

interface Emits { (e: 'toggle', value: boolean): void }

const {
  title = '',
  name = 'default',
} = defineProps<IProps>();

const emits = defineEmits<Emits>();

const slots = defineSlots<Slots>();

interface Exposes {
  show: () => void
  hide: () => void
}

const activeIndex = ref([name]);

const isPanelActive = computed(() => !activeIndex.value.includes(name));

watch(isPanelActive, () => {
  emits('toggle', isPanelActive.value);
});

defineExpose<Exposes>({
  show: () => {
    activeIndex.value = [name];
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
