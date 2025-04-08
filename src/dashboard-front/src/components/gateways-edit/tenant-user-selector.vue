<template>
  <div ref="memberSelectorEditRef" :style="styles" class="gateways-edit-member-selector">
    <template v-if="!isEditable">
      <div class="edit-wrapper">
        <div class="edit-content">
          <slot>
            <template v-if="membersText">
              <span class="member-item">
                <bk-popover>
                  <bk-user-display-name ref="bkUserDisplayNameRef" :user-id="membersText" />
                  <template #content>
                    <span><bk-user-display-name ref="bkUserDisplayNameRef" :user-id="membersText" /></span>
                  </template>
                </bk-popover>
              </span>
            </template>
            <template v-else>--</template>
          </slot>
        </div>
        <div v-if="isEditMode" class="edit-action-box">
          <i class="apigateway-icon icon-ag-edit-small edit-action" @click.self.stop="handleEdit" />
        </div>
      </div>
    </template>
    <div v-else class="edit-mode-content">
      <main class="edit-member-wrap">
        <bk-user-selector
          ref="memberSelectorRef"
          v-model="displayValue"
          :api-base-url="user.apiBaseUrl"
          :class="['edit-selector', { [isErrorClass]: isShowError }]"
          multiple
          :placeholder="placeholder"
          :tenant-id="user.user.tenant_id"
          required
          style="width: 500px"
          @change="handleChange"
        />
        <aside class="edit-member-actions">
          <bk-button style="width: 32px" @click.stop="handleSubmit">
            <i class="apigateway-icon icon-ag-check-1 f24" style="color: #3a84ff;"></i>
          </bk-button>
          <bk-button style="width: 32px" @click="handleCancel">
            <i class="apigateway-icon icon-ag-icon-close f24"></i>
          </bk-button>
        </aside>
      </main>
      <p v-if="isShowError" class="validate-error-tips">{{ errorTips }}</p>
    </div>
  </div>
</template>

<script lang="tsx" setup>
import {
  computed,
  nextTick,
  ref,
  watch,
} from 'vue';
import BkUserSelector from '@blueking/bk-user-selector';
import { useUser } from '@/store';

const user = useUser();

const props = defineProps({
  field: {
    type: String,
    required: true,
  },
  content: {
    type: Array,
    default: () => [],
  },
  width: {
    type: String,
    default: 'auto',
  },
  placeholder: {
    type: String,
    default: '请输入',
  },
  mode: {
    type: String,
    default: 'edit',
    validator(value: string) {
      return [
        'detail',
        'edit',
      ].includes(value);
    },
  },
  isRequired: {
    type: Boolean,
    default: true,
  },
  isErrorClass: {
    type: String,
    default: '',
  },
  errorValue: {
    type: String,
    default: '',
  },
});

const emit = defineEmits(['on-change']);

const memberSelectorRef = ref();
const memberSelectorEditRef = ref();
const isShowError = ref(false);
const isEditable = ref(false);
const errorTips = ref('');
const displayValue = ref([]);

const bkUserDisplayNameRef = ref();

const handleValidate = () => {
  isShowError.value = false;
  errorTips.value = '';
};

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
  displayValue.value = [...props.content];
};

const handleChange = () => {
  if (props.isRequired && !displayValue.value.length) {
    isShowError.value = true;
    errorTips.value = props.errorValue;
    return;
  }
  isEditable.value = true;
  nextTick(() => {
    memberSelectorRef.value?.tagInputRef?.focusInputTrigger();
  });
};

const hideEdit = (event: any) => {
  if (props.isRequired && !displayValue.value.length) {
    isShowError.value = true;
    errorTips.value = props.errorValue;
    return;
  }
  if (memberSelectorEditRef.value?.contains(event.target)) {
    return;
  }
  handleValidate();
  triggerChange();
};

const triggerChange = () => {
  if (props.isRequired && !displayValue.value.length) {
    isShowError.value = true;
    errorTips.value = props.errorValue;
    return;
  }
  isEditable.value = false;
  if (JSON.stringify(displayValue.value) === JSON.stringify(props.content)) {
    return;
  }
  emit('on-change', {
    [props.field]: displayValue.value,
  });
};

const styles = computed(() => {
  return {
    width: props.width,
  };
});

const isEditMode = computed(() => {
  return props.mode === 'edit';
});

const membersText = computed(() => {
  return displayValue.value.join(', ');
});

watch(
  () => props.content,
  (payload: any[]) => {
    displayValue.value = [...payload];
  },
  { immediate: true },
);

watch(
  () => props.errorValue,
  (payload: string) => {
    errorTips.value = payload;
  },
  { immediate: true },
);

// onMounted(() => {
//   document.body.addEventListener('click', hideEdit);
// });
//
// onBeforeMount(() => {
//   document.body.removeEventListener('click', hideEdit);
// });
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
      flex: 0 0 auto;
      max-width: calc(100% - 25px);
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
      line-height: 32px;

      .member-item {
        line-height: 32px;
        font-size: 12px;
        width: calc(100% - 25px);
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;

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
        margin-left: 4px;
        display: flex;
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
    font-size: 26px;
    color: #979ba5;
    cursor: pointer;
    display: none;

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

