/*
 * TencentBlueKing is pleased to support the open source community by making
 * 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
 * Copyright (C) Tencent. All rights reserved.
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
    ref="relatedAppCodesEditRef"
    class="gateways-edit-related-app-codes"
    :style="styles"
  >
    <template v-if="!isEditable">
      <div class="edit-wrapper">
        <div class="edit-content">
          <template v-if="displayValue.length">
            <span class="app-code-item">{{ displayValue.join(', ') }}</span>
          </template>
          <template v-else>
            --
          </template>
        </div>
        <div
          v-if="isEditMode"
          class="edit-action-box"
        >
          <AgIcon
            name="edit-small"
            size="26"
            class="edit-action"
            @click.self.stop="handleEdit"
          />
        </div>
      </div>
    </template>
    <div
      v-else
      class="edit-mode-content"
    >
      <main class="edit-app-codes-wrap">
        <BkTagInput
          ref="tagInputRef"
          v-model="displayValue"
          class="min-w-500px"
          :placeholder="placeholder"
          allow-create
          has-delete-icon
          :copyable="false"
          collapse-tags
          @keydown="handleEnter"
        />
        <aside class="edit-app-codes-actions">
          <BkButton
            class="w-32px"
            @click.stop="handleSubmit"
          >
            <AgIcon
              name="check-1"
              class="color-#3A84FF"
              size="24"
            />
          </BkButton>
          <BkButton
            class="w-32px"
            @click="handleCancel"
          >
            <AgIcon
              name="icon-close"
              size="24"
            />
          </BkButton>
        </aside>
      </main>
    </div>
  </div>
</template>

<script lang="ts" setup>
import AgIcon from '@/components/ag-icon/Index.vue';

interface IProps {
  field: string
  content?: string[]
  width?: string
  placeholder?: string
  mode?: 'edit' | 'detail'
}

interface IEmits {
  'on-change': [data: { [key: string]: string[] }]
  'on-submit': [data: { [key: string]: string[] }]
}

const {
  field,
  content = [],
  width = 'auto',
  placeholder = '',
  mode = 'edit',
} = defineProps<IProps>();

const emit = defineEmits<IEmits>();

const tagInputRef = ref();
const relatedAppCodesEditRef = ref();
const isEditable = ref(false);
const displayValue = ref<string[]>([]);

const styles = computed(() => {
  return { width: width };
});

const isEditMode = computed(() => {
  return mode === 'edit';
});

watch(
  () => content,
  (payload: string[]) => {
    displayValue.value = [...payload];
  },
  { immediate: true },
);

const handleEdit = () => {
  document.body.click();
  isEditable.value = true;
  nextTick(() => {
    tagInputRef.value?.focusInputTrigger();
  });
};

const handleSubmit = () => {
  if (!isEditable.value) return;
  triggerChange();
  emit('on-submit', { [field]: displayValue.value });
};

const handleCancel = () => {
  isEditable.value = false;
  displayValue.value = [...content];
};

const handleEnter = (event: KeyboardEvent) => {
  if (!isEditable.value) return;
  if (event.key !== 'Enter' || event.keyCode !== 13) return;
  triggerChange();
};

const triggerChange = () => {
  isEditable.value = false;
  if (JSON.stringify(displayValue.value) === JSON.stringify(content)) {
    return;
  }
  emit('on-change', { [field]: displayValue.value });
};

defineExpose({
  isEditable,
});

</script>

<style lang="scss" scoped>
.gateways-edit-related-app-codes {
  position: relative;

  .edit-wrapper {
    position: relative;
    display: flex;
    align-items: center;

    &:hover {

      .edit-action {
        display: block;
      }
    }

    .edit-content {
      max-width: calc(100% - 25px);
      min-width: 0;
      overflow: hidden;
      line-height: 32px;
      text-overflow: ellipsis;
      white-space: nowrap;
      flex: 0 0 auto;

      .app-code-item {
        display: block;
        max-width: 832px;
        overflow: hidden;
        font-size: 12px;
        line-height: 32px;
        text-overflow: ellipsis;
        white-space: nowrap;
      }
    }
  }

  .edit-mode-content {

    .edit-app-codes-wrap {
      display: flex;
      align-items: center;

      .edit-app-codes-actions {
        display: flex;
        margin-left: 4px;
        align-items: center;
        gap: 4px;
      }
    }
  }
}

.edit-action-box {
  display: flex;
  align-items: center;
  margin-right: auto;

  .icon-ag-edit-small {
    display: none;
    font-size: 26px;
    color: #979BA5;
    cursor: pointer;

    &:hover {
      color: #3a84ff;
    }
  }
}
</style>
