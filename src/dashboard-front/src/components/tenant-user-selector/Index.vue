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
    ref="memberSelectorEditRef"
    :style="styles"
    class="gateways-edit-member-selector"
  >
    <template v-if="!isEditable">
      <div class="edit-wrapper">
        <div class="edit-content">
          <slot>
            <template v-if="membersText">
              <span class="member-item">
                <BkPopover>
                  <div class="overflow-hidden text-ellipsis whitespace-nowrap">
                    <bk-user-display-name
                      v-if="featureFlagStore.isEnableDisplayName"
                      :user-id="membersText"
                    />
                    <template v-else>{{ membersText }}</template>
                  </div>
                  <template #content>
                    <div>
                      <bk-user-display-name
                        v-if="featureFlagStore.isEnableDisplayName"
                        :user-id="membersText"
                      />
                      <template v-else>{{ membersText }}</template>
                    </div>
                  </template>
                </BkPopover>
              </span>
            </template>
            <template v-else>
              --
            </template>
          </slot>
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
      <main class="edit-member-wrap">
        <BkUserSelector
          ref="memberSelectorRef"
          v-model="displayValue"
          :api-base-url="envStore.tenantUserDisplayAPI"
          class="edit-selector"
          :class="[{ [isErrorClass]: isShowError }]"
          multiple
          :placeholder="placeholder"
          :tenant-id="userStore.info.tenant_id || ''"
          required
          @change="handleChange"
        />
        <aside class="edit-member-actions">
          <BkButton
            class="w-32px"
            @click.stop="handleSubmit"
          >
            <AgIcon
              name="check-1"
              class="color-#3a84ff"
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
      <p
        v-if="isShowError"
        class="validate-error-tips"
      >
        {{ errorTips }}
      </p>
    </div>
  </div>
</template>

<script lang="tsx" setup>
import BkUserSelector from '@blueking/bk-user-selector';
import {
  useEnv,
  useFeatureFlag,
  useUserInfo,
} from '@/stores';

interface IProps {
  field: string
  content?: string[]
  width?: string
  placeholder?: string
  mode?: 'edit' | 'detail'
  isRequired?: boolean
  isErrorClass?: string
  errorValue?: string
}

const {
  field,
  content = [],
  width = 'auto',
  placeholder = '请输入',
  mode = 'edit',
  isRequired = true,
  isErrorClass = '',
  errorValue = '',
} = defineProps<IProps>();

const emit = defineEmits<{ 'on-change': [data: { [key: string]: string[] }] }>();

const envStore = useEnv();
const userStore = useUserInfo();
const featureFlagStore = useFeatureFlag();

const memberSelectorRef = ref();
const memberSelectorEditRef = ref();
const isShowError = ref(false);
const isEditable = ref(false);
const errorTips = ref('');
const displayValue = ref<string[]>([]);

const styles = computed(() => {
  return { width: width };
});

const isEditMode = computed(() => {
  return mode === 'edit';
});

const membersText = computed(() => {
  return displayValue.value.join(', ');
});

watch(
  () => content,
  (payload: any[]) => {
    displayValue.value = [...payload];
  },
  { immediate: true },
);

watch(
  () => errorValue,
  (payload: string) => {
    errorTips.value = payload;
  },
  { immediate: true },
);

const handleEdit = () => {
  isEditable.value = true;
  nextTick(() => {
    memberSelectorRef.value?.tagInputRef?.focusInputTrigger();
  });
};

const handleSubmit = () => {
  if (!isEditable.value) return;
  triggerChange();
};

const handleCancel = () => {
  isEditable.value = false;
  displayValue.value = [...content];
};

const handleChange = () => {
  isShowError.value = !displayValue.value.length;
  if (isRequired && !displayValue.value.length) {
    errorTips.value = errorValue;
    return;
  }
  isEditable.value = true;
  nextTick(() => {
    memberSelectorRef.value?.tagInputRef?.focusInputTrigger();
  });
  emit('on-change', { [field]: displayValue.value });
};

const triggerChange = () => {
  isShowError.value = !displayValue.value.length;
  if (isRequired && !displayValue.value.length) {
    errorTips.value = errorValue;
    return;
  }
  isEditable.value = false;
  if (JSON.stringify(displayValue.value) === JSON.stringify(content)) {
    return;
  }
  emit('on-change', { [field]: displayValue.value });
};

defineExpose({ isEditable });

</script>

<style lang="scss" scoped>
.gateways-edit-member-selector {
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
      overflow: hidden;
      line-height: 32px;
      text-overflow: ellipsis;
      white-space: nowrap;
      flex: 0 0 auto;

      .member-item {
        width: calc(100% - 25px);
        overflow: hidden;
        font-size: 12px;
        line-height: 32px;
        text-overflow: ellipsis;
        white-space: nowrap;

        i {
          font-size: 18px;
          color: #979ba5;
          vertical-align: middle;
          cursor: pointer;

          &.disabled {
            color: #c4c6cc;
            cursor: not-allowed;
          }
        }
      }
    }

    .edit-selector {
      width: 500px;
    }
  }

  .edit-mode-content {

    .edit-member-wrap {
      display: flex;
      align-items: center;

      .edit-member-actions {
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
    color: #979ba5;
    cursor: pointer;

    &:hover {
      color: #3a84ff;
    }
  }
}

:deep(.maintainers-error-tip) {

  .bk-tag-input-trigger {
    border-color: red;
  }
}

.validate-error-tips {
  font-size: 12px;
  color: #ff4d4d;
}
</style>
