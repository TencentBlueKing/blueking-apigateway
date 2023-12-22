<template>
  <div class="gateways-edit-member-selector" :style="styles">
    <template v-if="!isEditable">
      <div class="edit-wrapper">
        <div class="edit-content">
          <slot>
            <template v-if="displayValue.length">
              <span v-for="(item, index) in displayValue" :key="index" class="member-item">
                {{ displayValue.length > 1 && index !== displayValue.length - 1 ? `${item}，` : item }}
              </span>
            </template>
            <template v-else>--</template>
          </slot>
        </div>
        <div class="edit-action-box" v-if="isEditMode">
          <i class="apigateway-icon icon-ag-edit-small edit-action" @click.self.stop="handleEdit" />
        </div>
      </div>
    </template>
    <div v-else class="edit-mode-content">
      <MemberSelector
        ref="memberSelectorRef" v-model="displayValue"
        :class="['edit-selector', { [isErrorClass]: isShowError }]"
        :placeholder="placeholder"
        @blur="handleBlur"
        @keydown="handleEnter" />
      <p class="validate-error-tips" v-if="isShowError">{{ errorTips }}</p>
    </div>
  </div>
</template>

<script lang="ts" setup>
import { computed, ref, nextTick, watch, onBeforeMount, onMounted } from 'vue';
import MemberSelector from '../member-select';
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
      return ['detail', 'edit'].includes(value);
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
const isShowError = ref(false);
const isEditable = ref(false);
const errorTips = ref('');
const displayValue = ref([]) as any;

const handleValidate = () => {
  isShowError.value = false;
  errorTips.value = '';
};

const handleEdit = () => {
  document.body.click();
  isEditable.value = true;
  nextTick(() => {
    console.log(memberSelectorRef.value?.tagInputRef);
    memberSelectorRef.value?.tagInputRef?.tagInputRef.focus();
  });
};

const handleBlur = () => {
  if (!isEditable.value) return;
  triggerChange();
};

const handleEnter = (event: any) => {
  if (!isEditable.value) return;
  if (event.key === 'Enter' && event.keyCode === 13) {
    triggerChange();
  }
};

const hideEdit = (event: any) => {
  if (props.isRequired && !displayValue.value.length) {
    isShowError.value = true;
    return;
  }
  if (event.path && event.path.length > 0) {
    for (const i of event.path) {
      const target = event.path[i];
      console.log(target.className);
      if (target.className === 'gateways-edit-member-selector') {
        return;
      }
    }
  }
  // isEditable.value = false;
  handleValidate();
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

watch(
  () => props.content,
  (payload: any[]) => {
    displayValue.value = [...payload];
  },
);

watch(
  () => props.errorValue,
  (payload: string) => {
    errorTips.value = payload;
    console.log(errorTips.value, 444);
  },
  { immediate: true },
);

onMounted(() => {
  document.body.addEventListener('click', hideEdit);
});

onBeforeMount(() => {
  document.body.removeEventListener('click', hideEdit);
});
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
        display: inline-block;
        // padding: 0 10px;
        // margin: 2px 0 2px 6px;
        line-height: 32px;
        // border-radius: 2px;
        // background: #f0f1f5;
        font-size: 12px;

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
}

.edit-action-box {
  display: flex;
  align-items: center;
  margin-right: auto;

  .icon-ag-edit-small {
    font-size: 26px;
    color: #979BA5;
    cursor: pointer;
    display: none;

    &:hover {
      color: #1768ef;
    }
  }
}

.maintainers-error-tip {
  border: 1px solid red;
}

.validate-error-tips {
  font-size: 12px;
  color: #ff4d4d;
}
</style>

