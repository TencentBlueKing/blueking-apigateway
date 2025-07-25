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
  <div
    class="gateways-edit-textarea"
    :style="styles"
  >
    <template v-if="!isEditable">
      <div class="edit-wrapper">
        <div
          class="edit-content"
          :title="newVal"
        >
          <slot :value="newVal">
            {{ newVal }}
            <template v-if="!newVal">
              --
            </template>
          </slot>
        </div>
        <div
          v-if="isEditMode"
          class="edit-action-box"
        >
          <AgIcon
            class="edit-action"
            name="edit-small"
            size="26"
            @click.self.stop="handleEdit"
          />
        </div>
      </div>
    </template>
    <div
      v-else
      class="edit-mode-content"
    >
      <BkInput
        ref="textareaRef"
        v-model="newVal"
        type="textarea"
        class="edit-input"
        :placeholder="placeholder"
        :maxlength="maxLength"
        :rows="3"
        @input="handleInput"
        @blur="handleBlur"
        @enter="handleEnter"
      />
      <p
        v-if="isShowError"
        class="validate-error-tips"
      >
        {{ errorTips }}
      </p>
    </div>
  </div>
</template>

<script lang="ts" setup>
interface IProps {
  field: string
  content?: string
  width?: string
  placeholder?: string
  maxLength?: number
  mode?: 'edit' | 'detail'
}

const {
  field,
  content = '',
  width = 'auto',
  placeholder = '请输入',
  maxLength = 500,
  mode = 'edit',
} = defineProps<IProps>();

const emit = defineEmits<{ 'on-change': [data: { [key: string]: string }] }>();

const textareaRef = ref();
const isShowError = ref(false);
const isEditable = ref(false);
const errorTips = ref('');
const newVal = ref(content);

const styles = computed(() => {
  return { width: width };
});

const isEditMode = computed(() => {
  return mode === 'edit';
});

watch(
  () => content,
  () => {
    newVal.value = content;
  },
);

const handleEdit = () => {
  isEditable.value = true;
  nextTick(() => {
    textareaRef.value?.focus();
  });
};

const handleInput = () => {
  isShowError.value = false;
  errorTips.value = '';
};

const handleBlur = () => {
  if (!isEditable.value) return;
  isEditable.value = false;
  triggerChange();
};

const handleEnter = (value: string, event: any) => {
  if (!isEditable.value) return;
  if (event.key === 'Enter' && event.keyCode === 13) {
    newVal.value = newVal.value.trim();
    isEditable.value = false;
    triggerChange();
  }
};

const triggerChange = () => {
  isEditable.value = false;
  if (newVal.value === content) {
    return;
  }
  emit('on-change', { [field]: newVal.value });
};
</script>

<style lang="scss" scoped>
@keyframes textarea-edit-loading {

  to {
    transform: rotateZ(360deg);
  }
}

.gateways-edit-textarea {
  position: relative;

  .edit-wrapper {
    position: relative;
    display: flex;
    align-items: center;

    &:hover {

      .icon-ag-edit-small {
        display: block;
      }
    }
  }

  .edit-content {
    height: 26px;
    max-width: calc(100% - 25px);
    overflow: hidden;
    line-height: 26px;
    text-overflow: ellipsis;
    white-space: nowrap;
    flex: 0 0 auto;
  }

  .edit-action-box {
    display: flex;
    align-items: center;
    margin-right: auto;

    .edit-action {
      display: none;
      color: #979BA5;
      cursor: pointer;

      &:hover {
        color: #1768ef;
      }
    }
  }

  .edit-mode-content {
    // padding: 20px 0;

    .edit-input {
      width: 100%;
    }
  }

  .validate-error-tips {
    font-size: 12px;
    color: #ff4d4d;
  }
}
</style>
