<template>
  <div
    ref="memberSelectorEditRef"
    class="gateways-edit-member-selector"
    :style="styles"
  >
    <template v-if="!isEditable">
      <div class="edit-wrapper">
        <div class="edit-content">
          <slot>
            <template v-if="membersText">
              <span class="member-item">
                <BkPopover>
                  <bk-user-display-name :user-id="membersText" />
                  <template #content>
                    <span><bk-user-display-name :user-id="membersText" /></span>
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
        <MemberSelector
          ref="memberSelectorRef"
          v-model="displayValue"
          class="edit-selector w-500px"
          :class="[{ [isErrorClass]: isShowError }]"
          :placeholder="placeholder"
          has-delete-icon
          @change="handleChange"
          @keydown="handleEnter"
        />
        <aside class="edit-member-actions">
          <BkPopConfirm
            v-if="!displayValue?.includes(userInfoStore.info.username)"
            width="288"
            :content="t('您已将自己从维护人员列表中移除，移除后您将失去查看和编辑网关的权限。请确认！')"
            trigger="click"
            ext-cls="confirm-custom-btn"
            @confirm="handleSubmit"
            @cancel="handleCancel"
          >
            <BkButton class="w-32px">
              <AgIcon
                name="check-1"
                class="color-#3A84FF"
                size="24"
              />
            </BkButton>
          </BkPopConfirm>
          <BkButton
            v-else
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
import MemberSelector from '@/components/member-selector/index.tsx';
import { useUserInfo } from '@/stores';

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

const { t } = useI18n();

const userInfoStore = useUserInfo();

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
  document.body.click();
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
  if (isRequired && !displayValue.value.length) {
    isShowError.value = true;
    errorTips.value = errorValue;
    return;
  }
  isEditable.value = true;
  nextTick(() => {
    memberSelectorRef.value?.tagInputRef?.focusInputTrigger();
  });
};

const handleEnter = (event: any) => {
  if (!isEditable.value) return;
  if (!displayValue.value?.includes(userInfoStore.info.username)) {
    isShowError.value = true;
    errorTips.value = t('您已将自己从维护人员列表中移除，移除后您将失去查看和编辑网关的权限。请确认！');
    return;
  }
  if (event.key === 'Enter' && event.keyCode === 13) {
    triggerChange();
  }
};

const triggerChange = () => {
  if (isRequired && !displayValue.value.length) {
    isShowError.value = true;
    errorTips.value = errorValue;
    return;
  }
  isEditable.value = false;
  if (JSON.stringify(displayValue.value) === JSON.stringify(content)) {
    return;
  }
  emit('on-change', { [field]: displayValue.value });
};

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
      width: 100%;
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
    color: #979BA5;
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

<style lang="scss">
.confirm-custom-btn {

  .bk-button.bk-button-primary {
    background-color: #E71818;
    border-color: #E71818;

    &:hover {
      background-color: #ff5656;
      border-color: #ff5656;
    }
  }
}
</style>
